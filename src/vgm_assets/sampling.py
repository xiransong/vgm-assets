from __future__ import annotations

import json
import random
from pathlib import Path

from .catalog import load_asset_specs
from .paths import repo_relative_or_absolute


def assets_by_category(catalog_path: Path) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for asset in load_asset_specs(catalog_path):
        category = asset["category"]
        grouped.setdefault(category, []).append(asset)
    return grouped


def category_summary(catalog_path: Path) -> dict:
    grouped = assets_by_category(catalog_path)
    categories = []
    for category in sorted(grouped):
        assets = grouped[category]
        categories.append(
            {
                "category": category,
                "asset_count": len(assets),
                "asset_ids": [asset["asset_id"] for asset in assets],
                "sampling_policy": "uniform",
            }
        )
    return {
        "catalog_path": repo_relative_or_absolute(catalog_path),
        "category_count": len(categories),
        "categories": categories,
    }


def build_category_index(catalog_path: Path) -> dict:
    grouped = assets_by_category(catalog_path)
    categories = {}
    for category in sorted(grouped):
        assets = grouped[category]
        categories[category] = {
            "sampling_policy": "uniform",
            "asset_count": len(assets),
            "asset_ids": [asset["asset_id"] for asset in assets],
        }
    return {
        "catalog_path": repo_relative_or_absolute(catalog_path),
        "category_count": len(categories),
        "categories": categories,
    }


def write_category_index(catalog_path: Path, output_path: Path) -> dict:
    index = build_category_index(catalog_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index


def sample_uniform_asset(
    catalog_path: Path,
    category: str,
    seed: int | None = None,
) -> dict:
    grouped = assets_by_category(catalog_path)
    candidates = grouped.get(category)
    if not candidates:
        raise ValueError(f"No assets found for category '{category}' in {catalog_path}")

    rng = random.Random(seed)
    index = rng.randrange(len(candidates))
    sampled = candidates[index]
    return {
        "catalog_path": repo_relative_or_absolute(catalog_path),
        "category": category,
        "sampling_policy": "uniform",
        "candidate_count": len(candidates),
        "seed": seed,
        "sampled_index": index,
        "asset_id": sampled["asset_id"],
        "asset": sampled,
    }
