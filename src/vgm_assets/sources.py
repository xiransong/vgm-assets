from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .objaverse import (
    review_queue_output_path_for_harvest,
    validate_objaverse_furniture_metadata_harvest,
    validate_objaverse_furniture_metadata_harvest_data,
    write_objaverse_furniture_review_queue,
)
from .paths import default_data_root, default_raw_data_root, resolve_under
from .protocol import load_json


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_ref(path: Path, base_dir: Path) -> dict:
    relative = path.resolve().relative_to(base_dir.resolve())
    return {
        "path": relative.as_posix(),
        "format": path.suffix.lstrip(".") or "bin",
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


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


def load_objaverse_metadata_source_spec(spec_path: Path) -> dict:
    payload = load_json(spec_path)
    if not isinstance(payload, dict):
        raise TypeError(f"Objaverse metadata source spec at {spec_path} must be a JSON object")
    required = ["source_id", "source_url", "raw_layout"]
    for key in required:
        if key not in payload:
            raise ValueError(f"Objaverse metadata source spec at {spec_path} is missing '{key}'")
    raw_layout = payload.get("raw_layout")
    if not isinstance(raw_layout, dict):
        raise TypeError("Objaverse metadata source spec must define raw_layout")
    if "root_rel" not in raw_layout:
        raise ValueError("Objaverse metadata source spec raw_layout is missing 'root_rel'")
    return payload


def _coerce_string_list(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    items = [str(item).strip() for item in value if str(item).strip()]
    return items or None


def _coerce_nonnegative_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    return None


def _coerce_bounds(value: object) -> dict | None:
    if not isinstance(value, dict):
        return None
    try:
        width = float(value["width"])
        depth = float(value["depth"])
        height = float(value["height"])
    except (KeyError, TypeError, ValueError):
        return None
    if width < 0 or depth < 0 or height < 0:
        return None
    return {
        "width": width,
        "depth": depth,
        "height": height,
    }


def _first_value(entry: dict, keys: list[str]) -> object:
    for key in keys:
        if key in entry:
            return entry[key]
    return None


def _normalize_objaverse_metadata_record(entry: dict) -> dict | None:
    object_uid = _first_value(entry, ["object_uid", "uid", "id"])
    source_url = _first_value(entry, ["source_url", "url"])
    title = _first_value(entry, ["title", "name"])
    license_value = _first_value(entry, ["license", "license_name", "license_label"])

    if not all(isinstance(value, str) and value.strip() for value in [object_uid, source_url, title, license_value]):
        return None

    normalized = {
        "object_uid": str(object_uid).strip(),
        "source_url": str(source_url).strip(),
        "title": str(title).strip(),
        "license": str(license_value).strip(),
    }

    optional_string_lists = {
        "source_tags": ["source_tags", "tags"],
        "source_categories": ["source_categories", "categories"],
        "available_formats": ["available_formats", "formats"],
    }
    for out_key, in_keys in optional_string_lists.items():
        value = _coerce_string_list(_first_value(entry, in_keys))
        if value is not None:
            normalized[out_key] = value

    optional_strings = {
        "description": ["description", "caption", "text"],
        "thumbnail_url": ["thumbnail_url", "preview_url", "thumbnail"],
        "metadata_path": ["metadata_path"],
        "payload_ref": ["payload_ref", "mesh_path", "glb_path"],
    }
    for out_key, in_keys in optional_strings.items():
        value = _first_value(entry, in_keys)
        if isinstance(value, str) and value.strip():
            normalized[out_key] = value.strip()

    triangle_count = _coerce_nonnegative_int(_first_value(entry, ["triangle_count", "triangles"]))
    if triangle_count is not None:
        normalized["triangle_count"] = triangle_count

    vertex_count = _coerce_nonnegative_int(_first_value(entry, ["vertex_count", "vertices"]))
    if vertex_count is not None:
        normalized["vertex_count"] = vertex_count

    bounds = _coerce_bounds(_first_value(entry, ["bounds"]))
    if bounds is not None:
        normalized["bounds"] = bounds

    return normalized


def _load_objaverse_metadata_records(raw_path: Path) -> list[dict]:
    suffix = raw_path.suffix.lower()
    if suffix == ".jsonl":
        records: list[dict] = []
        with raw_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise TypeError(
                        f"Objaverse metadata line {line_number} in {raw_path} must be a JSON object"
                    )
                records.append(payload)
        return records

    payload = load_json(raw_path)
    if isinstance(payload, dict) and "records" in payload:
        records = payload["records"]
        if not isinstance(records, list):
            raise TypeError(f"'records' in {raw_path} must be a JSON array")
        if any(not isinstance(record, dict) for record in records):
            raise TypeError(f"All records in {raw_path} must be JSON objects")
        return records

    if isinstance(payload, list):
        if any(not isinstance(record, dict) for record in payload):
            raise TypeError(f"All records in {raw_path} must be JSON objects")
        return payload

    if isinstance(payload, dict):
        return [payload]

    raise TypeError(f"Unsupported Objaverse metadata payload shape in {raw_path}")


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


def find_selection_entry(selection_path: Path, selection_id: str) -> dict:
    for entry in load_selection_list(selection_path):
        if entry.get("selection_id") == selection_id:
            return entry
    raise ValueError(
        f"Selection id '{selection_id}' not found in {selection_path.as_posix()}"
    )


def _poly_haven_expected_files(entry: dict) -> list[dict]:
    preferred_format = _require_entry(entry, "preferred_format")
    return [
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
            "source_map": "nor_gl",
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
            "source_map": "thumbnail_url",
            "filename": "preview.png",
            "required": True,
        },
    ]


def _poly_haven_raw_rel_dir(spec: dict, entry: dict) -> Path:
    raw_storage = spec.get("raw_storage")
    if not isinstance(raw_storage, dict):
        raise TypeError("Poly Haven source spec must define raw_storage")
    source_asset_id = _require_entry(entry, "source_asset_id")
    preferred_resolution = _require_entry(entry, "preferred_resolution")
    preferred_format = _require_entry(entry, "preferred_format")
    return (
        Path(raw_storage["root_relpath"])
        / source_asset_id
        / f"{preferred_resolution}_{preferred_format}"
    )


def _poly_haven_normalized_rel_dir(spec: dict, entry: dict) -> Path:
    processing = spec.get("processing")
    if not isinstance(processing, dict):
        raise TypeError("Poly Haven source spec must define processing")
    return (
        Path(processing["normalized_root_relpath"])
        / _require_entry(entry, "surface_type")
        / _require_entry(entry, "material_id")
    )


def _poly_haven_source_manifest_path(
    spec: dict,
    entry: dict,
    raw_root: Path,
) -> Path:
    return resolve_under(raw_root, _poly_haven_raw_rel_dir(spec, entry)) / "source_manifest.json"


def _download_url(url: str, destination: Path, user_agent: str) -> None:
    request = Request(url, headers={"User-Agent": user_agent})
    with urlopen(request) as response, destination.open("wb") as handle:
        shutil.copyfileobj(response, handle)


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
                        "source_map": "nor_gl",
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
                        "source_map": "thumbnail_url",
                        "filename": "preview.png",
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
                    "preview_image": "preview.png",
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


def register_poly_haven_room_surface_material(
    spec_path: Path,
    selection_path: Path,
    selection_id: str,
    raw_material_dir: Path,
    raw_data_root: Path | None = None,
    acquired_at: str | None = None,
    acquired_by: str | None = None,
    notes: str | None = None,
) -> dict:
    spec = load_source_spec(spec_path)
    entry = find_selection_entry(selection_path, selection_id)
    raw_root = raw_data_root or default_raw_data_root()

    source_dir = raw_material_dir.expanduser().resolve()
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Missing raw material directory: {source_dir}")

    raw_rel_dir = _poly_haven_raw_rel_dir(spec, entry)
    destination_dir = resolve_under(raw_root, raw_rel_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    files_manifest: list[dict] = []
    missing_optional: list[str] = []
    for file_spec in _poly_haven_expected_files(entry):
        logical_name = file_spec["logical_name"]
        filename = file_spec["filename"]
        required = file_spec["required"]
        source_path = source_dir / filename
        if not source_path.exists():
            if required:
                raise FileNotFoundError(
                    f"Missing required Poly Haven file for {selection_id}: {source_path}"
                )
            missing_optional.append(logical_name)
            continue

        destination_path = destination_dir / filename
        if source_path != destination_path:
            shutil.copy2(source_path, destination_path)

        files_manifest.append(
            {
                "logical_name": logical_name,
                "filename": filename,
                "raw_relpath": (raw_rel_dir / filename).as_posix(),
                "sha256": _sha256(destination_path),
                "size_bytes": destination_path.stat().st_size,
            }
        )

    manifest = {
        "manifest_version": "v0",
        "source_id": spec["source_id"],
        "source_asset_id": _require_entry(entry, "source_asset_id"),
        "selection_id": selection_id,
        "surface_type": _require_entry(entry, "surface_type"),
        "material_id": _require_entry(entry, "material_id"),
        "source_url": _require_entry(entry, "source_url"),
        "license": entry.get("license", spec["license"]),
        "preferred_resolution": _require_entry(entry, "preferred_resolution"),
        "preferred_format": _require_entry(entry, "preferred_format"),
        "raw_asset_rel_dir": raw_rel_dir.as_posix(),
        "registered_at": _timestamp(acquired_at),
        "registered_by": acquired_by or os.environ.get("USER", "unknown"),
        "files": files_manifest,
        "missing_optional_files": missing_optional,
        "notes": notes or "",
    }

    manifest_path = destination_dir / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def fetch_poly_haven_room_surface_material(
    spec_path: Path,
    selection_path: Path,
    selection_id: str,
    raw_data_root: Path | None = None,
    acquired_at: str | None = None,
    acquired_by: str | None = None,
    notes: str | None = None,
    user_agent: str | None = None,
) -> dict:
    spec = load_source_spec(spec_path)
    entry = find_selection_entry(selection_path, selection_id)
    api = spec.get("api")
    if not isinstance(api, dict):
        raise TypeError("Poly Haven source spec must define api")

    source_asset_id = _require_entry(entry, "source_asset_id")
    api_base_url = _require_entry(api, "base_url").rstrip("/")
    ua = user_agent or "vgm-assets/0.1 (research prototype; contact=local)"

    with tempfile.TemporaryDirectory(prefix="vgm-assets-polyhaven-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        files_json_path = temp_dir / "api_files.json"
        info_json_path = temp_dir / "api_info.json"
        _download_url(
            f"{api_base_url}/files/{source_asset_id}",
            files_json_path,
            ua,
        )
        _download_url(
            f"{api_base_url}/info/{source_asset_id}",
            info_json_path,
            ua,
        )

        files_payload = load_json(files_json_path)
        info_payload = load_json(info_json_path)
        if not isinstance(files_payload, dict):
            raise TypeError("Poly Haven files response must be an object")
        if not isinstance(info_payload, dict):
            raise TypeError("Poly Haven info response must be an object")

        resolution = _require_entry(entry, "preferred_resolution")
        fmt = _require_entry(entry, "preferred_format")

        for file_spec in _poly_haven_expected_files(entry):
            logical_name = file_spec["logical_name"]
            filename = file_spec["filename"]
            required = file_spec["required"]

            if logical_name == "preview_image":
                preview_url = info_payload.get("thumbnail_url")
                if not isinstance(preview_url, str) or not preview_url:
                    if required:
                        raise ValueError(
                            f"Poly Haven info response for {source_asset_id} is missing thumbnail_url"
                        )
                    continue
                preview_suffix = Path(urlparse(preview_url).path).suffix or ".png"
                destination_name = f"preview{preview_suffix}"
                _download_url(preview_url, temp_dir / destination_name, ua)
                continue

            source_map = file_spec.get("source_map")
            source_record = files_payload.get(source_map)
            if not isinstance(source_record, dict):
                if required:
                    raise ValueError(
                        f"Poly Haven files response for {source_asset_id} is missing map '{source_map}'"
                    )
                continue
            resolution_record = source_record.get(resolution)
            if not isinstance(resolution_record, dict):
                if required:
                    raise ValueError(
                        f"Poly Haven files response for {source_asset_id} is missing resolution '{resolution}' for map '{source_map}'"
                    )
                continue
            format_record = resolution_record.get(fmt)
            if not isinstance(format_record, dict):
                if required:
                    raise ValueError(
                        f"Poly Haven files response for {source_asset_id} is missing format '{fmt}' for map '{source_map}' at resolution '{resolution}'"
                    )
                continue

            download_url = format_record.get("url")
            if not isinstance(download_url, str) or not download_url:
                if required:
                    raise ValueError(
                        f"Poly Haven files response for {source_asset_id} is missing download url for map '{source_map}'"
                    )
                continue

            _download_url(download_url, temp_dir / filename, ua)

        manifest = register_poly_haven_room_surface_material(
            spec_path=spec_path,
            selection_path=selection_path,
            selection_id=selection_id,
            raw_material_dir=temp_dir,
            raw_data_root=raw_data_root,
            acquired_at=acquired_at,
            acquired_by=acquired_by,
            notes=notes,
        )

        raw_root = raw_data_root or default_raw_data_root()
        raw_rel_dir = _poly_haven_raw_rel_dir(spec, entry)
        raw_dir = resolve_under(raw_root, raw_rel_dir)
        shutil.copy2(files_json_path, raw_dir / "api_files.json")
        shutil.copy2(info_json_path, raw_dir / "api_info.json")

        source_manifest_path = raw_dir / "source_manifest.json"
        manifest["api_metadata"] = {
            "files_endpoint": f"{api_base_url}/files/{source_asset_id}",
            "info_endpoint": f"{api_base_url}/info/{source_asset_id}",
            "api_files_relpath": (raw_rel_dir / "api_files.json").as_posix(),
            "api_info_relpath": (raw_rel_dir / "api_info.json").as_posix(),
            "thumbnail_url": info_payload.get("thumbnail_url", ""),
            "files_hash": info_payload.get("files_hash", ""),
        }
        source_manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest


def normalize_poly_haven_room_surface_material(
    spec_path: Path,
    selection_path: Path,
    selection_id: str,
    raw_data_root: Path | None = None,
    data_root: Path | None = None,
    created_at: str | None = None,
) -> dict:
    spec = load_source_spec(spec_path)
    entry = find_selection_entry(selection_path, selection_id)
    raw_root = raw_data_root or default_raw_data_root()
    processed_root = data_root or default_data_root()

    source_manifest_path = _poly_haven_source_manifest_path(spec, entry, raw_root)
    if not source_manifest_path.exists():
        raise FileNotFoundError(
            f"Missing registered Poly Haven source manifest: {source_manifest_path}"
        )
    source_manifest = load_json(source_manifest_path)
    if not isinstance(source_manifest, dict):
        raise TypeError(f"Source manifest at {source_manifest_path} must be an object")

    normalized_rel_dir = _poly_haven_normalized_rel_dir(spec, entry)
    normalized_dir = resolve_under(processed_root, normalized_rel_dir)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    available_files = {
        item["logical_name"]: item
        for item in source_manifest.get("files", [])
        if isinstance(item, dict) and "logical_name" in item and "raw_relpath" in item
    }

    normalized_files: dict[str, dict] = {}
    for file_spec in _poly_haven_expected_files(entry):
        logical_name = file_spec["logical_name"]
        required = file_spec["required"]
        source_file_entry = available_files.get(logical_name)
        if source_file_entry is None:
            if required:
                raise FileNotFoundError(
                    f"Registered source for {selection_id} is missing required file '{logical_name}'"
                )
            continue

        raw_file_path = resolve_under(raw_root, source_file_entry["raw_relpath"])
        if not raw_file_path.exists():
            raise FileNotFoundError(f"Missing registered raw file: {raw_file_path}")

        destination_path = normalized_dir / source_file_entry["filename"]
        shutil.copy2(raw_file_path, destination_path)
        normalized_files[logical_name] = {
            "path": (normalized_rel_dir / destination_path.name).as_posix(),
            "format": destination_path.suffix.lstrip(".") or "bin",
            "sha256": _sha256(destination_path),
            "size_bytes": destination_path.stat().st_size,
        }

    source_metadata = {
        "selection_id": selection_id,
        "surface_type": _require_entry(entry, "surface_type"),
        "material_id": _require_entry(entry, "material_id"),
        "display_name": _require_entry(entry, "display_name"),
        "source": spec["source_id"],
        "source_asset_id": _require_entry(entry, "source_asset_id"),
        "source_url": _require_entry(entry, "source_url"),
        "license": entry.get("license", spec["license"]),
        "style_tags": entry.get("style_tags", []),
        "tile_scale_m": entry.get("tile_scale_m", 1.0),
        "normalized_files": {key: Path(value["path"]).name for key, value in normalized_files.items()},
        "upstream": {
            "raw_source_manifest_relpath": source_manifest_path.relative_to(raw_root).as_posix()
        },
    }
    (normalized_dir / "source_metadata.json").write_text(
        json.dumps(source_metadata, indent=2) + "\n",
        encoding="utf-8",
    )

    bundle_manifest = {
        "manifest_version": "v0",
        "bundle_id": _require_entry(entry, "material_id"),
        "selection_id": selection_id,
        "surface_type": _require_entry(entry, "surface_type"),
        "material_id": _require_entry(entry, "material_id"),
        "display_name": _require_entry(entry, "display_name"),
        "source": spec["source_id"],
        "normalized_rel_dir": normalized_rel_dir.as_posix(),
        "created_at": _timestamp(created_at),
        "tile_scale_m": entry.get("tile_scale_m", 1.0),
        "style_tags": entry.get("style_tags", []),
        "files": normalized_files,
        "upstream": {
            "raw_source_manifest_relpath": source_manifest_path.relative_to(raw_root).as_posix()
        },
    }
    (normalized_dir / "bundle_manifest.json").write_text(
        json.dumps(bundle_manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "selection_id": selection_id,
        "material_id": bundle_manifest["material_id"],
        "surface_type": bundle_manifest["surface_type"],
        "normalized_rel_dir": normalized_rel_dir.as_posix(),
        "normalized_file_count": len(normalized_files),
        "bundle_manifest": (normalized_rel_dir / "bundle_manifest.json").as_posix(),
    }


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


def register_objaverse_raw_metadata_source(
    spec_path: Path,
    raw_file: Path,
    raw_data_root: Path | None = None,
    acquired_by: str | None = None,
    acquired_at: str | None = None,
    notes: str | None = None,
) -> dict:
    spec = load_objaverse_metadata_source_spec(spec_path)
    raw_root = raw_data_root or default_raw_data_root()

    raw_layout = spec["raw_layout"]
    root_rel = raw_layout["root_rel"]
    destination_dir = resolve_under(raw_root, root_rel)
    destination_dir.mkdir(parents=True, exist_ok=True)

    raw_file = raw_file.expanduser().resolve()
    accepted_extensions = raw_layout.get("accepted_extensions", [])
    if accepted_extensions:
        allowed = {str(value).lower() for value in accepted_extensions}
        if raw_file.suffix.lower() not in allowed:
            raise ValueError(
                f"Unsupported Objaverse metadata file extension '{raw_file.suffix}' for {raw_file}. "
                f"Allowed extensions: {sorted(allowed)}"
            )

    destination = destination_dir / raw_file.name
    if raw_file != destination.resolve():
        shutil.copy2(raw_file, destination)

    observed_sha256 = _sha256(destination)
    canonical_relpath = (Path(root_rel) / raw_file.name).as_posix()
    manifest = {
        "source_id": spec["source_id"],
        "source_family": spec.get("source_family", "objaverse"),
        "display_name": spec.get("display_name", spec["source_id"]),
        "source_url": spec["source_url"],
        "acquisition_method": spec.get("acquisition_method", "manual_export"),
        "original_filename": raw_file.name,
        "canonical_filename": destination.name,
        "canonical_relpath": canonical_relpath,
        "size_bytes": destination.stat().st_size,
        "sha256": observed_sha256,
        "preferred_formats": raw_layout.get("preferred_formats", []),
        "accepted_extensions": accepted_extensions,
        "acquired_at": _timestamp(acquired_at),
        "acquired_by": acquired_by or os.environ.get("USER", "unknown"),
        "notes": notes or "",
    }

    manifest_path = destination_dir / "source_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    return manifest


def import_objaverse_furniture_metadata_harvest(
    spec_path: Path,
    raw_data_root: Path | None = None,
    data_root: Path | None = None,
    output_path: Path | None = None,
    created_at: str | None = None,
) -> dict:
    spec = load_objaverse_metadata_source_spec(spec_path)
    raw_root = raw_data_root or default_raw_data_root()
    processed_root = data_root or default_data_root()

    raw_root_rel = Path(spec["raw_layout"]["root_rel"])
    manifest_path = resolve_under(raw_root, raw_root_rel / "source_manifest.json")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing registered Objaverse raw metadata manifest: {manifest_path}")

    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise TypeError(f"Objaverse source manifest at {manifest_path} must be a JSON object")

    canonical_relpath = manifest.get("canonical_relpath")
    if not isinstance(canonical_relpath, str) or not canonical_relpath:
        raise ValueError(f"Objaverse source manifest at {manifest_path} is missing canonical_relpath")

    raw_metadata_path = resolve_under(raw_root, canonical_relpath)
    if not raw_metadata_path.exists():
        raise FileNotFoundError(f"Missing registered Objaverse raw metadata file: {raw_metadata_path}")

    raw_records = _load_objaverse_metadata_records(raw_metadata_path)
    normalized_records: list[dict] = []
    skipped_records = 0
    for entry in raw_records:
        normalized = _normalize_objaverse_metadata_record(entry)
        if normalized is None:
            skipped_records += 1
            continue
        normalized_records.append(normalized)

    harvest = {
        "harvest_id": f"{spec['source_id']}__{raw_metadata_path.stem}",
        "source_id": spec["source_id"],
        "created_at": _timestamp(created_at),
        "record_count": len(normalized_records),
        "notes": (
            f"Imported from registered raw metadata artifact {raw_metadata_path.name}. "
            f"Skipped {skipped_records} invalid records during normalization."
        ),
        "records": normalized_records,
    }
    validate_objaverse_furniture_metadata_harvest_data(harvest)

    if output_path is None:
        processed_layout = spec.get("processed_layout")
        if not isinstance(processed_layout, dict):
            raise TypeError("Objaverse metadata source spec must define processed_layout")
        harvest_root_rel = processed_layout.get("metadata_harvest_root_rel")
        if not isinstance(harvest_root_rel, str) or not harvest_root_rel:
            raise ValueError("Objaverse metadata source spec processed_layout is missing metadata_harvest_root_rel")
        output_path = resolve_under(
            processed_root,
            Path(harvest_root_rel) / f"{raw_metadata_path.stem}_harvest.json",
        )
    else:
        output_path = output_path.expanduser().resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(harvest, indent=2) + "\n", encoding="utf-8")

    return {
        "source_manifest_path": str(manifest_path.resolve()),
        "raw_metadata_path": str(raw_metadata_path.resolve()),
        "output_path": str(output_path.resolve()),
        "record_count": harvest["record_count"],
        "skipped_records": skipped_records,
    }


def generate_objaverse_furniture_review_queue_from_harvest(
    spec_path: Path,
    harvest_path: Path,
    policy_path: Path,
    data_root: Path | None = None,
    output_path: Path | None = None,
    contract_path: Path | None = None,
    created_at: str | None = None,
) -> dict:
    spec = load_objaverse_metadata_source_spec(spec_path)
    processed_root = data_root or default_data_root()

    harvest = validate_objaverse_furniture_metadata_harvest(harvest_path)
    resolved_harvest_path = harvest_path.expanduser().resolve()

    if output_path is None:
        output_path = review_queue_output_path_for_harvest(
            spec=spec,
            harvest_path=resolved_harvest_path,
            data_root=processed_root,
        )
    else:
        output_path = output_path.expanduser().resolve()

    summary = write_objaverse_furniture_review_queue(
        harvest_path=resolved_harvest_path,
        policy_path=policy_path,
        output_path=output_path,
        contract_path=contract_path,
        created_at=created_at,
    )
    summary["source_id"] = harvest["source_id"]
    return summary


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
    if len(rel_dirs) == 1:
        slice_root_rel = rel_dirs[0].parent
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


def organize_kenney_opening_selection(
    spec_path: Path,
    selection_path: Path,
    selection_ids: list[str] | None = None,
    raw_data_root: Path | None = None,
    data_root: Path | None = None,
    created_at: str | None = None,
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
    selected_payload = []
    selected_ids = set(selection_ids or [])
    for entry in payload:
        if not isinstance(entry, dict):
            raise TypeError("Selection entries must be objects")
        entry_id = entry.get("selection_id")
        if selected_ids and entry_id not in selected_ids:
            continue
        selected_payload.append(entry)

    if selected_ids:
        found_ids = {entry.get("selection_id") for entry in selected_payload}
        missing_ids = sorted(selected_ids - found_ids)
        if missing_ids:
            raise ValueError(
                f"Opening selection ids not found in {selection_path.as_posix()}: {missing_ids}"
            )

    if not selected_payload:
        raise ValueError(f"No opening selections chosen from {selection_path.as_posix()}")

    manifest_assemblies: list[dict] = []
    rel_dirs: list[Path] = []
    for entry in selected_payload:
        normalized_rel_dir = entry.get("normalized_rel_dir")
        if not isinstance(normalized_rel_dir, str):
            raise ValueError(
                f"Selection entry {entry.get('selection_id')} is missing normalized_rel_dir"
            )
        rel_dir = Path(normalized_rel_dir)
        rel_dirs.append(rel_dir)
        destination = resolve_under(processed_root, rel_dir)
        destination.mkdir(parents=True, exist_ok=True)

        model_src = unpack_dir / _require_entry(entry, "raw_model_rel")
        preview_src = unpack_dir / _require_entry(entry, "raw_preview_rel")
        if not model_src.exists():
            raise FileNotFoundError(f"Missing raw model file: {model_src}")
        if not preview_src.exists():
            raise FileNotFoundError(f"Missing raw preview file: {preview_src}")

        mesh_dst = destination / "model.glb"
        preview_dst = destination / "preview.png"
        shutil.copy2(model_src, mesh_dst)
        shutil.copy2(preview_src, preview_dst)

        source_metadata = {
            "assembly_id": _require_entry(entry, "assembly_id"),
            "opening_type": _require_entry(entry, "opening_type"),
            "source": _require_entry(entry, "source_pack"),
            "license": _require_entry(entry, "license"),
            "source_name": _require_entry(entry, "source_name"),
            "source_url": _require_entry(entry, "source_url"),
            "source_model_path": _require_entry(entry, "raw_model_rel"),
            "source_preview_path": _require_entry(entry, "raw_preview_rel"),
            "normalized_files": {
                "mesh": "model.glb",
                "preview_image": "preview.png",
            },
        }
        with (destination / "source_metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(source_metadata, handle, indent=2)
            handle.write("\n")

        bundle_manifest = {
            "manifest_version": "v0",
            "bundle_id": _require_entry(entry, "assembly_id"),
            "selection_id": _require_entry(entry, "selection_id"),
            "opening_type": _require_entry(entry, "opening_type"),
            "assembly_id": _require_entry(entry, "assembly_id"),
            "display_name": _require_entry(entry, "display_name"),
            "source": _require_entry(entry, "source_pack"),
            "normalized_rel_dir": normalized_rel_dir,
            "created_at": _timestamp(created_at),
            "compatibility": entry["compatibility"],
            "files": {
                "mesh": _file_ref(mesh_dst, processed_root),
                "preview_image": _file_ref(preview_dst, processed_root),
            },
            "upstream": {
                "raw_archive_relpath": spec["raw_archive"]["canonical_relpath"],
            },
        }
        optional_pairs = {
            "style_tags": entry.get("style_tags"),
            "frame_depth_m": entry.get("frame_depth_m"),
            "door_swing": entry.get("door_swing"),
            "glazing": entry.get("glazing"),
            "license": entry.get("license"),
            "source_url": entry.get("source_url"),
        }
        for key, value in optional_pairs.items():
            if value is not None:
                bundle_manifest[key] = value

        with (destination / "bundle_manifest.json").open("w", encoding="utf-8") as handle:
            json.dump(bundle_manifest, handle, indent=2)
            handle.write("\n")

        manifest_assemblies.append(
            {
                "opening_type": entry["opening_type"],
                "assembly_id": entry["assembly_id"],
                "source_name": entry["source_name"],
                "normalized_dir": rel_dir.as_posix(),
            }
        )

    slice_root_rel = Path(os.path.commonpath([path.as_posix() for path in rel_dirs]))
    if len(rel_dirs) == 1:
        slice_root_rel = rel_dirs[0].parent
    slice_root = resolve_under(processed_root, slice_root_rel)
    root_level_assemblies = []
    for entry in manifest_assemblies:
        normalized_dir = Path(entry["normalized_dir"]).relative_to(slice_root_rel)
        root_level_assemblies.append(
            {
                "opening_type": entry["opening_type"],
                "assembly_id": entry["assembly_id"],
                "source_name": entry["source_name"],
                "normalized_dir": normalized_dir.as_posix(),
            }
        )

    selection_manifest = {
        "selection_id": f"{spec['source_id']}_{slice_root_rel.name}",
        "source_pack": spec["source_id"],
        "license": spec["license"],
        "assembly_count": len(root_level_assemblies),
        "assemblies": root_level_assemblies,
    }
    with (slice_root / "selection_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(selection_manifest, handle, indent=2)
        handle.write("\n")

    stale_manifest = resolve_under(processed_root, rel_dirs[0]) / "selection_manifest.json"
    current_manifest = slice_root / "selection_manifest.json"
    if stale_manifest != current_manifest and stale_manifest.exists():
        stale_manifest.unlink()

    return {
        "selection_id": selection_manifest["selection_id"],
        "assembly_count": len(root_level_assemblies),
        "slice_root": str(slice_root),
        "selected_ids": [entry["selection_id"] for entry in selected_payload],
    }


def organize_kenney_ceiling_fixture_selection(
    spec_path: Path,
    selection_path: Path,
    selection_ids: list[str] | None = None,
    raw_data_root: Path | None = None,
    data_root: Path | None = None,
    created_at: str | None = None,
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
    selected_payload = []
    selected_ids = set(selection_ids or [])
    for entry in payload:
        if not isinstance(entry, dict):
            raise TypeError("Selection entries must be objects")
        entry_id = entry.get("selection_id")
        if selected_ids and entry_id not in selected_ids:
            continue
        selected_payload.append(entry)

    if selected_ids:
        found_ids = {entry.get("selection_id") for entry in selected_payload}
        missing_ids = sorted(selected_ids - found_ids)
        if missing_ids:
            raise ValueError(
                f"Ceiling fixture selection ids not found in {selection_path.as_posix()}: {missing_ids}"
            )

    if not selected_payload:
        raise ValueError(f"No ceiling fixture selections chosen from {selection_path.as_posix()}")

    manifest_fixtures: list[dict] = []
    rel_dirs: list[Path] = []
    for entry in selected_payload:
        normalized_rel_dir = entry.get("normalized_rel_dir")
        if not isinstance(normalized_rel_dir, str):
            raise ValueError(
                f"Selection entry {entry.get('selection_id')} is missing normalized_rel_dir"
            )
        rel_dir = Path(normalized_rel_dir)
        rel_dirs.append(rel_dir)
        destination = resolve_under(processed_root, rel_dir)
        destination.mkdir(parents=True, exist_ok=True)

        model_src = unpack_dir / _require_entry(entry, "raw_model_rel")
        preview_src = unpack_dir / _require_entry(entry, "raw_preview_rel")
        if not model_src.exists():
            raise FileNotFoundError(f"Missing raw model file: {model_src}")
        if not preview_src.exists():
            raise FileNotFoundError(f"Missing raw preview file: {preview_src}")

        mesh_dst = destination / "model.glb"
        preview_dst = destination / "preview.png"
        shutil.copy2(model_src, mesh_dst)
        shutil.copy2(preview_src, preview_dst)

        source_metadata = {
            "fixture_id": _require_entry(entry, "fixture_id"),
            "mount_type": _require_entry(entry, "mount_type"),
            "source": _require_entry(entry, "source_pack"),
            "license": _require_entry(entry, "license"),
            "source_name": _require_entry(entry, "source_name"),
            "source_url": _require_entry(entry, "source_url"),
            "source_model_path": _require_entry(entry, "raw_model_rel"),
            "source_preview_path": _require_entry(entry, "raw_preview_rel"),
            "normalized_files": {
                "mesh": "model.glb",
                "preview_image": "preview.png",
            },
        }
        with (destination / "source_metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(source_metadata, handle, indent=2)
            handle.write("\n")

        bundle_manifest = {
            "manifest_version": "v0",
            "bundle_id": _require_entry(entry, "fixture_id"),
            "selection_id": _require_entry(entry, "selection_id"),
            "mount_type": _require_entry(entry, "mount_type"),
            "fixture_id": _require_entry(entry, "fixture_id"),
            "display_name": _require_entry(entry, "display_name"),
            "source": _require_entry(entry, "source_pack"),
            "normalized_rel_dir": normalized_rel_dir,
            "created_at": _timestamp(created_at),
            "dimensions": entry["dimensions"],
            "footprint": entry["footprint"],
            "files": {
                "mesh": _file_ref(mesh_dst, processed_root),
                "preview_image": _file_ref(preview_dst, processed_root),
            },
        }
        optional_pairs = {
            "style_tags": entry.get("style_tags"),
            "nominal_drop_height_m": entry.get("nominal_drop_height_m"),
            "emission_hints": entry.get("emission_hints"),
            "license": entry.get("license"),
            "source_url": entry.get("source_url"),
        }
        for key, value in optional_pairs.items():
            if value is not None:
                bundle_manifest[key] = value

        with (destination / "bundle_manifest.json").open("w", encoding="utf-8") as handle:
            json.dump(bundle_manifest, handle, indent=2)
            handle.write("\n")

        manifest_fixtures.append(
            {
                "mount_type": entry["mount_type"],
                "fixture_id": entry["fixture_id"],
                "source_name": entry["source_name"],
                "normalized_dir": rel_dir.as_posix(),
            }
        )

    slice_root_rel = Path(os.path.commonpath([path.as_posix() for path in rel_dirs]))
    if len(rel_dirs) == 1:
        slice_root_rel = rel_dirs[0].parent
    slice_root = resolve_under(processed_root, slice_root_rel)
    root_level_fixtures = []
    for entry in manifest_fixtures:
        normalized_dir = Path(entry["normalized_dir"]).relative_to(slice_root_rel)
        root_level_fixtures.append(
            {
                "mount_type": entry["mount_type"],
                "fixture_id": entry["fixture_id"],
                "source_name": entry["source_name"],
                "normalized_dir": normalized_dir.as_posix(),
            }
        )

    selection_manifest = {
        "selection_id": f"{spec['source_id']}_{slice_root_rel.name}",
        "source_pack": spec["source_id"],
        "license": spec["license"],
        "fixture_count": len(root_level_fixtures),
        "fixtures": root_level_fixtures,
    }
    with (slice_root / "selection_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(selection_manifest, handle, indent=2)
        handle.write("\n")

    stale_manifest = resolve_under(processed_root, rel_dirs[0]) / "selection_manifest.json"
    current_manifest = slice_root / "selection_manifest.json"
    if stale_manifest != current_manifest and stale_manifest.exists():
        stale_manifest.unlink()

    return {
        "selection_id": selection_manifest["selection_id"],
        "fixture_count": len(root_level_fixtures),
        "slice_root": str(slice_root),
        "selected_ids": [entry["selection_id"] for entry in selected_payload],
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
