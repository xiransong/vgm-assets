from __future__ import annotations

import json
from pathlib import Path

from .catalog import validate_asset_catalog
from .protocol import load_json


def load_size_normalization_plan(plan_path: Path) -> dict:
    payload = load_json(plan_path)
    if not isinstance(payload, dict):
        raise TypeError(f"Size-normalization plan at {plan_path} must be a JSON object")
    targets = payload.get("targets")
    if not isinstance(targets, dict) or not targets:
        raise ValueError(f"Size-normalization plan at {plan_path} must define non-empty 'targets'")
    config_id = payload.get("config_id")
    if not isinstance(config_id, str) or not config_id:
        raise ValueError(f"Size-normalization plan at {plan_path} must define non-empty 'config_id'")
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


def _apply_target_dimensions(asset: dict, target: dict, *, config_id: str) -> dict:
    updated = json.loads(json.dumps(asset))

    old_dims = updated["dimensions"]
    new_width = float(target["width"])
    new_depth = float(target["depth"])
    new_height = float(target["height"])

    sx = new_width / float(old_dims["width"])
    sy = new_height / float(old_dims["height"])
    sz = new_depth / float(old_dims["depth"])

    updated["dimensions"] = {
        "width": round(new_width, 3),
        "depth": round(new_depth, 3),
        "height": round(new_height, 3),
    }

    footprint = updated.get("footprint")
    if isinstance(footprint, dict):
        shape = footprint.get("shape", "rectangle")
        if shape == "circle":
            diameter = round(max(new_width, new_depth), 3)
            updated["footprint"] = {
                "shape": "circle",
                "width": diameter,
                "depth": diameter,
            }
        else:
            updated["footprint"] = {
                "shape": shape,
                "width": round(new_width, 3),
                "depth": round(new_depth, 3),
            }

    support = updated.get("support")
    if isinstance(support, dict):
        surfaces = support.get("support_surfaces")
        if isinstance(surfaces, list):
            support["support_surfaces"] = [
                _scaled_support_surface(surface, sx, sy, sz) for surface in surfaces
            ]

    provenance = updated.get("provenance")
    if isinstance(provenance, dict):
        provenance["config_id"] = config_id

    return updated


def apply_size_normalization(
    catalog_path: Path,
    plan_path: Path,
    *,
    output_path: Path | None = None,
) -> dict:
    plan = load_size_normalization_plan(plan_path)
    targets = plan["targets"]
    config_id = plan["config_id"]

    payload = load_json(catalog_path)
    if not isinstance(payload, list):
        raise TypeError(f"Catalog at {catalog_path} must be a JSON array")

    updated_records = []
    updated_asset_ids: list[str] = []
    for record in payload:
        if not isinstance(record, dict):
            raise TypeError(f"Catalog at {catalog_path} contains a non-object entry")
        asset_id = record.get("asset_id")
        if isinstance(asset_id, str) and asset_id in targets:
            updated_records.append(
                _apply_target_dimensions(record, targets[asset_id], config_id=config_id)
            )
            updated_asset_ids.append(asset_id)
        else:
            updated_records.append(record)

    target_output = output_path or catalog_path
    target_output.parent.mkdir(parents=True, exist_ok=True)
    target_output.write_text(json.dumps(updated_records, indent=2) + "\n", encoding="utf-8")
    validate_asset_catalog(target_output)

    return {
        "catalog_path": str(catalog_path.resolve()),
        "output_path": str(target_output.resolve()),
        "updated_asset_count": len(updated_asset_ids),
        "updated_asset_ids": updated_asset_ids,
        "config_id": config_id,
    }
