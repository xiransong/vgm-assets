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
    required = ["source_id", "source_url", "license", "processing"]
    for key in required:
        if key not in payload:
            raise ValueError(f"Source spec at {spec_path} is missing '{key}'")
    return payload


def load_selection_list(selection_path: Path) -> list[dict]:
    payload = load_json(selection_path)
    if not isinstance(payload, list):
        raise TypeError(f"Selection file at {selection_path} must be a JSON array")
    records: list[dict] = []
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            raise TypeError(
                f"Selection file at {selection_path} contains a non-object entry at index {index}"
            )
        records.append(entry)
    return records


def _require_entry(entry: dict, key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"Selection entry {entry.get('selection_id', '<unknown>')} is missing '{key}'"
        )
    return value


def build_poly_haven_room_surface_download_plan(
    spec_path: Path,
    selection_path: Path,
    created_at: str | None = None,
) -> dict:
    spec = load_source_spec(spec_path)
    raw_storage = spec.get("raw_storage")
    if not isinstance(raw_storage, dict):
        raise TypeError("Poly Haven source spec must define raw_storage")

    selection_records = load_selection_list(selection_path)
    downloads: list[dict] = []
    for entry in selection_records:
        selection_id = _require_entry(entry, "selection_id")
        surface_type = _require_entry(entry, "surface_type")
        material_id = _require_entry(entry, "material_id")
        source_asset_id = _require_entry(entry, "source_asset_id")
        preferred_resolution = _require_entry(entry, "preferred_resolution")
        preferred_format = _require_entry(entry, "preferred_format")

        raw_asset_rel_dir = (
            Path(raw_storage["root_relpath"])
            / source_asset_id
            / f"{preferred_resolution}_{preferred_format}"
        )
        bundle_rel_dir = (
            Path(spec["processing"]["normalized_root_relpath"])
            / surface_type
            / material_id
        )
        downloads.append(
            {
                "selection_id": selection_id,
                "surface_type": surface_type,
                "material_id": material_id,
                "source_asset_id": source_asset_id,
                "source_url": _require_entry(entry, "source_url"),
                "preferred_resolution": preferred_resolution,
                "preferred_format": preferred_format,
                "tile_scale_m": entry.get("tile_scale_m", 1.0),
                "style_tags": entry.get("style_tags", []),
                "raw_asset_rel_dir": raw_asset_rel_dir.as_posix(),
                "source_manifest_relpath": (
                    raw_asset_rel_dir / "source_manifest.json"
                ).as_posix(),
                "normalized_rel_dir": bundle_rel_dir.as_posix(),
                "api_request": {
                    "asset_id": source_asset_id,
                    "resolution": preferred_resolution,
                    "format": preferred_format,
                    "normal_space": "gl",
                },
                "expected_files": [
                    {
                        "logical_name": "base_color",
                        "source_map": "Diffuse",
                        "filename": f"base_color.{preferred_format}",
                        "required": True,
                    },
                    {
                        "logical_name": "roughness",
                        "source_map": "Rough",
                        "filename": f"roughness.{preferred_format}",
                        "required": True,
                    },
                    {
                        "logical_name": "normal",
                        "source_map": "NormalGL",
                        "filename": f"normal_gl.{preferred_format}",
                        "required": True,
                    },
                    {
                        "logical_name": "ao",
                        "source_map": "AO",
                        "filename": f"ao.{preferred_format}",
                        "required": False,
                    },
                    {
                        "logical_name": "displacement",
                        "source_map": "Displacement",
                        "filename": f"displacement.{preferred_format}",
                        "required": False,
                    },
                    {
                        "logical_name": "preview_image",
                        "source_map": "Thumbnail",
                        "filename": "preview.jpg",
                        "required": True,
                    },
                ],
            }
        )

    return {
        "plan_id": "poly_haven_room_surface_download_plan_v0",
        "source_id": spec["source_id"],
        "selection_path": selection_path.as_posix(),
        "planned_at": _timestamp(created_at),
        "raw_data_root_env_var": "VGM_ASSETS_RAW_DATA_ROOT",
        "raw_storage_root_relpath": raw_storage["root_relpath"],
        "api": spec.get("api", {}),
        "download_count": len(downloads),
        "downloads": downloads,
    }


def write_poly_haven_room_surface_download_plan(
    spec_path: Path,
    selection_path: Path,
    output_path: Path,
    created_at: str | None = None,
) -> dict:
    plan = build_poly_haven_room_surface_download_plan(
        spec_path=spec_path,
        selection_path=selection_path,
        created_at=created_at,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return plan


def build_poly_haven_room_surface_layout_plan(
    spec_path: Path,
    selection_path: Path,
    created_at: str | None = None,
) -> dict:
    spec = load_source_spec(spec_path)
    selection_records = load_selection_list(selection_path)

    bundles: list[dict] = []
    for entry in selection_records:
        surface_type = _require_entry(entry, "surface_type")
        material_id = _require_entry(entry, "material_id")
        preferred_format = _require_entry(entry, "preferred_format")
        normalized_rel_dir = (
            Path(spec["processing"]["normalized_root_relpath"])
            / surface_type
            / material_id
        )
        bundles.append(
            {
                "selection_id": _require_entry(entry, "selection_id"),
                "surface_type": surface_type,
                "material_id": material_id,
                "normalized_rel_dir": normalized_rel_dir.as_posix(),
                "files": {
                    "base_color": f"base_color.{preferred_format}",
                    "roughness": f"roughness.{preferred_format}",
                    "normal": f"normal_gl.{preferred_format}",
                    "ao": f"ao.{preferred_format}",
                    "displacement": f"displacement.{preferred_format}",
                    "preview_image": "preview.jpg",
                    "source_metadata": "source_metadata.json",
                    "bundle_manifest": "bundle_manifest.json",
                },
            }
        )

    return {
        "layout_id": "poly_haven_room_surface_layout_v0",
        "source_id": spec["source_id"],
        "selection_path": selection_path.as_posix(),
        "planned_at": _timestamp(created_at),
        "data_root_env_var": "VGM_ASSETS_DATA_ROOT",
        "normalized_root_relpath": spec["processing"]["normalized_root_relpath"],
        "bundle_count": len(bundles),
        "bundles": bundles,
    }


def write_poly_haven_room_surface_layout_plan(
    spec_path: Path,
    selection_path: Path,
    output_path: Path,
    created_at: str | None = None,
) -> dict:
    plan = build_poly_haven_room_surface_layout_plan(
        spec_path=spec_path,
        selection_path=selection_path,
        created_at=created_at,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return plan


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

    payload = load_selection_list(selection_path)

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


def rebuild_kenney_selection(
    spec_path: Path,
    selection_path: Path,
    raw_file: Path | None = None,
    raw_data_root: Path | None = None,
    data_root: Path | None = None,
    acquired_by: str | None = None,
    acquired_at: str | None = None,
    notes: str | None = None,
) -> dict:
    spec = load_source_spec(spec_path)
    raw_root = raw_data_root or default_raw_data_root()
    archive_path = resolve_under(raw_root, spec["raw_archive"]["canonical_relpath"])

    registered = False
    if raw_file is not None or not archive_path.exists():
        if raw_file is None:
            raise FileNotFoundError(
                f"Missing registered raw archive at {archive_path}; provide --raw-file"
            )
        register_raw_source(
            spec_path=spec_path,
            raw_file=raw_file,
            raw_data_root=raw_root,
            acquired_by=acquired_by,
            acquired_at=acquired_at,
            notes=notes,
        )
        registered = True

    unpack_manifest = unpack_registered_zip(
        spec_path=spec_path,
        raw_data_root=raw_root,
        data_root=data_root,
    )
    organize_summary = organize_kenney_selection(
        spec_path=spec_path,
        selection_path=selection_path,
        raw_data_root=raw_root,
        data_root=data_root,
    )
    return {
        "registered_raw_source": registered,
        "raw_archive": str(archive_path),
        "unpack_relpath": unpack_manifest["unpack_relpath"],
        "selection_id": organize_summary["selection_id"],
        "asset_count": organize_summary["asset_count"],
        "slice_root": organize_summary["slice_root"],
    }
