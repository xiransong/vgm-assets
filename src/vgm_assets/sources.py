from __future__ import annotations

import hashlib
import gzip
from importlib.metadata import PackageNotFoundError, version
import json
import os
import subprocess
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .catalog import load_asset_specs, validate_asset_catalog
from .objaverse import (
    review_queue_output_path_for_harvest,
    validate_objaverse_furniture_metadata_harvest,
    validate_objaverse_furniture_metadata_harvest_data,
    validate_objaverse_selective_geometry_manifest,
    write_objaverse_furniture_review_queue,
)
from .paths import default_data_root, default_raw_data_root, resolve_under
from .protocol import load_json, repo_root


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


def _git_commit_or_none(repo_dir: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    commit = result.stdout.strip()
    return commit or None


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
    items = [item.strip() for item in value if isinstance(item, str) and item.strip()]
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


def _archive_stem(path: Path) -> str:
    name = path.name
    for suffix in (".json.gz", ".jsonl.gz", ".jsonl", ".json", ".parquet"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def load_selection_list(selection_path: Path) -> list[dict]:
    payload = load_json(selection_path)
    if not isinstance(payload, list):
        raise TypeError(f"Selection list at {selection_path} must be a JSON array")
    normalized: list[dict] = []
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            raise TypeError(
                f"Selection list at {selection_path} contains a non-object entry at index {index}"
            )
        normalized.append(entry)
    return normalized


def _require_entry(entry: dict, key: str):
    if key not in entry:
        raise ValueError(f"Selection entry {entry.get('selection_id')} is missing '{key}'")
    return entry[key]


def _normalize_objaverse_license(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    mapping = {
        "cc0": "CC0",
        "by": "CC-BY 4.0",
        "by-sa": "CC-BY-SA",
        "by-nc": "CC-BY-NC",
        "by-nc-sa": "CC-BY-NC-SA",
    }
    if normalized in mapping:
        return mapping[normalized]
    if normalized:
        return value.strip()
    return None


def _extract_objaverse_thumbnail_url(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if not isinstance(value, dict):
        return None
    images = value.get("images")
    if not isinstance(images, list):
        return None
    best_url = None
    best_area = -1
    for image in images:
        if not isinstance(image, dict):
            continue
        url = image.get("url")
        width = image.get("width")
        height = image.get("height")
        if not isinstance(url, str) or not url.strip():
            continue
        if isinstance(width, int) and isinstance(height, int):
            area = width * height
        else:
            area = 0
        if area >= best_area:
            best_area = area
            best_url = url.strip()
    return best_url


def _extract_objaverse_archives(value: object) -> list[str] | None:
    if isinstance(value, dict):
        formats = [str(key).strip() for key in value.keys() if str(key).strip()]
        return formats or None
    return None


def _first_value(entry: dict, keys: list[str]) -> object:
    for key in keys:
        if key in entry:
            return entry[key]
    return None


def _normalize_objaverse_metadata_record(entry: dict) -> dict | None:
    object_uid = _first_value(entry, ["object_uid", "uid", "id"])
    source_url = _first_value(entry, ["source_url", "viewerUrl", "url", "uri"])
    title = _first_value(entry, ["title", "name"])
    license_value = _normalize_objaverse_license(
        _first_value(entry, ["license", "license_name", "license_label"])
    )

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

    if "source_tags" not in normalized:
        tags = entry.get("tags")
        if isinstance(tags, list):
            tag_names = []
            for item in tags:
                if isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str) and name.strip():
                        tag_names.append(name.strip())
            if tag_names:
                normalized["source_tags"] = tag_names

    if "source_categories" not in normalized:
        categories = entry.get("categories")
        if isinstance(categories, list):
            category_names = []
            for item in categories:
                if isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str) and name.strip():
                        category_names.append(name.strip())
                elif isinstance(item, str) and item.strip():
                    category_names.append(item.strip())
            if category_names:
                normalized["source_categories"] = category_names

    if "available_formats" not in normalized:
        archive_formats = _extract_objaverse_archives(entry.get("archives"))
        if archive_formats is not None:
            normalized["available_formats"] = archive_formats

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

    if "thumbnail_url" not in normalized:
        thumbnail_url = _extract_objaverse_thumbnail_url(entry.get("thumbnails"))
        if thumbnail_url is not None:
            normalized["thumbnail_url"] = thumbnail_url

    triangle_count = _coerce_nonnegative_int(_first_value(entry, ["triangle_count", "triangles"]))
    if triangle_count is None:
        triangle_count = _coerce_nonnegative_int(_first_value(entry, ["faceCount"]))
    if triangle_count is not None:
        normalized["triangle_count"] = triangle_count

    vertex_count = _coerce_nonnegative_int(_first_value(entry, ["vertex_count", "vertices"]))
    if vertex_count is None:
        vertex_count = _coerce_nonnegative_int(_first_value(entry, ["vertexCount"]))
    if vertex_count is not None:
        normalized["vertex_count"] = vertex_count

    bounds = _coerce_bounds(_first_value(entry, ["bounds"]))
    if bounds is not None:
        normalized["bounds"] = bounds

    return normalized


def _load_objaverse_metadata_records(raw_path: Path) -> list[dict]:
    suffix = raw_path.suffix.lower()
    name = raw_path.name.lower()
    if name.endswith(".jsonl.gz"):
        records: list[dict] = []
        with gzip.open(raw_path, "rt", encoding="utf-8") as handle:
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

    if name.endswith(".json.gz"):
        with gzip.open(raw_path, "rt", encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        payload = load_json(raw_path)
    if isinstance(payload, dict) and "records" in payload:
        records = payload["records"]
        if not isinstance(records, list):
            raise TypeError(f"'records' in {raw_path} must be a JSON array")
        if any(not isinstance(record, dict) for record in records):
            raise TypeError(f"All records in {raw_path} must be JSON objects")
        return records

    if isinstance(payload, dict):
        if all(isinstance(value, dict) for value in payload.values()):
            return list(payload.values())

    if isinstance(payload, list):
        if any(not isinstance(record, dict) for record in payload):
            raise TypeError(f"All records in {raw_path} must be JSON objects")
        return payload

    if isinstance(payload, dict):
        return [payload]

    raise TypeError(f"Unsupported Objaverse metadata payload shape in {raw_path}")

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
        filename_lower = raw_file.name.lower()
        if not any(filename_lower.endswith(extension) for extension in allowed):
            raise ValueError(
                f"Unsupported Objaverse metadata file extension for {raw_file}. "
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
            Path(harvest_root_rel) / f"{_archive_stem(raw_metadata_path)}_harvest.json",
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


def _objaverse_package_version() -> str:
    try:
        return version("objaverse")
    except PackageNotFoundError:
        return "unknown"


def download_objaverse_selective_geometry(
    manifest_path: Path,
    raw_data_root: Path | None = None,
    *,
    download_processes: int = 2,
    download_previews: bool = False,
    acquired_at: str | None = None,
    acquired_by: str | None = None,
    notes: str | None = None,
    user_agent: str | None = None,
) -> dict:
    manifest = validate_objaverse_selective_geometry_manifest(manifest_path)
    raw_root = raw_data_root or default_raw_data_root()

    try:
        import objaverse  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "The 'objaverse' Python package is required for geometry download. "
            "Install it in the vgm-assets environment first."
        ) from exc

    candidates = sorted(
        manifest.get("candidates", []),
        key=lambda candidate: (candidate.get("priority", 10**9), candidate.get("object_uid", "")),
    )
    uids = [candidate["object_uid"] for candidate in candidates]
    downloaded_paths = objaverse.load_objects(
        uids=uids,
        download_processes=download_processes,
    )
    if not isinstance(downloaded_paths, dict):
        raise TypeError("objaverse.load_objects(...) must return a uid-to-path mapping")

    acquisition_root = resolve_under(raw_root, manifest["raw_acquisition_root_rel"])
    acquisition_root.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    ua = user_agent or "vgm-assets/0.1 (research prototype; contact=local)"
    acquired_timestamp = _timestamp(acquired_at)
    acquired_user = acquired_by or os.environ.get("USER", "unknown")

    for candidate in candidates:
        object_uid = candidate["object_uid"]
        raw_candidate_dir = resolve_under(raw_root, candidate["raw_candidate_rel_dir"])
        raw_candidate_dir.mkdir(parents=True, exist_ok=True)

        downloaded_path_value = downloaded_paths.get(object_uid)
        if not isinstance(downloaded_path_value, str) or not downloaded_path_value:
            results.append(
                {
                    "object_uid": object_uid,
                    "status": "missing_download",
                    "raw_candidate_rel_dir": candidate["raw_candidate_rel_dir"],
                }
            )
            continue

        downloaded_path = Path(downloaded_path_value).expanduser().resolve()
        if not downloaded_path.exists():
            results.append(
                {
                    "object_uid": object_uid,
                    "status": "missing_download",
                    "downloaded_path": str(downloaded_path),
                    "raw_candidate_rel_dir": candidate["raw_candidate_rel_dir"],
                }
            )
            continue

        suffix = downloaded_path.suffix or ".glb"
        model_filename = f"model{suffix}"
        model_destination = raw_candidate_dir / model_filename
        if downloaded_path != model_destination:
            shutil.copy2(downloaded_path, model_destination)

        files_manifest = [
            {
                "logical_name": "mesh",
                "filename": model_filename,
                "raw_relpath": (
                    Path(candidate["raw_candidate_rel_dir"]) / model_filename
                ).as_posix(),
                "sha256": _sha256(model_destination),
                "size_bytes": model_destination.stat().st_size,
            }
        ]

        preview_url = candidate.get("thumbnail_url")
        if download_previews and isinstance(preview_url, str) and preview_url:
            preview_suffix = Path(urlparse(preview_url).path).suffix or ".jpg"
            preview_filename = f"preview{preview_suffix}"
            preview_destination = raw_candidate_dir / preview_filename
            _download_url(preview_url, preview_destination, ua)
            files_manifest.append(
                {
                    "logical_name": "preview_image",
                    "filename": preview_filename,
                    "raw_relpath": (
                        Path(candidate["raw_candidate_rel_dir"]) / preview_filename
                    ).as_posix(),
                    "sha256": _sha256(preview_destination),
                    "size_bytes": preview_destination.stat().st_size,
                }
            )

        source_manifest = {
            "manifest_version": "v0",
            "source_id": manifest["source_id"],
            "selection_id": manifest["selection_id"],
            "review_id": manifest["review_id"],
            "object_uid": object_uid,
            "title": candidate["title"],
            "category_guess": candidate["category_guess"],
            "priority": candidate["priority"],
            "license": candidate["license"],
            "source_url": candidate["source_url"],
            "available_formats": candidate.get("available_formats", []),
            "preferred_download_order": candidate.get("preferred_download_order", []),
            "raw_candidate_rel_dir": candidate["raw_candidate_rel_dir"],
            "acquisition_method": "objaverse_python_api",
            "downloaded_filename": model_filename,
            "downloaded_format": model_destination.suffix.lstrip(".") or "bin",
            "downloaded_at": acquired_timestamp,
            "downloaded_by": acquired_user,
            "objaverse_package_version": _objaverse_package_version(),
            "upstream": {
                "selection_manifest_relpath": manifest_path.relative_to(repo_root()).as_posix()
                if manifest_path.is_relative_to(repo_root())
                else str(manifest_path),
                "harvest_artifact": manifest["harvest_artifact"],
                "queue_artifact": manifest["queue_artifact"],
            },
            "files": files_manifest,
            "notes": notes or candidate.get("notes", ""),
        }
        source_manifest_path = raw_candidate_dir / "source_manifest.json"
        source_manifest_path.write_text(
            json.dumps(source_manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        results.append(
            {
                "object_uid": object_uid,
                "status": "downloaded",
                "raw_candidate_rel_dir": candidate["raw_candidate_rel_dir"],
                "source_manifest_relpath": (
                    Path(candidate["raw_candidate_rel_dir"]) / "source_manifest.json"
                ).as_posix(),
            }
        )

    batch_manifest = {
        "manifest_version": "v0",
        "selection_id": manifest["selection_id"],
        "source_id": manifest["source_id"],
        "review_id": manifest["review_id"],
        "created_at": acquired_timestamp,
        "raw_data_root_env_var": manifest["raw_data_root_env_var"],
        "raw_acquisition_root_rel": manifest["raw_acquisition_root_rel"],
        "candidate_count": manifest["candidate_count"],
        "results": results,
        "notes": notes or "",
    }
    batch_manifest_path = acquisition_root / f"{manifest['selection_id']}_download_manifest.json"
    batch_manifest_path.write_text(json.dumps(batch_manifest, indent=2) + "\n", encoding="utf-8")

    downloaded_count = sum(1 for result in results if result["status"] == "downloaded")
    missing_count = sum(1 for result in results if result["status"] == "missing_download")

    return {
        "selection_id": manifest["selection_id"],
        "manifest_path": str(manifest_path.resolve()),
        "raw_root": str(raw_root.resolve()),
        "batch_manifest_path": str(batch_manifest_path.resolve()),
        "requested_count": len(candidates),
        "downloaded_count": downloaded_count,
        "missing_count": missing_count,
    }


def _load_objaverse_normalization_plan(plan_path: Path) -> dict:
    payload = load_json(plan_path)
    if not isinstance(payload, dict):
        raise TypeError(f"Objaverse normalization plan at {plan_path} must be a JSON object")
    required = [
        "plan_id",
        "selection_id",
        "source_id",
        "config_id",
        "normalized_root_rel",
        "reference_catalog_path",
        "candidate_count",
        "candidates",
    ]
    for key in required:
        if key not in payload:
            raise ValueError(f"Objaverse normalization plan at {plan_path} is missing '{key}'")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError(f"Objaverse normalization plan at {plan_path} must define non-empty 'candidates'")
    return payload


def _scaled_support_surface(surface: dict, sx: float, sy: float, sz: float) -> dict:
    updated = dict(surface)
    if "height" in updated:
        updated["height"] = round(float(updated["height"]) * sy, 3)
    if "width" in updated:
        updated["width"] = round(float(updated["width"]) * sx, 3)
    if "depth" in updated:
        updated["depth"] = round(float(updated["depth"]) * sz, 3)
    return updated


def _scaled_template_asset(template_asset: dict, *, width: float, depth: float, height: float) -> dict:
    scaled = json.loads(json.dumps(template_asset))
    old_dims = template_asset["dimensions"]
    sx = width / float(old_dims["width"])
    sy = height / float(old_dims["height"])
    sz = depth / float(old_dims["depth"])

    scaled["dimensions"] = {
        "width": round(width, 3),
        "depth": round(depth, 3),
        "height": round(height, 3),
    }

    footprint = scaled.get("footprint")
    if isinstance(footprint, dict):
        shape = footprint.get("shape", "rectangle")
        if shape == "circle":
            diameter = round(max(width, depth), 3)
            scaled["footprint"] = {
                "shape": "circle",
                "width": diameter,
                "depth": diameter,
            }
        else:
            scaled["footprint"] = {
                "shape": shape,
                "width": round(width, 3),
                "depth": round(depth, 3),
            }

    support = scaled.get("support")
    if isinstance(support, dict):
        surfaces = support.get("support_surfaces")
        if isinstance(surfaces, list):
            support["support_surfaces"] = [
                _scaled_support_surface(surface, sx, sy, sz) for surface in surfaces
            ]

    return scaled


def normalize_objaverse_furniture_selection(
    plan_path: Path,
    *,
    raw_data_root: Path | None = None,
    data_root: Path | None = None,
    created_at: str | None = None,
) -> dict:
    plan = _load_objaverse_normalization_plan(plan_path)
    raw_root = raw_data_root or default_raw_data_root()
    processed_root = data_root or default_data_root()

    reference_catalog_path = repo_root() / plan["reference_catalog_path"]
    reference_assets = load_asset_specs(reference_catalog_path)
    template_by_id = {}
    for record in reference_assets:
        asset_id = record.get("asset_id")
        if isinstance(asset_id, str):
            template_by_id[asset_id] = record

    import trimesh  # type: ignore

    normalized_root_rel = Path(plan["normalized_root_rel"])
    slice_root = resolve_under(processed_root, normalized_root_rel)
    slice_root.mkdir(parents=True, exist_ok=True)

    manifest_assets: list[dict] = []
    bundle_manifest_paths: list[str] = []
    for candidate in plan["candidates"]:
        if not isinstance(candidate, dict):
            raise TypeError("Objaverse normalization plan candidates must be objects")
        object_uid = _require_entry(candidate, "object_uid")
        asset_id = _require_entry(candidate, "asset_id")
        category = _require_entry(candidate, "category")
        title = _require_entry(candidate, "title")
        template_asset_id = _require_entry(candidate, "template_asset_id")
        scale = float(candidate["uniform_scale"])
        sample_weight = float(candidate.get("sample_weight", 1.0))

        template_asset = template_by_id.get(template_asset_id)
        if template_asset is None:
            raise ValueError(
                f"Template asset '{template_asset_id}' not found in {reference_catalog_path}"
            )

        raw_candidate_dir = resolve_under(
            raw_root, Path("sources") / "objaverse" / "furniture_v0" / "geometry" / object_uid / "raw"
        )
        source_manifest_path = raw_candidate_dir / "source_manifest.json"
        if not source_manifest_path.exists():
            raise FileNotFoundError(f"Missing Objaverse raw source manifest: {source_manifest_path}")
        source_manifest = load_json(source_manifest_path)
        if not isinstance(source_manifest, dict):
            raise TypeError(f"Objaverse source manifest at {source_manifest_path} must be an object")

        mesh_files = [
            entry
            for entry in source_manifest.get("files", [])
            if isinstance(entry, dict) and entry.get("logical_name") == "mesh"
        ]
        if not mesh_files:
            raise FileNotFoundError(
                f"Objaverse source manifest at {source_manifest_path} has no mesh file"
            )
        mesh_filename = mesh_files[0]["filename"]
        raw_mesh_path = raw_candidate_dir / mesh_filename
        if not raw_mesh_path.exists():
            raise FileNotFoundError(f"Missing Objaverse raw mesh: {raw_mesh_path}")

        destination_rel_dir = normalized_root_rel / category / asset_id
        destination_dir = resolve_under(processed_root, destination_rel_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)

        scene = trimesh.load(raw_mesh_path, force="scene")
        scene.apply_scale(scale)
        mesh_dst = destination_dir / "model.glb"
        scene.export(mesh_dst)

        preview_dst = None
        preview_files = [
            entry
            for entry in source_manifest.get("files", [])
            if isinstance(entry, dict) and entry.get("logical_name") == "preview_image"
        ]
        if preview_files:
            preview_filename = preview_files[0]["filename"]
            raw_preview_path = raw_candidate_dir / preview_filename
            if raw_preview_path.exists():
                preview_dst = destination_dir / f"preview{raw_preview_path.suffix or '.png'}"
                shutil.copy2(raw_preview_path, preview_dst)

        bounds = scene.bounds
        if bounds is None:
            raise ValueError(f"Could not compute bounds for scaled Objaverse mesh {raw_mesh_path}")
        extents = bounds[1] - bounds[0]
        width = round(float(extents[0]), 3)
        height = round(float(extents[1]), 3)
        depth = round(float(extents[2]), 3)

        normalized_asset = _scaled_template_asset(
            template_asset,
            width=width,
            depth=depth,
            height=height,
        )

        source_metadata = {
            "asset_id": asset_id,
            "object_uid": object_uid,
            "title": title,
            "category": category,
            "source": "objaverse",
            "license": source_manifest.get("license", ""),
            "source_url": source_manifest.get("source_url", ""),
            "template_asset_id": template_asset_id,
            "uniform_scale": scale,
            "normalized_files": {
                "mesh": "model.glb",
            },
            "upstream": {
                "raw_source_manifest_relpath": source_manifest_path.relative_to(raw_root).as_posix()
            },
        }
        if preview_dst is not None:
            source_metadata["normalized_files"]["preview_image"] = preview_dst.name

        (destination_dir / "source_metadata.json").write_text(
            json.dumps(source_metadata, indent=2) + "\n",
            encoding="utf-8",
        )

        bundle_manifest = {
            "manifest_version": "v0",
            "bundle_id": asset_id,
            "selection_id": plan["selection_id"],
            "asset_id": asset_id,
            "category": category,
            "source": "objaverse",
            "sample_weight": sample_weight,
            "dimensions": normalized_asset["dimensions"],
            "footprint": normalized_asset.get("footprint"),
            "placement": normalized_asset["placement"],
            "walkability": normalized_asset["walkability"],
            "semantics": normalized_asset["semantics"],
            "support": normalized_asset["support"],
            "normalized_rel_dir": destination_rel_dir.as_posix(),
            "created_at": _timestamp(created_at),
            "config_id": plan["config_id"],
            "files": {
                "mesh": _file_ref(mesh_dst, processed_root),
            },
            "source_url": source_manifest.get("source_url", ""),
            "license": source_manifest.get("license", ""),
            "object_uid": object_uid,
            "template_asset_id": template_asset_id,
            "title": title,
            "notes": candidate.get("notes", ""),
        }
        if preview_dst is not None:
            bundle_manifest["files"]["preview_image"] = _file_ref(preview_dst, processed_root)

        bundle_manifest_path = destination_dir / "bundle_manifest.json"
        bundle_manifest_path.write_text(
            json.dumps(bundle_manifest, indent=2) + "\n",
            encoding="utf-8",
        )

        manifest_assets.append(
            {
                "asset_id": asset_id,
                "category": category,
                "title": title,
                "normalized_dir": (Path(category) / asset_id).as_posix(),
            }
        )
        bundle_manifest_paths.append((destination_rel_dir / "bundle_manifest.json").as_posix())

    selection_manifest = {
        "selection_id": plan["selection_id"],
        "source_id": plan["source_id"],
        "config_id": plan["config_id"],
        "asset_count": len(manifest_assets),
        "assets": manifest_assets,
        "bundle_manifest_paths": bundle_manifest_paths,
    }
    (slice_root / "selection_manifest.json").write_text(
        json.dumps(selection_manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "selection_id": plan["selection_id"],
        "slice_root": str(slice_root.resolve()),
        "asset_count": len(manifest_assets),
        "bundle_manifest_paths": [
            str(resolve_under(processed_root, path).resolve()) for path in bundle_manifest_paths
        ],
    }


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


def _default_ai2thor_repo_root() -> Path:
    override = os.environ.get("VGM_AI2THOR_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return repo_root().parents[2] / "ai2thor"


def _select_entries(
    payload: list[dict],
    *,
    selection_ids: list[str] | None,
    label: str,
    selection_path: Path,
) -> list[dict]:
    selected_payload = []
    selected_ids = set(selection_ids or [])
    for entry in payload:
        entry_id = entry.get("selection_id")
        if selected_ids and entry_id not in selected_ids:
            continue
        selected_payload.append(entry)

    if selected_ids:
        found_ids = {entry.get("selection_id") for entry in selected_payload}
        missing_ids = sorted(selected_ids - found_ids)
        if missing_ids:
            raise ValueError(
                f"{label} selection ids not found in {selection_path.as_posix()}: {missing_ids}"
            )

    if not selected_payload:
        raise ValueError(f"No {label} selections chosen from {selection_path.as_posix()}")

    return selected_payload


def _copy_tree_without_meta(source_dir: Path, destination_dir: Path) -> list[str]:
    copied: list[str] = []
    for path in sorted(source_dir.rglob("*")):
        if path.is_dir():
            if path.name.startswith("."):
                continue
            continue
        if path.name.endswith(".meta"):
            continue
        if any(part.startswith(".") for part in path.relative_to(source_dir).parts):
            continue
        relative = path.relative_to(source_dir)
        target = destination_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(relative.as_posix())
    return copied


def register_ai2thor_support_clutter_selection(
    selection_path: Path,
    *,
    source_repo_root: Path | None = None,
    selection_ids: list[str] | None = None,
    raw_data_root: Path | None = None,
    acquired_by: str | None = None,
    acquired_at: str | None = None,
    notes: str | None = None,
) -> dict:
    source_root = (source_repo_root or _default_ai2thor_repo_root()).resolve()
    raw_root = raw_data_root or default_raw_data_root()
    payload = load_selection_list(selection_path)
    selected_payload = _select_entries(
        payload,
        selection_ids=selection_ids,
        label="AI2-THOR support clutter",
        selection_path=selection_path,
    )

    source_commit = _git_commit_or_none(source_root)
    slice_root_rel = Path("sources") / "ai2thor" / "support_clutter_v0"
    slice_root = resolve_under(raw_root, slice_root_rel)
    slice_root.mkdir(parents=True, exist_ok=True)

    manifest_assets = []
    for entry in selected_payload:
        category = str(_require_entry(entry, "category"))
        asset_id = str(_require_entry(entry, "asset_id"))
        source_repo_rel_root = Path(str(_require_entry(entry, "source_repo_rel_root")))
        source_dir = source_root / source_repo_rel_root
        prefab_src = source_root / source_repo_rel_root / str(_require_entry(entry, "raw_prefab_rel"))
        model_src = source_root / source_repo_rel_root / str(_require_entry(entry, "raw_model_rel"))
        materials_src = source_root / source_repo_rel_root / str(_require_entry(entry, "raw_material_dir_rel"))
        if not source_dir.exists():
            raise FileNotFoundError(f"Missing AI2-THOR source directory: {source_dir}")
        if not prefab_src.exists():
            raise FileNotFoundError(f"Missing AI2-THOR prefab file: {prefab_src}")
        if not model_src.exists():
            raise FileNotFoundError(f"Missing AI2-THOR model file: {model_src}")
        if not materials_src.exists() or not materials_src.is_dir():
            raise FileNotFoundError(f"Missing AI2-THOR materials directory: {materials_src}")

        raw_dir_rel = slice_root_rel / category / asset_id / "raw"
        raw_dir = resolve_under(raw_root, raw_dir_rel)
        raw_dir.mkdir(parents=True, exist_ok=True)

        prefab_dst = raw_dir / "source_prefab.prefab"
        model_dst = raw_dir / "source_model.fbx"
        materials_dst = raw_dir / "materials"
        shutil.copy2(prefab_src, prefab_dst)
        shutil.copy2(model_src, model_dst)
        copied_materials = _copy_tree_without_meta(materials_src, materials_dst)

        source_manifest = {
            "selection_id": _require_entry(entry, "selection_id"),
            "asset_id": asset_id,
            "category": category,
            "source_repo": str(_require_entry(entry, "source_repo")),
            "source_repo_root": str(source_root),
            "source_commit": source_commit,
            "source_url": _require_entry(entry, "source_url"),
            "source_repo_rel_root": source_repo_rel_root.as_posix(),
            "source_name": _require_entry(entry, "source_name"),
            "license": _require_entry(entry, "license"),
            "registered_at": _timestamp(acquired_at),
            "acquired_by": acquired_by or "unknown",
            "notes": notes or entry.get("notes"),
            "raw_files": {
                "prefab": _file_ref(prefab_dst, raw_root),
                "model": _file_ref(model_dst, raw_root),
            },
            "raw_material_files": copied_materials,
        }
        with (raw_dir / "source_manifest.json").open("w", encoding="utf-8") as handle:
            json.dump(source_manifest, handle, indent=2)
            handle.write("\n")

        manifest_assets.append(
            {
                "category": category,
                "asset_id": asset_id,
                "selection_id": entry["selection_id"],
                "source_name": entry["source_name"],
                "raw_dir": raw_dir_rel.relative_to(slice_root_rel).as_posix(),
            }
        )

    selection_manifest = {
        "selection_id": "ai2thor_support_clutter_v0",
        "source_pack": "ai2thor",
        "source_repo_root": str(source_root),
        "source_commit": source_commit,
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
        "selected_ids": [entry["selection_id"] for entry in selected_payload],
    }


def normalize_ai2thor_support_clutter_selection(
    selection_path: Path,
    *,
    selection_ids: list[str] | None = None,
    raw_data_root: Path | None = None,
    data_root: Path | None = None,
    created_at: str | None = None,
) -> dict:
    raw_root = raw_data_root or default_raw_data_root()
    processed_root = data_root or default_data_root()
    payload = load_selection_list(selection_path)
    selected_payload = _select_entries(
        payload,
        selection_ids=selection_ids,
        label="AI2-THOR support clutter",
        selection_path=selection_path,
    )

    slice_root_rel = Path("sources") / "ai2thor" / "support_clutter_v0"
    raw_slice_root = resolve_under(raw_root, slice_root_rel)
    if not raw_slice_root.exists():
        raise FileNotFoundError(
            f"Missing registered AI2-THOR raw slice at {raw_slice_root}; run register-ai2thor-support-clutter-selection first"
        )

    manifest_assets = []
    rel_dirs: list[Path] = []
    for entry in selected_payload:
        category = str(_require_entry(entry, "category"))
        asset_id = str(_require_entry(entry, "asset_id"))
        raw_dir_rel = slice_root_rel / category / asset_id / "raw"
        raw_dir = resolve_under(raw_root, raw_dir_rel)
        prefab_src = raw_dir / "source_prefab.prefab"
        model_src = raw_dir / "source_model.fbx"
        materials_src = raw_dir / "materials"
        if not prefab_src.exists() or not model_src.exists():
            raise FileNotFoundError(
                f"Missing registered AI2-THOR raw payloads for {asset_id} under {raw_dir}"
            )

        normalized_rel_dir = Path(str(_require_entry(entry, "normalized_rel_dir")))
        rel_dirs.append(normalized_rel_dir)
        destination = resolve_under(processed_root, normalized_rel_dir)
        destination.mkdir(parents=True, exist_ok=True)

        model_dst = destination / "model.fbx"
        shutil.copy2(model_src, model_dst)

        copied_materials: list[str] = []
        if materials_src.exists():
            copied_materials = _copy_tree_without_meta(materials_src, destination / "materials")

        source_manifest_path = raw_dir / "source_manifest.json"
        source_manifest = load_json(source_manifest_path) if source_manifest_path.exists() else {}

        source_metadata = {
            "asset_id": asset_id,
            "category": category,
            "source": "ai2thor",
            "license": _require_entry(entry, "license"),
            "source_name": _require_entry(entry, "source_name"),
            "source_repo": _require_entry(entry, "source_repo"),
            "source_repo_rel_root": _require_entry(entry, "source_repo_rel_root"),
            "source_url": _require_entry(entry, "source_url"),
            "source_prefab_path": str(_require_entry(entry, "raw_prefab_rel")),
            "source_model_path": str(_require_entry(entry, "raw_model_rel")),
            "normalized_files": {
                "mesh": "model.fbx",
            },
        }
        if copied_materials:
            source_metadata["normalized_material_files"] = copied_materials
        if isinstance(source_manifest, dict):
            if "source_commit" in source_manifest:
                source_metadata["source_commit"] = source_manifest["source_commit"]
            if "selection_id" in source_manifest:
                source_metadata["selection_id"] = source_manifest["selection_id"]

        with (destination / "source_metadata.json").open("w", encoding="utf-8") as handle:
            json.dump(source_metadata, handle, indent=2)
            handle.write("\n")

        bundle_manifest = {
            "manifest_version": "v0",
            "bundle_id": asset_id,
            "selection_id": _require_entry(entry, "selection_id"),
            "asset_id": asset_id,
            "category": category,
            "display_name": _require_entry(entry, "display_name"),
            "source": "ai2thor",
            "normalized_rel_dir": normalized_rel_dir.as_posix(),
            "created_at": _timestamp(created_at),
            "files": {
                "mesh": _file_ref(model_dst, processed_root),
            },
            "upstream": {
                "raw_dir_relpath": raw_dir_rel.as_posix(),
            },
        }
        optional_pairs = {
            "style_tags": entry.get("style_tags"),
            "license": entry.get("license"),
            "source_url": entry.get("source_url"),
        }
        for key, value in optional_pairs.items():
            if value is not None:
                bundle_manifest[key] = value
        if copied_materials:
            bundle_manifest["materials_rel_dir"] = "materials"
            bundle_manifest["material_files"] = copied_materials

        with (destination / "bundle_manifest.json").open("w", encoding="utf-8") as handle:
            json.dump(bundle_manifest, handle, indent=2)
            handle.write("\n")

        manifest_assets.append(
            {
                "category": category,
                "asset_id": asset_id,
                "selection_id": entry["selection_id"],
                "source_name": entry["source_name"],
                "normalized_dir": normalized_rel_dir.as_posix(),
            }
        )

    slice_root_rel = Path(os.path.commonpath([path.as_posix() for path in rel_dirs]))
    if len(rel_dirs) == 1:
        slice_root_rel = rel_dirs[0].parent
    slice_root = resolve_under(processed_root, slice_root_rel)
    root_level_assets = []
    for entry in manifest_assets:
        normalized_dir = Path(entry["normalized_dir"]).relative_to(slice_root_rel)
        root_level_assets.append(
            {
                "category": entry["category"],
                "asset_id": entry["asset_id"],
                "selection_id": entry["selection_id"],
                "source_name": entry["source_name"],
                "normalized_dir": normalized_dir.as_posix(),
            }
        )

    selection_manifest = {
        "selection_id": "ai2thor_support_clutter_v0",
        "source_pack": "ai2thor",
        "asset_count": len(root_level_assets),
        "assets": root_level_assets,
    }
    with (slice_root / "selection_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(selection_manifest, handle, indent=2)
        handle.write("\n")

    return {
        "selection_id": selection_manifest["selection_id"],
        "asset_count": len(root_level_assets),
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
