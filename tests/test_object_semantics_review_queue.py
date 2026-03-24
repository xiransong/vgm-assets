from __future__ import annotations

from pathlib import Path

import pytest

from vgm_assets.object_semantics_review_queue import (
    validate_object_semantics_review_queue,
    validate_object_semantics_review_queue_data,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ai2thor_object_semantics_review_queue_validates() -> None:
    payload = validate_object_semantics_review_queue(
        REPO_ROOT / "catalogs" / "object_semantics_v0" / "ai2thor_review_queue_v0.json"
    )
    assert payload["version"] == "object_semantics_review_queue_v0"
    assert payload["batch_count"] == 2
    assert payload["item_count"] == 6
    assert payload["batches"][0]["entries"][0]["asset_id"] == "ai2thor_coffee_table_01"


def test_review_queue_rejects_unknown_needs_fix_target() -> None:
    with pytest.raises(Exception):
        validate_object_semantics_review_queue_data(
            {
                "queue_id": "broken_review_queue_v0",
                "version": "object_semantics_review_queue_v0",
                "source_id": "ai2thor_object_semantics_v0",
                "candidate_annotation_set_ref": "catalogs/object_semantics_v0/ai2thor_candidate_annotations_v0.json",
                "reviewed_annotation_set_ref": "catalogs/object_semantics_v0/ai2thor_reviewed_annotations_v0.json",
                "created_at": "2026-03-24T00:00:00+00:00",
                "review_scope_v0": ["asset_role", "category"],
                "item_count": 1,
                "batch_count": 1,
                "batches": [
                    {
                        "batch_id": "broken_batch_v0",
                        "title": "Broken Batch",
                        "status": "pending",
                        "recommended_session_asset_count": 1,
                        "asset_count": 1,
                        "entries": [
                            {
                                "queue_item_id": "broken_batch_v0_000",
                                "asset_id": "ai2thor_mug_01",
                                "asset_role": "child_object",
                                "category": "mug",
                                "sort_key": 0,
                                "priority": "normal",
                                "queue_status": "needs_fix",
                                "annotation_review_status": "uncertain",
                                "needs_fix_targets_v0": ["unknown_field"]
                            }
                        ]
                    }
                ]
            }
        )
