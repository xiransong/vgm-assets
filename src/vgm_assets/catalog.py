from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .protocol import default_protocol_root, load_json, validate_instance

ASSET_SCHEMA = "schemas/core/asset_spec.schema.json"
MANIFEST_SCHEMA = "schemas/manifests/asset_catalog_manifest.schema.json"
DEFAULT_PROTOCOL_VERSION = "v0"
DEFAULT_PRODUCER = {
    "repo": "vgm-assets",
    "version": "0.1.0-dev",
    "commit": "working_tree",
}


def load_asset_specs(catalog_path: Path) -> list[dict]:
    payload = load_json(catalog_path)
    if not isinstance(payload, list):
        raise TypeError(f"Catalog at {catalog_path} must be a JSON array")
    normalized: list[dict] = []
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise TypeError(
                f"Catalog at {catalog_path} contains a non-object entry at index {index}"
            )
        normalized.append(record)
    return normalized


def validate_asset_catalog(
    catalog_path: Path,
    protocol_root: Path | None = None,
) -> list[dict]:
    root = protocol_root or default_protocol_root()
    records = load_asset_specs(catalog_path)
    for record in records:
        validate_instance(record, ASSET_SCHEMA, root)
    return records


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_ref_for(path: Path, base_dir: Path) -> dict:
    relative = path.resolve().relative_to(base_dir.resolve())
    return {
        "path": relative.as_posix(),
        "format": path.suffix.lstrip(".") or "json",
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


def build_catalog_manifest(
    catalog_path: Path,
    catalog_id: str,
    protocol_root: Path | None = None,
    created_at: str | None = None,
    producer: dict | None = None,
) -> dict:
    root = protocol_root or default_protocol_root()
    records = validate_asset_catalog(catalog_path, root)
    manifest = {
        "catalog_id": catalog_id,
        "asset_count": len(records),
        "catalog_files": [_file_ref_for(catalog_path, base_dir=repo_root())],
        "protocol_version": DEFAULT_PROTOCOL_VERSION,
        "producer": producer or DEFAULT_PRODUCER,
        "created_at": created_at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    validate_instance(manifest, MANIFEST_SCHEMA, root)
    return manifest


def write_catalog_manifest(
    catalog_path: Path,
    output_path: Path,
    catalog_id: str,
    protocol_root: Path | None = None,
    created_at: str | None = None,
    producer: dict | None = None,
) -> dict:
    manifest = build_catalog_manifest(
        catalog_path=catalog_path,
        catalog_id=catalog_id,
        protocol_root=protocol_root,
        created_at=created_at,
        producer=producer,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    return manifest


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]
