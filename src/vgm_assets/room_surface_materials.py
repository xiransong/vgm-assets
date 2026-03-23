from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .catalog import _file_ref_for
from .paths import default_data_root
from .protocol import load_json, repo_root, validator_class_for_schema

DEFAULT_PRODUCER = {
    "repo": "vgm-assets",
    "version": "0.1.0-dev",
    "commit": "working_tree",
}
ROOM_SURFACE_MATERIAL_CATALOG_SCHEMA = (
    Path("schemas") / "local" / "room_surface_material_catalog_v0.schema.json"
)


def _timestamp(value: str | None = None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_room_surface_material_catalog(catalog_path: Path) -> list[dict]:
    payload = load_json(catalog_path)
    if not isinstance(payload, list):
        raise TypeError(f"Room-surface material catalog at {catalog_path} must be a JSON array")
    normalized: list[dict] = []
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise TypeError(
                f"Room-surface material catalog at {catalog_path} contains a non-object entry at index {index}"
            )
        normalized.append(record)
    return normalized


def room_surface_material_catalog_schema_path() -> Path:
    return repo_root() / ROOM_SURFACE_MATERIAL_CATALOG_SCHEMA


def validate_room_surface_material_catalog_data(payload: object) -> list[dict]:
    schema_path = room_surface_material_catalog_schema_path()
    schema = load_json(schema_path)
    validator_cls = validator_class_for_schema(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, list):
        raise TypeError("Room-surface material catalog payload must be a list after validation")
    return payload


def validate_room_surface_material_catalog(catalog_path: Path) -> list[dict]:
    payload = load_room_surface_material_catalog(catalog_path)
    return validate_room_surface_material_catalog_data(payload)


def _source_metadata_path(bundle_manifest_path: Path) -> Path:
    return bundle_manifest_path.with_name("source_metadata.json")


def build_room_surface_material_record_from_bundle(
    bundle_manifest_path: Path,
    *,
    sample_weight: float = 1.0,
    config_id: str = "room_surface_materials_v0_bundle_import_v1",
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
        "surface_type",
        "material_id",
        "display_name",
        "source",
        "tile_scale_m",
        "style_tags",
        "files",
    ]
    for key in required:
        if key not in bundle_manifest:
            raise ValueError(f"Bundle manifest at {bundle_manifest_path} is missing '{key}'")

    files = bundle_manifest["files"]
    if not isinstance(files, dict):
        raise TypeError(f"'files' in {bundle_manifest_path} must be an object")

    record = {
        "material_id": bundle_manifest["material_id"],
        "surface_type": bundle_manifest["surface_type"],
        "sample_weight": sample_weight,
        "source": bundle_manifest["source"],
        "display_name": bundle_manifest["display_name"],
        "style_tags": bundle_manifest["style_tags"],
        "tile_scale_m": bundle_manifest["tile_scale_m"],
        "files": files,
        "provenance": {
            "producer": DEFAULT_PRODUCER,
            "config_id": config_id,
            "upstream_ids": [bundle_manifest["selection_id"]],
            "upstream_bundle_relpath": bundle_manifest["normalized_rel_dir"] + "/bundle_manifest.json",
        },
    }

    optional_pairs = {
        "selection_id": bundle_manifest.get("selection_id"),
        "source_asset_id": source_metadata.get("source_asset_id"),
        "source_url": source_metadata.get("source_url"),
        "license": source_metadata.get("license"),
    }
    for key, value in optional_pairs.items():
        if value is not None:
            record[key] = value

    return record


def write_room_surface_material_catalog(
    bundle_manifest_paths: list[Path],
    output_path: Path,
    *,
    sample_weight: float = 1.0,
    config_id: str = "room_surface_materials_v0_bundle_import_v1",
) -> list[dict]:
    records = [
        build_room_surface_material_record_from_bundle(
            path,
            sample_weight=sample_weight,
            config_id=config_id,
        )
        for path in bundle_manifest_paths
    ]
    validate_room_surface_material_catalog_data(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return records


def build_surface_type_index(catalog_path: Path) -> dict:
    grouped: dict[str, list[dict]] = {}
    for record in validate_room_surface_material_catalog(catalog_path):
        surface_type = record["surface_type"]
        grouped.setdefault(surface_type, []).append(record)

    surface_types = {}
    for surface_type in sorted(grouped):
        records = grouped[surface_type]
        surface_types[surface_type] = {
            "sampling_policy": "uniform",
            "material_count": len(records),
            "material_ids": [record["material_id"] for record in records],
        }

    return {
        "catalog_path": repo_relative_path(catalog_path),
        "surface_type_count": len(surface_types),
        "surface_types": surface_types,
    }


def write_surface_type_index(catalog_path: Path, output_path: Path) -> dict:
    index = build_surface_type_index(catalog_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index


def build_material_catalog_manifest(
    catalog_path: Path,
    catalog_id: str,
    *,
    created_at: str | None = None,
    producer: dict | None = None,
) -> dict:
    records = validate_room_surface_material_catalog(catalog_path)
    return {
        "catalog_id": catalog_id,
        "material_count": len(records),
        "catalog_files": [_file_ref_for(catalog_path, base_dir=repo_root())],
        "producer": producer or DEFAULT_PRODUCER,
        "created_at": _timestamp(created_at),
    }


def write_material_catalog_manifest(
    catalog_path: Path,
    output_path: Path,
    catalog_id: str,
    *,
    created_at: str | None = None,
    producer: dict | None = None,
) -> dict:
    manifest = build_material_catalog_manifest(
        catalog_path=catalog_path,
        catalog_id=catalog_id,
        created_at=created_at,
        producer=producer,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def refresh_room_surface_material_catalog(
    *,
    catalog_id: str,
    bundle_manifest_paths: list[Path],
    catalog_output: Path,
    surface_type_index_output: Path,
    manifest_output: Path,
    created_at: str | None = None,
    producer: dict | None = None,
) -> dict:
    records = write_room_surface_material_catalog(
        bundle_manifest_paths=bundle_manifest_paths,
        output_path=catalog_output,
    )
    index = write_surface_type_index(catalog_output, surface_type_index_output)
    manifest = write_material_catalog_manifest(
        catalog_path=catalog_output,
        output_path=manifest_output,
        catalog_id=catalog_id,
        created_at=created_at,
        producer=producer,
    )
    return {
        "catalog_id": catalog_id,
        "material_count": len(records),
        "catalog_output": str(catalog_output.resolve()),
        "surface_type_count": index["surface_type_count"],
        "surface_type_index_output": str(surface_type_index_output.resolve()),
        "manifest_output": str(manifest_output.resolve()),
        "manifest_created_at": manifest["created_at"],
    }


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root()).as_posix()
    except ValueError:
        return str(resolved)
