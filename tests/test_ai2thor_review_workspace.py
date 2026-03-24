from __future__ import annotations

from pathlib import Path

from vgm_assets.ai2thor_review_workspace import (
    ai2thor_object_semantics_candidate_path,
    ai2thor_object_semantics_review_queue_path,
    ai2thor_object_semantics_review_workspace_root,
    refresh_ai2thor_object_semantics_review_workspace,
)
from vgm_assets.object_semantics import validate_object_semantics_annotation_set
from vgm_assets.object_semantics_explorer import default_object_semantics_explorer_config
from vgm_assets.object_semantics_review_queue import validate_object_semantics_review_queue


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_refresh_ai2thor_object_semantics_review_workspace_writes_processed_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    data_root = tmp_path / "processed"
    summary = refresh_ai2thor_object_semantics_review_workspace(
        REPO_ROOT / "sources" / "ai2thor" / "object_semantics_selection_v0.json",
        data_root=data_root,
    )

    workspace_root = ai2thor_object_semantics_review_workspace_root(data_root)
    assert summary["workspace_root"] == str(workspace_root)
    candidate_path = ai2thor_object_semantics_candidate_path(data_root)
    queue_path = ai2thor_object_semantics_review_queue_path(data_root)
    assert candidate_path.exists()
    assert queue_path.exists()

    candidate_payload = validate_object_semantics_annotation_set(candidate_path)
    assert len(candidate_payload["assets"]) == 9

    queue_payload = validate_object_semantics_review_queue(queue_path)
    assert queue_payload["item_count"] == 9
    assert queue_payload["batch_count"] == 3
    assert queue_payload["batches"][0]["entries"][0]["asset_id"] == "ai2thor_coffee_table_01"
    assert queue_payload["batches"][1]["entries"][0]["asset_id"] == "ai2thor_tv_stand_01"

    monkeypatch.setenv("VGM_ASSETS_DATA_ROOT", str(data_root))
    config = default_object_semantics_explorer_config()
    assert config.candidate_path == candidate_path.resolve()
