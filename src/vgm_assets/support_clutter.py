from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .catalog import write_catalog_manifest
from .paths import default_raw_data_root, resolve_under
from .protocol import load_json, validator_class_for_schema
from .sampling import write_category_index
from .support_surfaces import (
    load_support_surface_annotation_set,
    validate_support_surface_annotation_set_data,
)

SUPPORT_CLUTTER_PROP_ANNOTATION_SET_SCHEMA = (
    Path("schemas") / "local" / "support_clutter_prop_annotation_set_v0.schema.json"
)
SUPPORT_CLUTTER_COMPATIBILITY_SCHEMA = (
    Path("schemas") / "local" / "support_clutter_compatibility_v0.schema.json"
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


def support_clutter_compatibility_schema_path() -> Path:
    return repo_root() / SUPPORT_CLUTTER_COMPATIBILITY_SCHEMA


def load_support_clutter_prop_annotation_set(path: Path) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise TypeError(f"Support-clutter prop annotation set at {path} must be a JSON object")
    return payload


def validate_support_clutter_prop_annotation_set_data(payload: object) -> dict:
    schema = load_json(support_clutter_prop_annotation_set_schema_path())
    validator_cls = validator_class_for_schema(schema)
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


def load_support_clutter_compatibility(path: Path) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise TypeError(f"Support-clutter compatibility payload at {path} must be a JSON object")
    return payload


def validate_support_clutter_compatibility_data(payload: object) -> dict:
    schema = load_json(support_clutter_compatibility_schema_path())
    validator_cls = validator_class_for_schema(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, dict):
        raise TypeError("Support-clutter compatibility payload must be an object after validation")
    return payload


def validate_support_clutter_compatibility(path: Path) -> dict:
    return validate_support_clutter_compatibility_data(load_support_clutter_compatibility(path))


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


def _annotation_map_by_asset_id(payload: dict, field_name: str) -> dict[str, dict[str, Any]]:
    records = payload.get(field_name)
    if not isinstance(records, list):
        raise TypeError(f"Expected {field_name} list in payload")
    mapped: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise TypeError(f"{field_name} entries must be objects")
        asset_id = record.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            raise ValueError(f"{field_name} entry is missing asset_id")
        mapped[asset_id] = record
    return mapped


def build_support_clutter_compatibility(
    *,
    support_surface_annotations_path: Path,
    prop_annotations_path: Path,
) -> dict:
    support_payload = validate_support_surface_annotation_set_data(
        load_support_surface_annotation_set(support_surface_annotations_path)
    )
    prop_payload = validate_support_clutter_prop_annotation_set_data(
        load_support_clutter_prop_annotation_set(prop_annotations_path)
    )

    support_assets = support_payload.get("assets", [])
    prop_records = prop_payload.get("props", [])

    available_surface_types: dict[str, dict[str, Any]] = {}
    for asset in support_assets:
        if not isinstance(asset, dict):
            raise TypeError("Support-surface asset annotations must be objects")
        asset_id = asset.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            raise ValueError("Support-surface asset annotation is missing asset_id")
        surfaces = asset.get("support_surfaces_v1", [])
        if not isinstance(surfaces, list):
            raise TypeError("support_surfaces_v1 must be a list")
        for surface in surfaces:
            if not isinstance(surface, dict):
                raise TypeError("support surface entries must be objects")
            surface_type = surface.get("surface_type")
            if not isinstance(surface_type, str) or not surface_type:
                raise ValueError("support surface entry is missing surface_type")
            categories = surface.get("supports_categories", [])
            if not isinstance(categories, list):
                raise TypeError("supports_categories must be a list")
            payload = available_surface_types.setdefault(
                surface_type,
                {"support_asset_ids": set(), "prop_categories": set()},
            )
            payload["support_asset_ids"].add(asset_id)
            for category in categories:
                if isinstance(category, str) and category:
                    payload["prop_categories"].add(category)

    prop_categories: dict[str, dict[str, Any]] = {}
    for record in prop_records:
        if not isinstance(record, dict):
            raise TypeError("Prop annotation entries must be objects")
        category = record.get("category")
        asset_id = record.get("asset_id")
        allowed = record.get("allowed_surface_types")
        if not isinstance(category, str) or not isinstance(asset_id, str):
            raise ValueError("Prop annotation entry must define category and asset_id")
        if not isinstance(allowed, list):
            raise TypeError("allowed_surface_types must be a list")
        entry = prop_categories.setdefault(
            category,
            {"allowed_support_surface_types": set(), "prop_asset_ids": []},
        )
        entry["prop_asset_ids"].append(asset_id)
        for surface_type in allowed:
            if not isinstance(surface_type, str):
                continue
            surface_info = available_surface_types.get(surface_type)
            if surface_info is None:
                continue
            if category not in surface_info["prop_categories"]:
                continue
            entry["allowed_support_surface_types"].add(surface_type)

    support_surface_types: dict[str, dict[str, Any]] = {}
    for surface_type, entry in available_surface_types.items():
        allowed_categories = sorted(
            category
            for category, prop_entry in prop_categories.items()
            if surface_type in prop_entry["allowed_support_surface_types"]
        )
        if not allowed_categories:
            continue
        support_surface_types[surface_type] = {
            "support_asset_ids": sorted(entry["support_asset_ids"]),
            "prop_categories": allowed_categories,
        }

    compatibility = {
        "version": "support_clutter_v0",
        "source_support_annotation_set_id": support_payload["annotation_set_id"],
        "source_prop_annotation_set_id": prop_payload["annotation_set_id"],
        "prop_categories": {
            category: {
                "allowed_support_surface_types": sorted(entry["allowed_support_surface_types"]),
                "prop_asset_ids": sorted(entry["prop_asset_ids"]),
            }
            for category, entry in sorted(prop_categories.items())
        },
        "support_surface_types": support_surface_types,
    }
    return validate_support_clutter_compatibility_data(compatibility)


def write_support_clutter_compatibility(
    *,
    support_surface_annotations_path: Path,
    prop_annotations_path: Path,
    output_path: Path,
) -> dict:
    compatibility = build_support_clutter_compatibility(
        support_surface_annotations_path=support_surface_annotations_path,
        prop_annotations_path=prop_annotations_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(compatibility, indent=2) + "\n", encoding="utf-8")
    return {
        "version": compatibility["version"],
        "output": str(output_path.resolve()),
        "prop_category_count": len(compatibility["prop_categories"]),
        "support_surface_type_count": len(compatibility["support_surface_types"]),
    }


def _build_prop_asset_record(
    *,
    bundle_manifest: dict[str, Any],
    measurement: dict[str, Any],
    annotation: dict[str, Any],
) -> dict[str, Any]:
    category = str(bundle_manifest["category"])
    width_m = float(measurement["width_m"])
    depth_m = float(measurement["depth_m"])
    height_m = float(measurement["height_m"])
    style_tags = bundle_manifest.get("style_tags", [])
    tags = ["prop", "support_clutter", category]
    if isinstance(style_tags, list):
        for tag in style_tags:
            if isinstance(tag, str) and tag not in tags:
                tags.append(tag)

    affordance_map = {
        "mug": ["tabletop_prop", "grasp"],
        "book": ["tabletop_prop", "book"],
    }
    record = {
        "asset_id": bundle_manifest["asset_id"],
        "category": category,
        "source": bundle_manifest["source"],
        "sample_weight": 1.0,
        "dimensions": {
            "width": round(width_m, 6),
            "depth": round(depth_m, 6),
            "height": round(height_m, 6),
        },
        "footprint": {
            "shape": annotation["base_shape"],
            "width": float(annotation["base_width_m"]),
            "depth": float(annotation["base_depth_m"]),
        },
        "placement": {
            "placement_type": "interior",
            "min_wall_clearance": 0.0,
            "min_object_clearance": 0.0,
            "allowed_orientations_deg": [0.0, 90.0, 180.0, 270.0],
        },
        "walkability": {
            "blocks_walking": False,
            "clearance_buffer": 0.0,
        },
        "semantics": {
            "tags": tags,
            "affordances": affordance_map.get(category, ["tabletop_prop"]),
        },
        "support": {
            "supports_objects": False,
            "support_surfaces": [],
        },
        "files": bundle_manifest.get("files", {}),
        "provenance": {
            "protocol_version": "v0",
            "producer": {
                "repo": "vgm-assets",
                "version": "0.1.0-dev",
                "commit": "working_tree",
            },
            "config_id": "support_clutter_ai2thor_v0_prefab_metadata_v0",
            "upstream_ids": [
                bundle_manifest["selection_id"],
                bundle_manifest["asset_id"],
                "support_clutter_ai2thor_v0_prefab_measurements_v0",
                "support_clutter_ai2thor_v0_prop_annotations_v0",
            ],
        },
    }
    return record


def refresh_support_clutter_asset_catalog(
    *,
    catalog_id: str,
    selection_manifest_path: Path,
    measurements_path: Path,
    prop_annotations_path: Path,
    support_surface_annotations_path: Path,
    catalog_output: Path,
    category_index_output: Path,
    support_compatibility_output: Path,
    manifest_output: Path,
    created_at: str | None = None,
) -> dict:
    selection_manifest = load_json(selection_manifest_path)
    if not isinstance(selection_manifest, dict):
        raise TypeError(f"Selection manifest at {selection_manifest_path} must be an object")
    assets = selection_manifest.get("assets")
    if not isinstance(assets, list):
        raise TypeError(f"Selection manifest at {selection_manifest_path} must define assets")

    measurements_payload = load_json(measurements_path)
    if not isinstance(measurements_payload, dict):
        raise TypeError(f"Measurements payload at {measurements_path} must be an object")
    measurement_map = _annotation_map_by_asset_id(measurements_payload, "props")

    prop_annotations_payload = validate_support_clutter_prop_annotation_set_data(
        load_support_clutter_prop_annotation_set(prop_annotations_path)
    )
    annotation_map = _annotation_map_by_asset_id(prop_annotations_payload, "props")

    records: list[dict[str, Any]] = []
    selection_root = selection_manifest_path.parent
    for asset in assets:
        if not isinstance(asset, dict):
            raise TypeError("Selection manifest assets must be objects")
        asset_id = asset.get("asset_id")
        normalized_dir = asset.get("normalized_dir")
        if not isinstance(asset_id, str) or not isinstance(normalized_dir, str):
            raise ValueError("Selection manifest asset entry must define asset_id and normalized_dir")
        bundle_manifest_path = selection_root / normalized_dir / "bundle_manifest.json"
        bundle_manifest = load_json(bundle_manifest_path)
        if not isinstance(bundle_manifest, dict):
            raise TypeError(f"Bundle manifest at {bundle_manifest_path} must be an object")
        measurement = measurement_map.get(asset_id)
        annotation = annotation_map.get(asset_id)
        if measurement is None:
            raise ValueError(f"Missing measurement for asset_id {asset_id}")
        if annotation is None:
            raise ValueError(f"Missing prop annotation for asset_id {asset_id}")
        records.append(
            _build_prop_asset_record(
                bundle_manifest=bundle_manifest,
                measurement=measurement,
                annotation=annotation,
            )
        )

    catalog_output.parent.mkdir(parents=True, exist_ok=True)
    catalog_output.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    category_index = write_category_index(catalog_output, category_index_output)
    manifest = write_catalog_manifest(
        catalog_path=catalog_output,
        output_path=manifest_output,
        catalog_id=catalog_id,
        created_at=created_at,
    )
    compatibility_summary = write_support_clutter_compatibility(
        support_surface_annotations_path=support_surface_annotations_path,
        prop_annotations_path=prop_annotations_path,
        output_path=support_compatibility_output,
    )
    return {
        "catalog_id": catalog_id,
        "asset_count": len(records),
        "catalog_output": str(catalog_output.resolve()),
        "category_index_output": str(category_index_output.resolve()),
        "category_count": category_index["category_count"],
        "support_compatibility_output": str(support_compatibility_output.resolve()),
        "support_surface_type_count": compatibility_summary["support_surface_type_count"],
        "manifest_output": str(manifest_output.resolve()),
        "manifest_created_at": manifest["created_at"],
    }
