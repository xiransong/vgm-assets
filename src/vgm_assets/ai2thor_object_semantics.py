from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .object_semantics import write_object_semantics_annotation_set
from .sources import (
    _default_ai2thor_repo_root,
    _require_entry,
    _select_entries,
    load_selection_list,
)
from .support_clutter import (
    _extract_prefab_collider_records,
    _measure_prefab_bounds,
    _scaled_collider_bounds,
    _union_bounds,
)

AI2THOR_OBJECT_SEMANTICS_SLICE_ROOT = Path("sources") / "ai2thor" / "object_semantics_v0"
_RESTRICTION_HEADER_RE = re.compile(r"^Receptacle Restrictions for:\s*(?P<object_type>[A-Za-z0-9_]+)\s*$")

_SURFACE_TYPE_BY_CATEGORY = {
    "coffee_table": "coffee_table_top",
    "side_table": "side_table_top",
    "bookshelf": "bookshelf_shelf",
    "tv_stand": "tv_stand_top",
    "desk": "desk_top",
    "counter_top": "counter_top",
}
_SURFACE_CLASS_BY_CATEGORY = {
    "coffee_table": "table_top",
    "side_table": "side_table_top",
    "bookshelf": "bookshelf_shelf",
    "tv_stand": "tv_stand_top",
    "desk": "desk_top",
    "counter_top": "counter_top",
}
_RECEPTACLE_LABEL_BY_CATEGORY = {
    "coffee_table": "CoffeeTable",
    "side_table": "SideTable",
    "bookshelf": "Shelf",
    "tv_stand": "TVStand",
    "desk": "Desk",
    "counter_top": "CounterTop",
}
_CHILD_BASE_SHAPE_BY_CATEGORY = {
    "mug": "circle",
    "bowl": "circle",
    "book": "rectangle",
}
_FRONT_AXIS_BY_CATEGORY = {
    "book": "+x",
}
_PLACEMENT_STYLE_BY_CATEGORY = {
    "coffee_table": "scattered",
    "side_table": "scattered",
    "bookshelf": "grid_like",
    "tv_stand": "aligned_front",
    "armchair": "centered",
    "sofa": "centered",
    "floor_lamp": "centered",
    "desk": "aligned_front",
    "mug": "scattered",
    "bowl": "scattered",
    "book": "grid_like",
}


def _timestamp(value: str | None = None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _vector_dict(x: float, y: float, z: float) -> dict[str, float]:
    return {"x": round(x, 6), "y": round(y, 6), "z": round(z, 6)}


def _normal_axis_for_bottom() -> str:
    return "+y"


def _front_axis_for_category(category: str) -> str:
    return _FRONT_AXIS_BY_CATEGORY.get(category, "+z")


def _load_ai2thor_placement_restrictions(source_repo_root: Path) -> dict[str, list[str]]:
    restrictions_path = (
        source_repo_root / "unity" / "Assets" / "DebugTextFiles" / "PlacementRestrictions.txt"
    )
    if not restrictions_path.exists():
        raise FileNotFoundError(f"Missing AI2-THOR placement restrictions file: {restrictions_path}")

    restrictions: dict[str, list[str]] = {}
    current_object_type: str | None = None
    for raw_line in restrictions_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        header_match = _RESTRICTION_HEADER_RE.match(line)
        if header_match is not None:
            current_object_type = header_match.group("object_type")
            restrictions.setdefault(current_object_type, [])
            continue
        if current_object_type is None:
            continue
        receptacles = [
            token.strip()
            for token in line.split(",")
            if token.strip()
        ]
        restrictions[current_object_type].extend(receptacles)
    return restrictions


def _local_surface_types_for_child_object_type(
    object_type: str,
    restrictions: dict[str, list[str]],
) -> list[str]:
    local_surface_types: list[str] = []
    for receptacle in restrictions.get(object_type, []):
        mapped = None
        if receptacle == "CoffeeTable":
            mapped = "coffee_table_top"
        elif receptacle == "SideTable":
            mapped = "side_table_top"
        elif receptacle == "Shelf":
            mapped = "bookshelf_shelf"
        elif receptacle == "TVStand":
            mapped = "tv_stand_top"
        elif receptacle == "Desk":
            mapped = "desk_top"
        elif receptacle == "CounterTop":
            mapped = "counter_top"
        if mapped is not None and mapped not in local_surface_types:
            local_surface_types.append(mapped)
    return local_surface_types


def _selected_child_categories_for_parent_category(
    parent_category: str,
    child_entries: list[dict[str, Any]],
    restrictions: dict[str, list[str]],
) -> list[str]:
    receptacle_label = _RECEPTACLE_LABEL_BY_CATEGORY.get(parent_category)
    if receptacle_label is None:
        return []

    categories: list[str] = []
    for entry in child_entries:
        object_type = str(_require_entry(entry, "object_type"))
        category = str(_require_entry(entry, "category"))
        if receptacle_label in restrictions.get(object_type, []) and category not in categories:
            categories.append(category)
    return categories


def _surface_candidates_from_prefab(prefab_path: Path) -> list[dict[str, Any]]:
    colliders = _extract_prefab_collider_records(prefab_path)
    candidates: list[dict[str, Any]] = []
    seen_keys: set[tuple[float, float, float, float, float]] = set()

    for collider in colliders:
        if not collider["is_trigger"]:
            continue
        bounds = _scaled_collider_bounds(collider)
        width_m, thickness_m, depth_m = bounds["size"]
        if min(width_m, depth_m) < 0.15:
            continue
        if thickness_m > min(width_m, depth_m) * 0.4:
            continue
        top_y = bounds["max"][1]
        if top_y <= 0.05:
            continue
        center = bounds["center"]
        key = (
            round(width_m, 4),
            round(depth_m, 4),
            round(center[0], 4),
            round(top_y, 4),
            round(center[2], 4),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        candidates.append(
            {
                "width_m": round(width_m, 6),
                "depth_m": round(depth_m, 6),
                "height_m": round(top_y, 6),
                "local_center_m": _vector_dict(center[0], top_y, center[2]),
            }
        )

    candidates.sort(key=lambda item: item["height_m"])
    return candidates


def _parent_surfaces_from_prefab(
    *,
    prefab_path: Path,
    category: str,
    supported_categories: list[str],
) -> list[dict[str, Any]]:
    if category not in _SURFACE_TYPE_BY_CATEGORY:
        return []
    surface_type = _SURFACE_TYPE_BY_CATEGORY[category]
    surface_class = _SURFACE_CLASS_BY_CATEGORY[category]
    candidates = _surface_candidates_from_prefab(prefab_path)
    if not candidates:
        return []

    if category != "bookshelf":
        candidates = [candidates[-1]]

    surfaces: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        if category == "bookshelf":
            surface_id = f"shelf_{index}"
        else:
            surface_id = "top"
        surfaces.append(
            {
                "surface_id": surface_id,
                "surface_type": surface_type,
                "surface_class": surface_class,
                "shape": "rectangle",
                "width_m": candidate["width_m"],
                "depth_m": candidate["depth_m"],
                "height_m": candidate["height_m"],
                "local_center_m": candidate["local_center_m"],
                "normal_axis": "+y",
                "front_axis": _front_axis_for_category(category),
                "usable_margin_m": 0.025 if category == "bookshelf" else 0.03,
                "supports_categories": supported_categories,
                "placement_style": _PLACEMENT_STYLE_BY_CATEGORY[category],
                "review_status": "auto",
            }
        )
    return surfaces


def _bottom_support_plane_from_measurement(
    *,
    category: str,
    width_m: float,
    depth_m: float,
    center_m: dict[str, Any],
    min_corner_m: dict[str, Any],
) -> dict[str, Any]:
    shape = _CHILD_BASE_SHAPE_BY_CATEGORY.get(category, "rectangle")
    if shape == "circle":
        diameter = round(max(width_m, depth_m), 6)
        plane_width_m = diameter
        plane_depth_m = diameter
    else:
        plane_width_m = round(width_m, 6)
        plane_depth_m = round(depth_m, 6)

    return {
        "shape": shape,
        "width_m": plane_width_m,
        "depth_m": plane_depth_m,
        "local_center_m": _vector_dict(
            float(center_m["x"]),
            float(min_corner_m["y"]),
            float(center_m["z"]),
        ),
        "normal_axis": _normal_axis_for_bottom(),
        "review_status": "auto",
    }


def _measure_parent_prefab_bounds(prefab_path: Path) -> dict[str, Any]:
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
        fallback = [collider for collider in colliders if not collider["is_trigger"]]
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


def _clamp_parent_measurement_floor_contact(measurement: dict[str, Any]) -> dict[str, Any]:
    min_y = float(measurement["min_corner_m"]["y"])
    if min_y >= 0.0 or min_y < -0.02:
        return measurement
    height_m = float(measurement["height_m"])
    min_corner_m = _vector_dict(
        float(measurement["min_corner_m"]["x"]),
        0.0,
        float(measurement["min_corner_m"]["z"]),
    )
    max_corner_m = _vector_dict(
        float(measurement["max_corner_m"]["x"]),
        round(height_m, 6),
        float(measurement["max_corner_m"]["z"]),
    )
    center_m = _vector_dict(
        float(measurement["center_m"]["x"]),
        round(height_m / 2.0, 6),
        float(measurement["center_m"]["z"]),
    )
    corrected = dict(measurement)
    corrected["center_m"] = center_m
    corrected["min_corner_m"] = min_corner_m
    corrected["max_corner_m"] = max_corner_m
    corrected["floor_contact_clamped"] = True
    return corrected


def _parent_bottom_support_plane_from_measurement(measurement: dict[str, Any]) -> dict[str, Any]:
    width_m = float(measurement["width_m"])
    depth_m = float(measurement["depth_m"])
    center_m = measurement["center_m"]
    min_corner_m = measurement["min_corner_m"]
    return {
        "shape": "rectangle",
        "width_m": round(width_m, 6),
        "depth_m": round(depth_m, 6),
        "local_center_m": _vector_dict(
            float(center_m["x"]),
            float(min_corner_m["y"]),
            float(center_m["z"]),
        ),
        "normal_axis": _normal_axis_for_bottom(),
        "review_status": "auto",
    }


def _child_annotation_from_selection_entry(
    *,
    entry: dict[str, Any],
    prefab_path: Path,
    restrictions: dict[str, list[str]],
) -> dict[str, Any]:
    category = str(_require_entry(entry, "category"))
    object_type = str(_require_entry(entry, "object_type"))
    measurement = _measure_prefab_bounds(prefab_path)
    width_m = float(measurement["width_m"])
    depth_m = float(measurement["depth_m"])
    max_horizontal = round(max(width_m, depth_m), 6)
    min_horizontal = round(min(width_m, depth_m), 6)
    allowed_surface_types = _local_surface_types_for_child_object_type(object_type, restrictions)

    return {
        "asset_id": str(_require_entry(entry, "asset_id")),
        "asset_role": "child_object",
        "category": category,
        "front_axis": _front_axis_for_category(category),
        "up_axis": "+y",
        "bottom_support_plane": _bottom_support_plane_from_measurement(
            category=category,
            width_m=width_m,
            depth_m=depth_m,
            center_m=measurement["center_m"],
            min_corner_m=measurement["min_corner_m"],
        ),
        "placement_class": category,
        "review_status": "auto",
        "review_notes": (
            f"AI2-THOR candidate annotation seeded from {prefab_path.name} using "
            f"{measurement['measurement_source']} and PlacementRestrictions.txt."
        ),
        "child_placement": {
            "base_shape": _CHILD_BASE_SHAPE_BY_CATEGORY.get(category, "rectangle"),
            "base_width_m": max_horizontal if category in {"mug", "bowl"} else max_horizontal,
            "base_depth_m": max_horizontal if category in {"mug", "bowl"} else min_horizontal,
            "support_margin_m": 0.015 if category in {"mug", "bowl"} else 0.01,
            "allowed_surface_types": allowed_surface_types,
            "upright_axis": "+y",
            "stable_support_required": True,
            "placement_style": _PLACEMENT_STYLE_BY_CATEGORY.get(category, "scattered"),
        },
    }


def _parent_measurement_is_implausibly_small(
    measurement: dict[str, Any],
    surfaces: list[dict[str, Any]],
) -> bool:
    width_m = float(measurement["width_m"])
    depth_m = float(measurement["depth_m"])
    if width_m < 0.1 or depth_m < 0.1:
        return True
    if not surfaces:
        return False
    max_surface_width = max(float(surface["width_m"]) for surface in surfaces)
    max_surface_depth = max(float(surface["depth_m"]) for surface in surfaces)
    return width_m < (max_surface_width * 0.2) or depth_m < (max_surface_depth * 0.2)


def _fallback_parent_measurement_from_surfaces(
    *,
    category: str,
    measurement: dict[str, Any],
    surfaces: list[dict[str, Any]],
) -> dict[str, Any]:
    primary_surface = max(surfaces, key=lambda surface: float(surface["width_m"]) * float(surface["depth_m"]))
    width_m = round(float(primary_surface["width_m"]), 6)
    depth_m = round(float(primary_surface["depth_m"]), 6)
    if category == "bookshelf":
        height_m = round(max(float(primary_surface["height_m"]) * 4.0, 0.8), 6)
    else:
        height_m = round(max(float(primary_surface["height_m"]) / 0.75, float(primary_surface["height_m"]) + 0.2), 6)
    center_x = float(primary_surface["local_center_m"]["x"])
    center_z = float(primary_surface["local_center_m"]["z"])
    min_y = 0.0
    max_y = round(min_y + height_m, 6)
    center_y = round((min_y + max_y) / 2.0, 6)
    return {
        "measurement_source": "support_surface_fallback",
        "fallback_from": str(measurement["measurement_source"]),
        "collider_count": int(measurement["collider_count"]),
        "used_collider_count": int(measurement["used_collider_count"]),
        "width_m": width_m,
        "height_m": height_m,
        "depth_m": depth_m,
        "center_m": _vector_dict(center_x, center_y, center_z),
        "min_corner_m": _vector_dict(center_x - (width_m / 2.0), min_y, center_z - (depth_m / 2.0)),
        "max_corner_m": _vector_dict(center_x + (width_m / 2.0), max_y, center_z + (depth_m / 2.0)),
        "upright_axis": "+y",
    }


def _measure_refined_parent_prefab_bounds(
    *,
    prefab_path: Path,
    category: str,
) -> dict[str, Any]:
    measurement = _clamp_parent_measurement_floor_contact(_measure_parent_prefab_bounds(prefab_path))
    surface_candidates = _surface_candidates_from_prefab(prefab_path)
    if category not in _SURFACE_TYPE_BY_CATEGORY:
        return measurement
    if _parent_measurement_is_implausibly_small(measurement, surface_candidates):
        return _fallback_parent_measurement_from_surfaces(
            category=category,
            measurement=measurement,
            surfaces=surface_candidates,
        )
    return measurement


def _parent_annotation_from_selection_entry(
    *,
    entry: dict[str, Any],
    prefab_path: Path,
    supported_categories: list[str],
) -> dict[str, Any]:
    category = str(_require_entry(entry, "category"))
    measurement = _measure_refined_parent_prefab_bounds(
        prefab_path=prefab_path,
        category=category,
    )
    surfaces = _parent_surfaces_from_prefab(
        prefab_path=prefab_path,
        category=category,
        supported_categories=supported_categories,
    )
    review_status = "auto"
    bottom_support_plane = _parent_bottom_support_plane_from_measurement(measurement)
    if not surfaces:
        review_suffix = (
            "No horizontal receptacle trigger colliders were used for this asset, so the candidate "
            "review focuses on orientation, bottom support, and canonical bounds."
        )
    else:
        review_suffix = "Support surfaces were derived from horizontal trigger colliders."
    if measurement["measurement_source"] == "support_surface_fallback":
        bottom_support_plane["review_status"] = "uncertain"
        review_status = "uncertain"
        review_suffix = (
            "Support surfaces were derived from horizontal trigger colliders, and the canonical "
            "bounds fell back to the strongest seeded support surface because the prefab collider "
            "bounds looked implausibly small."
        )
    elif measurement.get("floor_contact_clamped") is True:
        review_suffix = (
            "Support surfaces were derived from horizontal trigger colliders, and a small negative "
            "floor-contact offset from the prefab collider seed was clamped to zero for review."
        )
    return {
        "asset_id": str(_require_entry(entry, "asset_id")),
        "asset_role": "parent_object",
        "category": category,
        "front_axis": _front_axis_for_category(category),
        "up_axis": "+y",
        "bottom_support_plane": bottom_support_plane,
        "placement_class": category,
        "review_status": review_status,
        "review_notes": (
            f"AI2-THOR candidate annotation seeded from {prefab_path.name}. {review_suffix}"
        ),
        "supports_objects": bool(surfaces),
        "support_surfaces_v1": surfaces,
    }


def write_ai2thor_object_semantics_candidates(
    selection_path: Path,
    *,
    output_path: Path,
    source_repo_root: Path | None = None,
    selection_ids: list[str] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    source_root = (source_repo_root or _default_ai2thor_repo_root()).resolve()
    payload = load_selection_list(selection_path)
    selected_payload = _select_entries(
        payload,
        selection_ids=selection_ids,
        label="AI2-THOR object semantics",
        selection_path=selection_path,
    )
    restrictions = _load_ai2thor_placement_restrictions(source_root)

    child_entries = [
        entry for entry in selected_payload if str(_require_entry(entry, "asset_role")) == "child_object"
    ]
    annotations: list[dict[str, Any]] = []

    for entry in selected_payload:
        asset_role = str(_require_entry(entry, "asset_role"))
        prefab_path = source_root / Path(str(_require_entry(entry, "source_prefab_rel")))
        if not prefab_path.exists():
            raise FileNotFoundError(f"Missing AI2-THOR prefab: {prefab_path}")

        if asset_role == "child_object":
            annotations.append(
                _child_annotation_from_selection_entry(
                    entry=entry,
                    prefab_path=prefab_path,
                    restrictions=restrictions,
                )
            )
            continue

        if asset_role == "parent_object":
            supported_categories = _selected_child_categories_for_parent_category(
                str(_require_entry(entry, "category")),
                child_entries,
                restrictions,
            )
            annotations.append(
                _parent_annotation_from_selection_entry(
                    entry=entry,
                    prefab_path=prefab_path,
                    supported_categories=supported_categories,
                )
            )
            continue

        raise ValueError(f"Unsupported asset_role in selection entry: {asset_role}")

    annotation_set = {
        "annotation_set_id": "ai2thor_object_semantics_v0_candidates",
        "version": "object_semantics_annotation_set_v0",
        "notes": (
            "First AI2-THOR-derived candidate object-semantics annotation set for the "
            "benchmark parent/child review slice."
        ),
        "assets": annotations,
    }
    write_object_semantics_annotation_set(annotation_set, output_path)
    return {
        "annotation_set_id": annotation_set["annotation_set_id"],
        "output": str(output_path.resolve()),
        "asset_count": len(annotations),
        "selection_count": len(selected_payload),
        "created_at": _timestamp(created_at),
        "selection_root": str(AI2THOR_OBJECT_SEMANTICS_SLICE_ROOT),
    }
