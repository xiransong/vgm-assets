from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema.validators import validator_for

from .paths import default_raw_data_root, resolve_under
from .protocol import load_json

SUPPORT_CLUTTER_PROP_ANNOTATION_SET_SCHEMA = (
    Path("schemas") / "local" / "support_clutter_prop_annotation_set_v0.schema.json"
)
AI2THOR_SUPPORT_CLUTTER_SLICE_ROOT = Path("sources") / "ai2thor" / "support_clutter_v0"

_DOC_HEADER_RE = re.compile(r"^--- !u!(?P<type_id>\d+) &(?P<file_id>\d+)$")
_FILE_ID_RE = re.compile(r"^\s*m_GameObject:\s+\{fileID:\s*(?P<file_id>-?\d+)\}\s*$")
_SCALAR_RE = re.compile(r"^\s*(?P<key>[A-Za-z0-9_]+):\s*(?P<value>.+?)\s*$")
_VECTOR3_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z0-9_]+):\s+\{x:\s*(?P<x>[^,]+),\s*y:\s*(?P<y>[^,]+),\s*z:\s*(?P<z>[^}]+)\}\s*$"
)


def _timestamp(value: str | None = None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _vector_dict(x: float, y: float, z: float) -> dict[str, float]:
    return {"x": round(x, 6), "y": round(y, 6), "z": round(z, 6)}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def support_clutter_prop_annotation_set_schema_path() -> Path:
    return repo_root() / SUPPORT_CLUTTER_PROP_ANNOTATION_SET_SCHEMA


def load_support_clutter_prop_annotation_set(path: Path) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise TypeError(f"Support-clutter prop annotation set at {path} must be a JSON object")
    return payload


def validate_support_clutter_prop_annotation_set_data(payload: object) -> dict:
    schema = load_json(support_clutter_prop_annotation_set_schema_path())
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, dict):
        raise TypeError("Support-clutter prop annotation payload must be an object after validation")
    return payload


def validate_support_clutter_prop_annotation_set(path: Path) -> dict:
    return validate_support_clutter_prop_annotation_set_data(
        load_support_clutter_prop_annotation_set(path)
    )


def _parse_scalar(lines: list[str], key: str) -> str | None:
    prefix = f"{key}:"
    for line in lines:
        if not line.lstrip().startswith(prefix):
            continue
        return line.split(":", 1)[1].strip()
    return None


def _parse_vector3(lines: list[str], key: str) -> tuple[float, float, float] | None:
    prefix = f"{key}:"
    for line in lines:
        if not line.lstrip().startswith(prefix):
            continue
        match = _VECTOR3_RE.match(line)
        if match is None:
            raise ValueError(f"Malformed vector3 line for {key}: {line}")
        return (
            float(match.group("x")),
            float(match.group("y")),
            float(match.group("z")),
        )
    return None


def _parse_game_object_file_id(lines: list[str]) -> str | None:
    for line in lines:
        match = _FILE_ID_RE.match(line)
        if match is not None:
            return match.group("file_id")
    return None


def _parse_unity_prefab_documents(prefab_path: Path) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in prefab_path.read_text(encoding="utf-8").splitlines():
        header_match = _DOC_HEADER_RE.match(raw_line)
        if header_match is not None:
            if current is not None:
                documents.append(current)
            current = {
                "type_id": int(header_match.group("type_id")),
                "file_id": header_match.group("file_id"),
                "lines": [],
            }
            continue
        if current is not None:
            current["lines"].append(raw_line)
    if current is not None:
        documents.append(current)
    return documents


def _extract_prefab_collider_records(prefab_path: Path) -> list[dict[str, Any]]:
    documents = _parse_unity_prefab_documents(prefab_path)
    game_objects: dict[str, dict[str, str]] = {}
    transforms: dict[str, dict[str, tuple[float, float, float]]] = {}
    collider_docs: list[dict[str, Any]] = []

    for document in documents:
        lines = document["lines"]
        type_id = document["type_id"]
        file_id = document["file_id"]
        if type_id == 1:
            game_objects[file_id] = {
                "name": _parse_scalar(lines, "m_Name") or "",
                "tag": _parse_scalar(lines, "m_TagString") or "",
            }
        elif type_id == 4:
            game_object_id = _parse_game_object_file_id(lines)
            if game_object_id is None:
                continue
            local_position = _parse_vector3(lines, "m_LocalPosition") or (0.0, 0.0, 0.0)
            local_scale = _parse_vector3(lines, "m_LocalScale") or (1.0, 1.0, 1.0)
            transforms[game_object_id] = {
                "local_position": local_position,
                "local_scale": local_scale,
            }
        elif type_id == 65:
            collider_docs.append(document)

    colliders: list[dict[str, Any]] = []
    for document in collider_docs:
        lines = document["lines"]
        game_object_id = _parse_game_object_file_id(lines)
        if game_object_id is None:
            continue
        size = _parse_vector3(lines, "m_Size")
        center = _parse_vector3(lines, "m_Center")
        if size is None or center is None:
            continue
        is_trigger_raw = _parse_scalar(lines, "m_IsTrigger")
        is_trigger = is_trigger_raw == "1"
        transform = transforms.get(
            game_object_id,
            {"local_position": (0.0, 0.0, 0.0), "local_scale": (1.0, 1.0, 1.0)},
        )
        game_object = game_objects.get(game_object_id, {"name": "", "tag": ""})
        colliders.append(
            {
                "game_object_id": game_object_id,
                "name": game_object["name"],
                "tag": game_object["tag"],
                "is_trigger": is_trigger,
                "size_m": size,
                "center_m": center,
                "local_position_m": transform["local_position"],
                "local_scale": transform["local_scale"],
            }
        )
    return colliders


def _scaled_collider_bounds(collider: dict[str, Any]) -> dict[str, tuple[float, float, float]]:
    sx, sy, sz = collider["local_scale"]
    px, py, pz = collider["local_position_m"]
    cx, cy, cz = collider["center_m"]
    wx = abs(sx) * collider["size_m"][0]
    wy = abs(sy) * collider["size_m"][1]
    wz = abs(sz) * collider["size_m"][2]
    center_x = px + (sx * cx)
    center_y = py + (sy * cy)
    center_z = pz + (sz * cz)
    half_x = wx / 2.0
    half_y = wy / 2.0
    half_z = wz / 2.0
    return {
        "min": (center_x - half_x, center_y - half_y, center_z - half_z),
        "max": (center_x + half_x, center_y + half_y, center_z + half_z),
        "size": (wx, wy, wz),
        "center": (center_x, center_y, center_z),
    }


def _union_bounds(colliders: list[dict[str, Any]]) -> dict[str, tuple[float, float, float]]:
    if not colliders:
        raise ValueError("Cannot union zero colliders")
    mins: list[tuple[float, float, float]] = []
    maxs: list[tuple[float, float, float]] = []
    for collider in colliders:
        bounds = _scaled_collider_bounds(collider)
        mins.append(bounds["min"])
        maxs.append(bounds["max"])
    min_corner = (
        min(value[0] for value in mins),
        min(value[1] for value in mins),
        min(value[2] for value in mins),
    )
    max_corner = (
        max(value[0] for value in maxs),
        max(value[1] for value in maxs),
        max(value[2] for value in maxs),
    )
    return {
        "min": min_corner,
        "max": max_corner,
        "size": (
            max_corner[0] - min_corner[0],
            max_corner[1] - min_corner[1],
            max_corner[2] - min_corner[2],
        ),
        "center": (
            (min_corner[0] + max_corner[0]) / 2.0,
            (min_corner[1] + max_corner[1]) / 2.0,
            (min_corner[2] + max_corner[2]) / 2.0,
        ),
    }


def _measure_prefab_bounds(prefab_path: Path) -> dict[str, Any]:
    colliders = _extract_prefab_collider_records(prefab_path)
    preferred = [
        collider
        for collider in colliders
        if collider["name"] == "BoundingBox" and not collider["is_trigger"]
    ]
    if preferred:
        bounds = _scaled_collider_bounds(preferred[0])
        source = "bounding_box_collider"
        used_colliders = [preferred[0]]
    else:
        fallback = [
            collider
            for collider in colliders
            if collider["tag"] == "SimObjPhysics" and not collider["is_trigger"]
        ]
        if not fallback:
            raise ValueError(f"No usable non-trigger collider found in {prefab_path}")
        bounds = _union_bounds(fallback)
        source = "non_trigger_collider_union"
        used_colliders = fallback

    width_m, height_m, depth_m = bounds["size"]
    return {
        "measurement_source": source,
        "collider_count": len(colliders),
        "used_collider_count": len(used_colliders),
        "width_m": round(width_m, 6),
        "height_m": round(height_m, 6),
        "depth_m": round(depth_m, 6),
        "center_m": _vector_dict(*bounds["center"]),
        "min_corner_m": _vector_dict(*bounds["min"]),
        "max_corner_m": _vector_dict(*bounds["max"]),
        "upright_axis": "+y",
    }


def write_ai2thor_support_clutter_measurements(
    selection_manifest_path: Path,
    output_path: Path,
    raw_data_root: Path | None = None,
    created_at: str | None = None,
) -> dict:
    raw_root = raw_data_root or default_raw_data_root()
    selection_manifest = load_json(selection_manifest_path)
    if not isinstance(selection_manifest, dict):
        raise TypeError(f"Selection manifest at {selection_manifest_path} must be an object")
    assets = selection_manifest.get("assets")
    if not isinstance(assets, list):
        raise TypeError(f"Selection manifest at {selection_manifest_path} must contain an assets list")

    records: list[dict[str, Any]] = []
    for asset in assets:
        if not isinstance(asset, dict):
            raise TypeError("Selection manifest assets entries must be objects")
        category = str(asset["category"])
        asset_id = str(asset["asset_id"])
        raw_manifest_path = resolve_under(
            raw_root,
            AI2THOR_SUPPORT_CLUTTER_SLICE_ROOT / category / asset_id / "raw" / "source_manifest.json",
        )
        raw_manifest = load_json(raw_manifest_path)
        if not isinstance(raw_manifest, dict):
            raise TypeError(f"Raw source manifest at {raw_manifest_path} must be an object")
        raw_files = raw_manifest.get("raw_files")
        if not isinstance(raw_files, dict):
            raise TypeError(f"Raw source manifest at {raw_manifest_path} must define raw_files")
        prefab_ref = raw_files.get("prefab")
        if not isinstance(prefab_ref, dict):
            raise TypeError(f"Raw source manifest at {raw_manifest_path} must define raw_files.prefab")
        prefab_path_value = prefab_ref.get("path")
        if not isinstance(prefab_path_value, str):
            raise TypeError(f"Raw source manifest at {raw_manifest_path} must define prefab.path")
        prefab_path = resolve_under(raw_root, prefab_path_value)
        measurement = _measure_prefab_bounds(prefab_path)
        records.append(
            {
                "asset_id": asset_id,
                "category": category,
                "source_name": raw_manifest.get("source_name", asset.get("source_name", asset_id)),
                "raw_prefab_path": prefab_path_value,
                **measurement,
            }
        )

    payload = {
        "measurement_set_id": "support_clutter_ai2thor_v0_prefab_measurements_v0",
        "version": "support_clutter_ai2thor_prefab_measurements_v0",
        "selection_id": selection_manifest.get("selection_id", "ai2thor_support_clutter_v0"),
        "created_at": _timestamp(created_at),
        "notes": (
            "Approximate prop measurements derived from AI2-THOR Unity prefab colliders. "
            "BoundingBox colliders are preferred when available."
        ),
        "props": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {
        "measurement_set_id": payload["measurement_set_id"],
        "output": str(output_path.resolve()),
        "prop_count": len(records),
    }


def _prop_annotation_from_measurement(record: dict[str, Any]) -> dict[str, Any]:
    category = str(record["category"])
    width_m = float(record["width_m"])
    depth_m = float(record["depth_m"])
    max_horizontal = round(max(width_m, depth_m), 6)
    min_horizontal = round(min(width_m, depth_m), 6)

    if category == "mug":
        return {
            "asset_id": record["asset_id"],
            "category": category,
            "placement_class": "mug",
            "base_shape": "circle",
            "base_width_m": max_horizontal,
            "base_depth_m": max_horizontal,
            "support_margin_m": 0.015,
            "allowed_surface_types": ["coffee_table_top", "side_table_top"],
            "upright_axis": "+y",
            "stable_support_required": True,
            "placement_style": "scattered",
            "review_status": "auto",
            "notes": (
                f"Derived from {record['measurement_source']} in AI2-THOR prefab metadata."
            ),
        }

    if category == "book":
        return {
            "asset_id": record["asset_id"],
            "category": category,
            "placement_class": "book",
            "base_shape": "rectangle",
            "base_width_m": max_horizontal,
            "base_depth_m": min_horizontal,
            "support_margin_m": 0.01,
            "allowed_surface_types": [
                "coffee_table_top",
                "side_table_top",
                "bookshelf_shelf",
            ],
            "upright_axis": "+y",
            "stable_support_required": True,
            "placement_style": "grid_like",
            "review_status": "auto",
            "notes": (
                "Derived from prefab collider bounds and treated as a flat-lying v0 clutter prop."
            ),
        }

    raise ValueError(f"Unsupported support-clutter category: {category}")


def write_support_clutter_prop_annotation_set_from_measurements(
    measurements_path: Path,
    output_path: Path,
    created_at: str | None = None,
) -> dict:
    payload = load_json(measurements_path)
    if not isinstance(payload, dict):
        raise TypeError(f"Measurement payload at {measurements_path} must be an object")
    props = payload.get("props")
    if not isinstance(props, list):
        raise TypeError(f"Measurement payload at {measurements_path} must define a props list")

    annotations = {
        "annotation_set_id": "support_clutter_ai2thor_v0_prop_annotations_v0",
        "version": "support_clutter_prop_annotation_set_v0",
        "notes": (
            "First AI2-THOR-derived prop annotation set for the support-aware clutter bridge. "
            "Derived from prefab-based measurements."
        ),
        "props": [_prop_annotation_from_measurement(record) for record in props],
    }
    annotations = validate_support_clutter_prop_annotation_set_data(annotations)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(annotations, indent=2) + "\n", encoding="utf-8")
    return {
        "annotation_set_id": annotations["annotation_set_id"],
        "output": str(output_path.resolve()),
        "prop_count": len(annotations["props"]),
    }
