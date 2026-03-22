from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema.validators import validator_for

from .catalog import _file_ref_for
from .protocol import load_json

DEFAULT_PRODUCER = {
    "repo": "vgm-assets",
    "version": "0.1.0-dev",
    "commit": "working_tree",
}
WALL_FIXTURE_CATALOG_SCHEMA = (
    Path("schemas") / "local" / "wall_fixture_catalog_v0.schema.json"
)


def _timestamp(value: str | None = None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root()).as_posix()
    except ValueError:
        return str(resolved)


def wall_fixture_catalog_schema_path() -> Path:
    return repo_root() / WALL_FIXTURE_CATALOG_SCHEMA


def load_wall_fixture_catalog(catalog_path: Path) -> list[dict]:
    payload = load_json(catalog_path)
    if not isinstance(payload, list):
        raise TypeError(f"Wall-fixture catalog at {catalog_path} must be a JSON array")
    normalized: list[dict] = []
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise TypeError(
                f"Wall-fixture catalog at {catalog_path} contains a non-object entry at index {index}"
            )
        normalized.append(record)
    return normalized


def validate_wall_fixture_catalog_data(payload: object) -> list[dict]:
    schema = load_json(wall_fixture_catalog_schema_path())
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, list):
        raise TypeError("Wall-fixture catalog payload must be a list after validation")
    return payload


def validate_wall_fixture_catalog(catalog_path: Path) -> list[dict]:
    return validate_wall_fixture_catalog_data(load_wall_fixture_catalog(catalog_path))


def _source_metadata_path(bundle_manifest_path: Path) -> Path:
    return bundle_manifest_path.with_name("source_metadata.json")


def build_wall_fixture_record_from_bundle(
    bundle_manifest_path: Path,
    *,
    sample_weight: float = 1.0,
    config_id: str = "wall_fixtures_v0_bundle_import_v1",
) -> dict:
    bundle_manifest = load_json(bundle_manifest_path)
    if not isinstance(bundle_manifest, dict):
        raise TypeError(f"Bundle manifest at {bundle_manifest_path} must be a JSON object")

    source_metadata = {}
    source_metadata_path = _source_metadata_path(bundle_manifest_path)
    if source_metadata_path.exists():
        loaded = load_json(source_metadata_path)
        if isinstance(loaded, dict):
            source_metadata = loaded

    required = [
        "selection_id",
        "fixture_id",
        "category",
        "dimensions",
        "mount",
        "files",
    ]
    for key in required:
        if key not in bundle_manifest:
            raise ValueError(f"Bundle manifest at {bundle_manifest_path} is missing '{key}'")

    files = bundle_manifest["files"]
    if not isinstance(files, dict):
        raise TypeError(f"'files' in {bundle_manifest_path} must be an object")

    record = {
        "fixture_id": bundle_manifest["fixture_id"],
        "category": bundle_manifest["category"],
        "sample_weight": sample_weight,
        "dimensions": bundle_manifest["dimensions"],
        "mount": bundle_manifest["mount"],
        "files": files,
        "provenance": {
            "producer": DEFAULT_PRODUCER,
            "config_id": config_id,
            "upstream_ids": [bundle_manifest["selection_id"]],
            "upstream_bundle_relpath": bundle_manifest["normalized_rel_dir"] + "/bundle_manifest.json",
        },
    }

    optional_pairs = {
        "display_name": bundle_manifest.get("display_name"),
        "style_tags": bundle_manifest.get("style_tags"),
        "preferred_height_band_m": bundle_manifest.get("preferred_height_band_m"),
        "preferred_room_types": bundle_manifest.get("preferred_room_types"),
        "review_status": bundle_manifest.get("review_status"),
        "source": bundle_manifest.get("source"),
        "selection_id": bundle_manifest.get("selection_id"),
        "license": bundle_manifest.get("license"),
        "source_url": bundle_manifest.get("source_url") or source_metadata.get("source_url"),
    }
    for key, value in optional_pairs.items():
        if value is not None:
            record[key] = value

    return record


def write_wall_fixture_catalog(
    bundle_manifest_paths: list[Path],
    output_path: Path,
    *,
    sample_weight: float = 1.0,
    config_id: str = "wall_fixtures_v0_bundle_import_v1",
) -> list[dict]:
    records = [
        build_wall_fixture_record_from_bundle(
            path, sample_weight=sample_weight, config_id=config_id
        )
        for path in bundle_manifest_paths
    ]
    validate_wall_fixture_catalog_data(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return records


def build_wall_fixture_category_index(catalog_path: Path) -> dict:
    grouped: dict[str, list[dict]] = {}
    for record in validate_wall_fixture_catalog(catalog_path):
        category = record["category"]
        grouped.setdefault(category, []).append(record)

    categories = {}
    for category in sorted(grouped):
        records = grouped[category]
        categories[category] = {
            "sampling_policy": "uniform",
            "fixture_count": len(records),
            "fixture_ids": [record["fixture_id"] for record in records],
        }

    return {
        "catalog_path": repo_relative_path(catalog_path),
        "category_count": len(categories),
        "categories": categories,
    }


def write_wall_fixture_category_index(catalog_path: Path, output_path: Path) -> dict:
    index = build_wall_fixture_category_index(catalog_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index


def build_wall_fixture_catalog_manifest(
    catalog_path: Path,
    catalog_id: str,
    *,
    created_at: str | None = None,
    producer: dict | None = None,
) -> dict:
    records = validate_wall_fixture_catalog(catalog_path)
    return {
        "catalog_id": catalog_id,
        "fixture_count": len(records),
        "catalog_files": [_file_ref_for(catalog_path, base_dir=repo_root())],
        "producer": producer or DEFAULT_PRODUCER,
        "created_at": _timestamp(created_at),
    }


def write_wall_fixture_catalog_manifest(
    catalog_path: Path,
    output_path: Path,
    catalog_id: str,
    *,
    created_at: str | None = None,
    producer: dict | None = None,
) -> dict:
    manifest = build_wall_fixture_catalog_manifest(
        catalog_path=catalog_path,
        catalog_id=catalog_id,
        created_at=created_at,
        producer=producer,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def refresh_wall_fixture_catalog(
    *,
    catalog_id: str,
    bundle_manifest_paths: list[Path],
    catalog_output: Path,
    fixture_category_index_output: Path,
    manifest_output: Path,
    created_at: str | None = None,
    producer: dict | None = None,
) -> dict:
    records = write_wall_fixture_catalog(
        bundle_manifest_paths=bundle_manifest_paths,
        output_path=catalog_output,
    )
    index = write_wall_fixture_category_index(
        catalog_output, fixture_category_index_output
    )
    manifest = write_wall_fixture_catalog_manifest(
        catalog_path=catalog_output,
        output_path=manifest_output,
        catalog_id=catalog_id,
        created_at=created_at,
        producer=producer,
    )
    return {
        "catalog_id": catalog_id,
        "fixture_count": len(records),
        "catalog_output": str(catalog_output.resolve()),
        "category_count": index["category_count"],
        "fixture_category_index_output": str(fixture_category_index_output.resolve()),
        "manifest_output": str(manifest_output.resolve()),
        "manifest_created_at": manifest["created_at"],
    }
