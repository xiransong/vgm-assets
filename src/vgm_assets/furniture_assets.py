from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .catalog import write_catalog_manifest
from .protocol import load_json
from .sampling import write_category_index

DEFAULT_PRODUCER = {
    "repo": "vgm-assets",
    "version": "0.1.0-dev",
    "commit": "working_tree",
}


def _timestamp(value: str | None = None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_bundle_manifest(path: Path) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise TypeError(f"Furniture bundle manifest at {path} must be a JSON object")
    return payload


def build_furniture_asset_record_from_bundle(bundle_manifest_path: Path) -> dict:
    bundle_manifest = _load_bundle_manifest(bundle_manifest_path)

    required = [
        "selection_id",
        "asset_id",
        "category",
        "source",
        "sample_weight",
        "dimensions",
        "placement",
        "walkability",
        "semantics",
        "support",
        "files",
        "normalized_rel_dir",
        "config_id",
    ]
    for key in required:
        if key not in bundle_manifest:
            raise ValueError(f"Bundle manifest at {bundle_manifest_path} is missing '{key}'")

    record = {
        "asset_id": bundle_manifest["asset_id"],
        "category": bundle_manifest["category"],
        "source": bundle_manifest["source"],
        "sample_weight": bundle_manifest["sample_weight"],
        "dimensions": bundle_manifest["dimensions"],
        "placement": bundle_manifest["placement"],
        "walkability": bundle_manifest["walkability"],
        "semantics": bundle_manifest["semantics"],
        "support": bundle_manifest["support"],
        "provenance": {
            "protocol_version": "v0",
            "producer": DEFAULT_PRODUCER,
            "config_id": bundle_manifest["config_id"],
            "upstream_ids": [bundle_manifest["selection_id"], bundle_manifest["asset_id"]],
        },
    }

    optional_pairs = {
        "footprint": bundle_manifest.get("footprint"),
        "files": bundle_manifest.get("files"),
    }
    for key, value in optional_pairs.items():
        if value is not None:
            record[key] = value

    return record


def write_furniture_asset_catalog(
    *,
    bundle_manifest_paths: list[Path],
    output_path: Path,
) -> list[dict]:
    records = [
        build_furniture_asset_record_from_bundle(path) for path in bundle_manifest_paths
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return records


def refresh_furniture_asset_catalog(
    *,
    catalog_id: str,
    bundle_manifest_paths: list[Path],
    catalog_output: Path,
    category_index_output: Path,
    manifest_output: Path,
    created_at: str | None = None,
    producer: dict | None = None,
) -> dict:
    records = write_furniture_asset_catalog(
        bundle_manifest_paths=bundle_manifest_paths,
        output_path=catalog_output,
    )
    category_index = write_category_index(catalog_output, category_index_output)
    manifest = write_catalog_manifest(
        catalog_path=catalog_output,
        output_path=manifest_output,
        catalog_id=catalog_id,
        created_at=created_at,
        producer=producer,
    )
    return {
        "catalog_id": catalog_id,
        "asset_count": len(records),
        "catalog_output": str(catalog_output.resolve()),
        "category_index_output": str(category_index_output.resolve()),
        "category_count": category_index["category_count"],
        "manifest_output": str(manifest_output.resolve()),
        "manifest_created_at": manifest["created_at"],
    }
