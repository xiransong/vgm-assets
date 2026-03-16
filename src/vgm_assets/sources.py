from __future__ import annotations

import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .paths import default_data_root, default_raw_data_root, resolve_under
from .protocol import load_json


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp(value: str | None = None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_source_spec(spec_path: Path) -> dict:
    payload = load_json(spec_path)
    if not isinstance(payload, dict):
        raise TypeError(f"Source spec at {spec_path} must be a JSON object")
    required = ["source_id", "source_url", "license", "raw_archive", "processing"]
    for key in required:
        if key not in payload:
            raise ValueError(f"Source spec at {spec_path} is missing '{key}'")
    return payload


def register_raw_source(
    spec_path: Path,
    raw_file: Path,
    raw_data_root: Path | None = None,
    acquired_by: str | None = None,
    acquired_at: str | None = None,
    notes: str | None = None,
) -> dict:
    spec = load_source_spec(spec_path)
    raw_root = raw_data_root or default_raw_data_root()

    raw_archive = spec["raw_archive"]
    if not isinstance(raw_archive, dict):
        raise TypeError("raw_archive must be an object")

    canonical_relpath = raw_archive["canonical_relpath"]
    destination = resolve_under(raw_root, canonical_relpath)
    destination.parent.mkdir(parents=True, exist_ok=True)

    raw_file = raw_file.expanduser().resolve()
    if raw_file != destination.resolve():
        shutil.copy2(raw_file, destination)

    observed_sha256 = _sha256(destination)
    expected_sha256 = raw_archive.get("sha256")
    if expected_sha256 and observed_sha256 != expected_sha256:
        raise ValueError(
            f"SHA256 mismatch for {destination}: expected {expected_sha256}, got {observed_sha256}"
        )

    manifest = {
        "source_id": spec["source_id"],
        "source_url": spec["source_url"],
        "license": spec["license"],
        "acquisition_method": spec.get("acquisition_method", "manual_download"),
        "original_filename": raw_file.name,
        "canonical_filename": destination.name,
        "canonical_relpath": canonical_relpath,
        "size_bytes": destination.stat().st_size,
        "sha256": observed_sha256,
        "acquired_at": _timestamp(acquired_at),
        "acquired_by": acquired_by or os.environ.get("USER", "unknown"),
        "notes": notes or "",
    }

    manifest_path = destination.parent / "source_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    return manifest


def unpack_registered_zip(
    spec_path: Path,
    raw_data_root: Path | None = None,
    data_root: Path | None = None,
) -> dict:
    spec = load_source_spec(spec_path)
    raw_root = raw_data_root or default_raw_data_root()
    processed_root = data_root or default_data_root()

    raw_archive = spec["raw_archive"]
    processing = spec["processing"]
    archive_path = resolve_under(raw_root, raw_archive["canonical_relpath"])
    if not archive_path.exists():
        raise FileNotFoundError(f"Missing registered raw archive: {archive_path}")

    expected_sha256 = raw_archive.get("sha256")
    observed_sha256 = _sha256(archive_path)
    if expected_sha256 and observed_sha256 != expected_sha256:
        raise ValueError(
            f"SHA256 mismatch for {archive_path}: expected {expected_sha256}, got {observed_sha256}"
        )

    unpack_dir = resolve_under(processed_root, processing["unpack_relpath"])
    unpack_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(unpack_dir)

    manifest = {
        "source_id": spec["source_id"],
        "archive_relpath": raw_archive["canonical_relpath"],
        "archive_sha256": observed_sha256,
        "unpack_relpath": processing["unpack_relpath"],
        "unpacked_at": _timestamp(),
    }

    manifest_path = unpack_dir / "unpack_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    return manifest


def organize_kenney_selection(
    spec_path: Path,
    selection_path: Path,
    raw_data_root: Path | None = None,
    data_root: Path | None = None,
) -> dict:
    spec = load_source_spec(spec_path)
    raw_root = raw_data_root or default_raw_data_root()
    processed_root = data_root or default_data_root()
    processing = spec["processing"]
    archive_path = resolve_under(raw_root, spec["raw_archive"]["canonical_relpath"])
    if not archive_path.exists():
        raise FileNotFoundError(
            f"Missing registered raw archive at {archive_path}; run register-raw-source first"
        )

    unpack_dir = resolve_under(processed_root, processing["unpack_relpath"])
    if not unpack_dir.exists():
        raise FileNotFoundError(
            f"Missing unpacked source tree at {unpack_dir}; run unpack-registered-zip first"
        )

    payload = load_json(selection_path)
    if not isinstance(payload, list):
        raise TypeError(f"Selection file at {selection_path} must be a JSON array")

    selection_records: list[dict] = []
    rel_dirs: list[Path] = []
    for entry in payload:
        if not isinstance(entry, dict):
            raise TypeError("Selection entries must be objects")

        normalized_rel_dir = entry.get("normalized_rel_dir")
        if not isinstance(normalized_rel_dir, str):
            raise ValueError(
                f"Selection entry {entry.get('selection_id')} is missing normalized_rel_dir"
            )
        rel_dir = Path(normalized_rel_dir)
        normalized_root_rel = Path(processing["normalized_root_relpath"])
        if normalized_root_rel not in rel_dir.parents:
            raise ValueError(
                f"Selection entry {entry.get('selection_id')} must live under "
                f"{processing['normalized_root_relpath']}"
            )
        rel_dirs.append(rel_dir)
        destination = resolve_under(processed_root, rel_dir)
        destination.mkdir(parents=True, exist_ok=True)

        model_src = unpack_dir / entry["raw_model_rel"]
        preview_src = unpack_dir / entry["raw_preview_rel"]
        if not model_src.exists():
            raise FileNotFoundError(f"Missing raw model file: {model_src}")
        if not preview_src.exists():
            raise FileNotFoundError(f"Missing raw preview file: {preview_src}")

        shutil.copy2(model_src, destination / "model.glb")
        shutil.copy2(preview_src, destination / "preview.png")

        source_metadata = {
            "asset_id": entry["asset_id"],
            "category": entry["category"],
            "source": entry["source_pack"],
            "license": entry["license"],
            "source_name": entry["source_name"],
            "source_model_path": entry["raw_model_rel"],
            "source_preview_path": entry["raw_preview_rel"],
            "normalized_files": {
                "mesh": "model.glb",
                "preview_image": "preview.png",
            },
        }
        with (destination / "source_metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(source_metadata, handle, indent=2)
            handle.write("\n")

        selection_records.append(entry)

    slice_root_rel = Path(os.path.commonpath([path.as_posix() for path in rel_dirs]))
    slice_root = resolve_under(processed_root, slice_root_rel)

    manifest_assets = []
    for entry in selection_records:
        asset_rel_dir = Path(entry["normalized_rel_dir"]).relative_to(slice_root_rel)
        manifest_assets.append(
            {
                "category": entry["category"],
                "asset_id": entry["asset_id"],
                "source_name": entry["source_name"],
                "normalized_dir": asset_rel_dir.as_posix(),
            }
        )

    selection_manifest = {
        "selection_id": f"{spec['source_id']}_{slice_root_rel.name}",
        "source_pack": spec["source_id"],
        "license": spec["license"],
        "asset_count": len(manifest_assets),
        "assets": manifest_assets,
    }
    with (slice_root / "selection_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(selection_manifest, handle, indent=2)
        handle.write("\n")

    return {
        "selection_id": selection_manifest["selection_id"],
        "asset_count": len(manifest_assets),
        "slice_root": str(slice_root),
    }
