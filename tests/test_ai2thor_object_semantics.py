from __future__ import annotations

from pathlib import Path

from vgm_assets.ai2thor_object_semantics import write_ai2thor_object_semantics_candidates
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

    assert summary["asset_count"] == 6
    payload = validate_object_semantics_annotation_set(output_path)
    assert len(payload["assets"]) == 6

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
