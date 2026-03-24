from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .ai2thor_object_semantics import write_ai2thor_object_semantics_candidates
from .object_semantics import validate_object_semantics_annotation_set
from .object_semantics_review_queue import (
    write_object_semantics_review_queue,
)
from .paths import data_root_relative_or_absolute, default_data_root
from .sources import _default_ai2thor_repo_root

AI2THOR_OBJECT_SEMANTICS_REVIEW_ROOT = (
    Path("review") / "object_semantics" / "ai2thor" / "object_semantics_v0"
)
REVIEW_SCOPE_V0 = [
    "asset_role",
    "category",
    "front_axis",
    "up_axis",
    "bottom_support_surface",
    "support_surfaces_v1",
    "canonical_bounds",
]


def ai2thor_object_semantics_review_workspace_root(data_root: Path | None = None) -> Path:
    return (data_root or default_data_root()).resolve() / AI2THOR_OBJECT_SEMANTICS_REVIEW_ROOT


def ai2thor_object_semantics_candidate_path(data_root: Path | None = None) -> Path:
    return ai2thor_object_semantics_review_workspace_root(data_root) / "candidate_annotations_v0.json"


def ai2thor_object_semantics_reviewed_path(data_root: Path | None = None) -> Path:
    return ai2thor_object_semantics_review_workspace_root(data_root) / "reviewed_annotations_v0.json"


def ai2thor_object_semantics_review_queue_path(data_root: Path | None = None) -> Path:
    return ai2thor_object_semantics_review_workspace_root(data_root) / "review_queue_v0.json"


def _review_status_to_queue_status(review_status: str) -> str:
    if review_status == "reviewed":
        return "reviewed"
    if review_status == "uncertain":
        return "needs_fix"
    if review_status == "rejected":
        return "rejected"
    return "pending"


def _batch_status(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "completed"
    queue_statuses = {entry["queue_status"] for entry in entries}
    if queue_statuses <= {"reviewed", "rejected", "deferred"}:
        return "completed"
    if queue_statuses == {"pending"}:
        return "pending"
    return "in_progress"


def build_ai2thor_object_semantics_review_queue_data(
    *,
    candidate_payload: dict,
    reviewed_payload: dict | None,
    selection_path: Path,
    data_root: Path | None = None,
    created_at: str,
) -> dict:
    reviewed_map = {
        str(asset["asset_id"]): asset
        for asset in reviewed_payload.get("assets", [])
        if isinstance(asset, dict) and isinstance(asset.get("asset_id"), str)
    } if reviewed_payload is not None else {}

    parent_entries: list[dict[str, Any]] = []
    child_entries: list[dict[str, Any]] = []

    for sort_key, candidate_asset in enumerate(candidate_payload.get("assets", [])):
        if not isinstance(candidate_asset, dict):
            continue
        asset_id = str(candidate_asset["asset_id"])
        current_asset = deepcopy(reviewed_map.get(asset_id, candidate_asset))
        category = str(current_asset["category"])
        asset_role = str(current_asset["asset_role"])
        queue_entry = {
            "queue_item_id": f"ai2thor_object_semantics_v0_{sort_key:03d}",
            "asset_id": asset_id,
            "asset_role": asset_role,
            "category": category,
            "sort_key": sort_key,
            "priority": "high" if asset_role == "parent_object" else "normal",
            "queue_status": _review_status_to_queue_status(str(current_asset.get("review_status", "auto"))),
            "annotation_review_status": str(current_asset.get("review_status", "auto")),
        }
        review_notes = current_asset.get("review_notes")
        if isinstance(review_notes, str) and review_notes.strip():
            queue_entry["review_notes"] = review_notes
        needs_fix_targets = current_asset.get("needs_fix_targets_v0")
        if isinstance(needs_fix_targets, list) and needs_fix_targets:
            queue_entry["needs_fix_targets_v0"] = needs_fix_targets

        if asset_role == "parent_object":
            parent_entries.append(queue_entry)
        else:
            child_entries.append(queue_entry)

    parent_batch = {
        "batch_id": "ai2thor_supporting_parents_v0",
        "title": "Supporting Parents",
        "status": _batch_status(parent_entries),
        "recommended_session_asset_count": max(len(parent_entries), 1),
        "asset_count": len(parent_entries),
        "notes": "Review furniture-like supporting parents together so support-surface judgments stay consistent across the batch.",
        "entries": parent_entries,
    }
    child_batch = {
        "batch_id": "ai2thor_tabletop_children_v0",
        "title": "Tabletop Children",
        "status": _batch_status(child_entries),
        "recommended_session_asset_count": max(len(child_entries), 1),
        "asset_count": len(child_entries),
        "notes": "Review tabletop child props together so upright-axis and base-support judgments remain coherent.",
        "entries": child_entries,
    }
    batches = [batch for batch in (parent_batch, child_batch) if batch["asset_count"] > 0]

    return {
        "queue_id": "ai2thor_object_semantics_review_queue_v0",
        "version": "object_semantics_review_queue_v0",
        "source_id": "ai2thor_object_semantics_v0",
        "candidate_annotation_set_ref": data_root_relative_or_absolute(
            ai2thor_object_semantics_candidate_path(data_root),
            data_root,
        ),
        "reviewed_annotation_set_ref": data_root_relative_or_absolute(
            ai2thor_object_semantics_reviewed_path(data_root),
            data_root,
        ),
        "created_at": created_at,
        "review_scope_v0": list(
            candidate_payload.get("assets", [{}])[0].get("review_scope_v0", REVIEW_SCOPE_V0)
        )
        if candidate_payload.get("assets")
        else list(REVIEW_SCOPE_V0),
        "item_count": len(parent_entries) + len(child_entries),
        "batch_count": len(batches),
        "notes": (
            "Generated from the AI2-THOR object-semantics candidate artifact and the current "
            "reviewed working copy in the processed review workspace."
        ),
        "batches": batches,
    }


def refresh_ai2thor_object_semantics_review_workspace(
    selection_path: Path,
    *,
    data_root: Path | None = None,
    source_repo_root: Path | None = None,
    created_at: str | None = None,
) -> dict:
    workspace_root = ai2thor_object_semantics_review_workspace_root(data_root)
    workspace_root.mkdir(parents=True, exist_ok=True)

    candidate_path = ai2thor_object_semantics_candidate_path(data_root)
    candidate_summary = write_ai2thor_object_semantics_candidates(
        selection_path,
        output_path=candidate_path,
        source_repo_root=source_repo_root or _default_ai2thor_repo_root(),
        created_at=created_at,
    )
    candidate_payload = validate_object_semantics_annotation_set(candidate_path)

    reviewed_path = ai2thor_object_semantics_reviewed_path(data_root)
    reviewed_payload = (
        validate_object_semantics_annotation_set(reviewed_path) if reviewed_path.exists() else None
    )

    queue_path = ai2thor_object_semantics_review_queue_path(data_root)
    queue_payload = build_ai2thor_object_semantics_review_queue_data(
        candidate_payload=candidate_payload,
        reviewed_payload=reviewed_payload,
        selection_path=selection_path,
        data_root=data_root,
        created_at=str(candidate_summary["created_at"]),
    )
    write_object_semantics_review_queue(queue_payload, queue_path)

    return {
        "workspace_root": str(workspace_root),
        "candidate_path": str(candidate_path),
        "reviewed_path": str(reviewed_path),
        "review_queue_path": str(queue_path),
        "asset_count": candidate_summary["asset_count"],
    }
