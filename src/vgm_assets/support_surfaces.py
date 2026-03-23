from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from .protocol import load_json, validator_class_for_schema

SUPPORT_SURFACE_ANNOTATION_SET_SCHEMA = (
    Path("schemas") / "local" / "support_surface_annotation_set_v1.schema.json"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def support_surface_annotation_set_schema_path() -> Path:
    return repo_root() / SUPPORT_SURFACE_ANNOTATION_SET_SCHEMA


def load_support_surface_annotation_set(path: Path) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise TypeError(f"Support-surface annotation set at {path} must be a JSON object")
    return payload


def validate_support_surface_annotation_set_data(payload: object) -> dict:
    schema = load_json(support_surface_annotation_set_schema_path())
    validator_cls = validator_class_for_schema(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, dict):
        raise TypeError("Support-surface annotation payload must be an object after validation")
    return payload


def validate_support_surface_annotation_set(path: Path) -> dict:
    return validate_support_surface_annotation_set_data(load_support_surface_annotation_set(path))


def _support_annotation_map(payload: dict) -> dict[str, dict[str, Any]]:
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise TypeError("Support-surface annotation payload must define an assets list")
    mapped: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise TypeError("Support-surface asset entries must be objects")
        asset_id = asset.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            raise ValueError("Support-surface asset entry is missing asset_id")
        mapped[asset_id] = asset
    return mapped


def build_protocol_support_from_annotation(annotation: dict[str, Any]) -> dict[str, Any]:
    surfaces = annotation.get("support_surfaces_v1")
    if not isinstance(surfaces, list):
        raise TypeError("support_surfaces_v1 must be a list")
    thin_surfaces: list[dict[str, Any]] = []
    rich_surfaces: list[dict[str, Any]] = []
    for surface in surfaces:
        if not isinstance(surface, dict):
            raise TypeError("support surface annotations must be objects")
        thin_surfaces.append(
            {
                "surface_id": surface["surface_id"],
                "height": surface["height_m"],
                "width": surface["width_m"],
                "depth": surface["depth_m"],
            }
        )
        rich_surfaces.append(
            {
                "surface_id": surface["surface_id"],
                "surface_type": surface["surface_type"],
                "surface_class": surface["surface_class"],
                "shape": surface["shape"],
                "width_m": surface["width_m"],
                "depth_m": surface["depth_m"],
                "height_m": surface["height_m"],
                "local_center_m": deepcopy(surface["local_center_m"]),
                "normal_axis": surface["normal_axis"],
                "front_axis": surface["front_axis"],
                "usable_margin_m": surface["usable_margin_m"],
            }
        )
    return {
        "supports_objects": bool(annotation.get("supports_objects", False)),
        "support_surfaces": thin_surfaces,
        "support_surfaces_v1": rich_surfaces,
    }


def apply_support_surface_annotations_to_asset_records(
    records: list[dict[str, Any]],
    support_annotations_payload: dict,
) -> list[dict[str, Any]]:
    annotation_map = _support_annotation_map(support_annotations_payload)
    updated: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            raise TypeError("Asset records must be objects")
        cloned = deepcopy(record)
        asset_id = cloned.get("asset_id")
        if isinstance(asset_id, str) and asset_id in annotation_map:
            cloned["support"] = build_protocol_support_from_annotation(annotation_map[asset_id])
        updated.append(cloned)
    return updated


def filter_support_surface_annotations_for_asset_records(
    records: list[dict[str, Any]],
    support_annotations_payload: dict,
) -> dict[str, Any]:
    validated = validate_support_surface_annotation_set_data(support_annotations_payload)
    annotation_map = _support_annotation_map(validated)
    asset_ids = {
        record.get("asset_id")
        for record in records
        if isinstance(record, dict) and isinstance(record.get("asset_id"), str)
    }
    filtered_assets = [
        deepcopy(annotation_map[asset_id])
        for asset_id in sorted(asset_ids)
        if asset_id in annotation_map
    ]
    result = {
        "annotation_set_id": validated["annotation_set_id"],
        "version": validated["version"],
        "notes": validated.get("notes", ""),
        "assets": filtered_assets,
    }
    return validate_support_surface_annotation_set_data(result)


def write_support_surface_annotation_set(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    validated = validate_support_surface_annotation_set_data(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(validated, indent=2) + "\n", encoding="utf-8")
    return validated
