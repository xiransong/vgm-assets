from __future__ import annotations

from pathlib import Path

from vgm_assets.ai2thor_object_semantics import (
    _measure_refined_parent_prefab_bounds,
    write_ai2thor_object_semantics_candidates,
)
from vgm_assets.object_semantics import validate_object_semantics_annotation_set
from vgm_assets.sources import _default_ai2thor_repo_root


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_default_ai2thor_repo_root_points_to_local_repo_checkout() -> None:
    assert _default_ai2thor_repo_root() == REPO_ROOT.parent.parent / "ai2thor"


def test_write_ai2thor_object_semantics_candidates_generates_valid_benchmark_slice(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "ai2thor_candidates.json"
    summary = write_ai2thor_object_semantics_candidates(
        REPO_ROOT / "sources" / "ai2thor" / "object_semantics_selection_v0.json",
        output_path=output_path,
    )

    assert summary["asset_count"] == 9
    payload = validate_object_semantics_annotation_set(output_path)
    assert len(payload["assets"]) == 9

    by_asset_id = {asset["asset_id"]: asset for asset in payload["assets"]}
    coffee_table = by_asset_id["ai2thor_coffee_table_01"]
    assert coffee_table["asset_role"] == "parent_object"
    assert coffee_table["support_surfaces_v1"][0]["surface_type"] == "coffee_table_top"
    assert coffee_table["support_surfaces_v1"][0]["supports_categories"] == [
        "mug",
        "book",
        "bowl",
    ]

    bookshelf = by_asset_id["ai2thor_bookshelf_01"]
    assert bookshelf["review_status"] == "uncertain"
    assert bookshelf["bottom_support_plane"]["review_status"] == "uncertain"
    assert bookshelf["support_surfaces_v1"][0]["surface_type"] == "bookshelf_shelf"
    assert bookshelf["bottom_support_plane"]["width_m"] == 1.0
    assert bookshelf["bottom_support_plane"]["depth_m"] == 1.0

    tv_stand = by_asset_id["ai2thor_tv_stand_01"]
    assert tv_stand["asset_role"] == "parent_object"
    assert tv_stand["support_surfaces_v1"][0]["surface_type"] == "tv_stand_top"
    assert tv_stand["supports_objects"] is True

    sofa = by_asset_id["ai2thor_sofa_01"]
    assert sofa["asset_role"] == "parent_object"
    assert sofa["supports_objects"] is False
    assert sofa["support_surfaces_v1"] == []
    assert sofa["placement_class"] == "sofa"

    floor_lamp = by_asset_id["ai2thor_floor_lamp_01"]
    assert floor_lamp["asset_role"] == "parent_object"
    assert floor_lamp["supports_objects"] is False
    assert floor_lamp["support_surfaces_v1"] == []
    assert floor_lamp["placement_class"] == "floor_lamp"

    mug = by_asset_id["ai2thor_mug_01"]
    assert mug["asset_role"] == "child_object"
    assert mug["child_placement"]["allowed_surface_types"] == [
        "desk_top",
        "tv_stand_top",
        "coffee_table_top",
        "side_table_top",
        "counter_top",
        "bookshelf_shelf",
    ]


def test_refined_parent_measurement_clamps_side_table_floor_and_fixes_bookshelf_size() -> None:
    ai2thor_root = _default_ai2thor_repo_root()
    side_table_measurement = _measure_refined_parent_prefab_bounds(
        prefab_path=ai2thor_root
        / "unity/Assets/Physics/SimObjsPhysics/Common Objects/SideTable/Prefabs/Side_Table_Master_Prefabs/Side_Table_202_Master.prefab",
        category="side_table",
    )
    assert side_table_measurement["measurement_source"] == "bounding_box_collider"
    assert side_table_measurement["floor_contact_clamped"] is True
    assert side_table_measurement["min_corner_m"]["y"] == 0.0

    bookshelf_measurement = _measure_refined_parent_prefab_bounds(
        prefab_path=ai2thor_root
        / "unity/Assets/Physics/SimObjsPhysics/Entryway Objects/Furniture/StandingShelf.prefab",
        category="bookshelf",
    )
    assert bookshelf_measurement["measurement_source"] == "support_surface_fallback"
    assert bookshelf_measurement["width_m"] == 1.0
    assert bookshelf_measurement["depth_m"] == 1.0
    assert bookshelf_measurement["height_m"] >= 0.8
