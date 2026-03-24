from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from vgm_assets.object_semantics_explorer import (
    ObjectSemanticsExplorerConfig,
    default_object_semantics_explorer_config,
    get_object_semantics_asset_detail,
)
from vgm_assets.object_semantics_explorer_app import create_app
from vgm_assets.object_semantics_review_queue import validate_object_semantics_review_queue


def _explorer_fixture(tmp_path: Path) -> ObjectSemanticsExplorerConfig:
    default = default_object_semantics_explorer_config()
    reviewed_path = tmp_path / "ai2thor_reviewed_annotations_v0.json"
    review_queue_path = tmp_path / "ai2thor_review_queue_v0.json"
    review_queue_path.write_text(
        default.review_queue_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return ObjectSemanticsExplorerConfig(
        candidate_path=default.candidate_path,
        reviewed_path=reviewed_path,
        review_queue_path=review_queue_path,
        selection_path=default.selection_path,
        source_repo_root=default.source_repo_root,
        frontend_dist_path=tmp_path / "frontend_dist",
    )


def test_explorer_api_lists_assets_and_resolves_model_pack(tmp_path: Path) -> None:
    config = _explorer_fixture(tmp_path)
    app = create_app(config)
    client = TestClient(app)

    response = client.get("/api/object-semantics/assets")
    assert response.status_code == 200
    payload = response.json()
    assert payload["review_queue"]["batch_count"] == 2
    assert [asset["asset_id"] for asset in payload["assets"]] == [
        "ai2thor_coffee_table_01",
        "ai2thor_side_table_01",
        "ai2thor_bookshelf_01",
        "ai2thor_mug_01",
        "ai2thor_book_01",
        "ai2thor_bowl_01",
    ]
    assert payload["assets"][0]["has_model_pack"] is True
    assert payload["assets"][0]["has_review_mesh"] is True
    assert payload["assets"][0]["has_reviewed_override"] is False


def test_explorer_api_saves_reviewed_asset_without_touching_candidate(tmp_path: Path) -> None:
    config = _explorer_fixture(tmp_path)
    app = create_app(config)
    client = TestClient(app)

    detail = get_object_semantics_asset_detail(config, "ai2thor_coffee_table_01")
    detail["asset"]["review_status"] = "reviewed"
    detail["asset"]["review_notes"] = "confirmed by reviewer"
    detail["asset"]["review_scope_v0"] = [
        "asset_role",
        "category",
        "front_axis",
        "up_axis",
        "bottom_support_surface",
        "support_surfaces_v1",
        "canonical_bounds",
    ]
    detail["asset"]["needs_fix_targets_v0"] = []

    response = client.post("/api/object-semantics/assets/ai2thor_coffee_table_01", json=detail["asset"])
    assert response.status_code == 200
    saved = response.json()
    assert saved["asset"]["review_status"] == "reviewed"
    assert saved["current_source"] == "reviewed"
    assert saved["asset"]["review_scope_v0"][-1] == "canonical_bounds"

    reviewed_payload = json.loads(config.reviewed_path.read_text(encoding="utf-8"))
    reviewed_assets = {asset["asset_id"]: asset for asset in reviewed_payload["assets"]}
    assert reviewed_assets["ai2thor_coffee_table_01"]["review_notes"] == "confirmed by reviewer"
    assert reviewed_assets["ai2thor_coffee_table_01"]["review_scope_v0"][0] == "asset_role"
    assert reviewed_assets["ai2thor_mug_01"]["review_status"] == "auto"
    queue_payload = validate_object_semantics_review_queue(config.review_queue_path)
    queue_entries = {
        entry["asset_id"]: entry
        for batch in queue_payload["batches"]
        for entry in batch["entries"]
    }
    assert queue_entries["ai2thor_coffee_table_01"]["queue_status"] == "reviewed"

    candidate_payload = json.loads(config.candidate_path.read_text(encoding="utf-8"))
    candidate_assets = {asset["asset_id"]: asset for asset in candidate_payload["assets"]}
    assert candidate_assets["ai2thor_coffee_table_01"]["review_status"] == "auto"


def test_explorer_detail_exposes_canonical_bounds_and_source_refs(tmp_path: Path) -> None:
    config = _explorer_fixture(tmp_path)
    detail = get_object_semantics_asset_detail(config, "ai2thor_mug_01")

    assert detail["source_refs"]["prefab"]["exists"] is True
    assert detail["source_refs"]["model_pack"]["format"] == "fbx"
    assert detail["source_refs"]["review_mesh"]["mesh_instances"][0]["mesh_name"] == "mug_1"
    assert detail["canonical_bounds"]["normalization_source"] == "ai2thor_prefab_collider"
    assert detail["canonical_bounds"]["measurement_source"] == "bounding_box_collider"
    assert detail["proxy_bounds"]["measurement_source"] == "bounding_box_collider"
    assert detail["canonical_bounds"]["width_m"] == detail["proxy_bounds"]["width_m"]
