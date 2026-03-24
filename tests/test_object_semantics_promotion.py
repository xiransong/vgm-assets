from __future__ import annotations

import json
from pathlib import Path

import pytest

from vgm_assets.object_semantics import validate_object_semantics_annotation_set
from vgm_assets.object_semantics_promotion import promote_reviewed_object_semantics_slice


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _review_fixture(tmp_path: Path) -> tuple[Path, Path]:
    candidate_payload = json.loads(
        (REPO_ROOT / "catalogs" / "object_semantics_v0" / "ai2thor_candidate_annotations_v0.json").read_text(
            encoding="utf-8"
        )
    )
    queue_payload = json.loads(
        (REPO_ROOT / "catalogs" / "object_semantics_v0" / "ai2thor_review_queue_v0.json").read_text(
            encoding="utf-8"
        )
    )

    for asset in candidate_payload["assets"]:
        if asset["asset_id"] == "ai2thor_coffee_table_01":
            asset["review_status"] = "reviewed"
            asset["review_notes"] = "accepted supporting parent"
        elif asset["asset_id"] == "ai2thor_mug_01":
            asset["review_status"] = "reviewed"
            asset["review_notes"] = "accepted tabletop child"

    for batch in queue_payload["batches"]:
        for entry in batch["entries"]:
            if entry["asset_id"] in {"ai2thor_coffee_table_01", "ai2thor_mug_01"}:
                entry["queue_status"] = "reviewed"
                entry["annotation_review_status"] = "reviewed"

    reviewed_path = tmp_path / "reviewed_annotations_v0.json"
    queue_path = tmp_path / "review_queue_v0.json"
    _write_json(reviewed_path, candidate_payload)
    _write_json(queue_path, queue_payload)
    return reviewed_path, queue_path


def test_promote_reviewed_object_semantics_slice_writes_reviewed_only_outputs(tmp_path: Path) -> None:
    reviewed_path, queue_path = _review_fixture(tmp_path)

    summary = promote_reviewed_object_semantics_slice(
        reviewed_annotations=reviewed_path,
        review_queue=queue_path,
        output_dir=tmp_path / "export",
        export_id="ai2thor_reviewed_object_semantics_v0_r1",
    )

    assert summary["asset_count"] == 2
    assert summary["parent_asset_count"] == 1
    assert summary["child_asset_count"] == 1
    assert summary["categories"] == ["coffee_table", "mug"]

    reviewed_slice = validate_object_semantics_annotation_set(
        tmp_path / "export" / "reviewed_annotations_v0.json"
    )
    parent_slice = validate_object_semantics_annotation_set(
        tmp_path / "export" / "parent_object_annotations_v0.json"
    )
    child_slice = validate_object_semantics_annotation_set(
        tmp_path / "export" / "child_object_annotations_v0.json"
    )

    assert [asset["asset_id"] for asset in reviewed_slice["assets"]] == [
        "ai2thor_coffee_table_01",
        "ai2thor_mug_01",
    ]
    assert [asset["asset_id"] for asset in parent_slice["assets"]] == ["ai2thor_coffee_table_01"]
    assert [asset["asset_id"] for asset in child_slice["assets"]] == ["ai2thor_mug_01"]

    manifest = json.loads((tmp_path / "export" / "reviewed_slice_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "object_semantics_reviewed_slice_v0"
    assert manifest["asset_count"] == 2
    assert manifest["parent_asset_count"] == 1
    assert manifest["child_asset_count"] == 1


def test_promote_reviewed_object_semantics_slice_rejects_queue_mismatch(tmp_path: Path) -> None:
    reviewed_path, queue_path = _review_fixture(tmp_path)
    queue_payload = json.loads(queue_path.read_text(encoding="utf-8"))
    for batch in queue_payload["batches"]:
        for entry in batch["entries"]:
            if entry["asset_id"] == "ai2thor_mug_01":
                entry["queue_status"] = "needs_fix"
                entry["annotation_review_status"] = "uncertain"
    _write_json(queue_path, queue_payload)

    with pytest.raises(ValueError, match="only queue_status='reviewed' may be promoted"):
        promote_reviewed_object_semantics_slice(
            reviewed_annotations=reviewed_path,
            review_queue=queue_path,
            output_dir=tmp_path / "export",
            export_id="ai2thor_reviewed_object_semantics_v0_r1",
        )
