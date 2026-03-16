from __future__ import annotations

import random
from pathlib import Path

from .catalog import load_asset_specs


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
        "catalog_path": str(catalog_path.resolve()),
        "category_count": len(categories),
        "categories": categories,
    }


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
        "catalog_path": str(catalog_path.resolve()),
        "category": category,
        "sampling_policy": "uniform",
        "candidate_count": len(candidates),
        "seed": seed,
        "sampled_index": index,
        "asset_id": sampled["asset_id"],
        "asset": sampled,
    }
