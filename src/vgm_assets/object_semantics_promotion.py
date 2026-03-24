from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import shutil
from pathlib import Path
from typing import Any

from .object_semantics import (
    validate_object_semantics_annotation_set,
    write_object_semantics_annotation_set,
)
from .object_semantics_review_queue import validate_object_semantics_review_queue
from .paths import repo_relative_or_absolute


def _replace_directory(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _timestamp(created_at: str | None = None) -> str:
    return created_at or datetime.now(timezone.utc).isoformat()


def _review_queue_entry_map(queue_payload: dict) -> dict[str, dict[str, Any]]:
    return {
        str(entry["asset_id"]): entry
        for batch in queue_payload.get("batches", [])
        if isinstance(batch, dict)
        for entry in batch.get("entries", [])
        if isinstance(entry, dict) and isinstance(entry.get("asset_id"), str)
    }


def _filtered_annotation_set(
    *,
    source_payload: dict,
    assets: list[dict[str, Any]],
    annotation_set_id: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "annotation_set_id": annotation_set_id,
        "version": source_payload["version"],
        "notes": notes,
        "assets": assets,
    }


def _write_json(payload: dict[str, Any], output_path: Path) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def promote_reviewed_object_semantics_slice(
    *,
    reviewed_annotations: Path,
    review_queue: Path,
    output_dir: Path,
    export_id: str,
    created_at: str | None = None,
    allow_empty: bool = False,
) -> dict[str, Any]:
    reviewed_payload = validate_object_semantics_annotation_set(reviewed_annotations)
    queue_payload = validate_object_semantics_review_queue(review_queue)
    queue_entry_map = _review_queue_entry_map(queue_payload)

    reviewed_assets: list[dict[str, Any]] = []
    for asset in reviewed_payload.get("assets", []):
        if not isinstance(asset, dict):
            continue
        if asset.get("review_status") != "reviewed":
            continue
        asset_id = str(asset["asset_id"])
        queue_entry = queue_entry_map.get(asset_id)
        if queue_entry is None:
            raise ValueError(f"Reviewed asset {asset_id} is missing from review queue {review_queue}")
        if queue_entry.get("queue_status") != "reviewed":
            raise ValueError(
                f"Reviewed asset {asset_id} has queue_status={queue_entry.get('queue_status')!r}; "
                "only queue_status='reviewed' may be promoted"
            )
        reviewed_assets.append(deepcopy(asset))

    if not reviewed_assets and not allow_empty:
        raise ValueError(
            f"No reviewed assets were eligible for promotion in {reviewed_annotations}; "
            "complete at least one reviewed queue item before exporting a reviewed slice"
        )

    parent_assets = [asset for asset in reviewed_assets if asset.get("asset_role") == "parent_object"]
    child_assets = [asset for asset in reviewed_assets if asset.get("asset_role") == "child_object"]
    categories = sorted({str(asset["category"]) for asset in reviewed_assets})

    output_root = _replace_directory(output_dir)
    created_at_value = _timestamp(created_at)

    reviewed_slice_path = output_root / "reviewed_annotations_v0.json"
    parent_slice_path = output_root / "parent_object_annotations_v0.json"
    child_slice_path = output_root / "child_object_annotations_v0.json"
    manifest_path = output_root / "reviewed_slice_manifest.json"

    reviewed_slice = _filtered_annotation_set(
        source_payload=reviewed_payload,
        assets=reviewed_assets,
        annotation_set_id=f"{export_id}_reviewed",
        notes=(
            "Frozen reviewed-only object-semantics slice promoted from the processed AI2-THOR "
            "review workspace. Only assets with annotation review_status=reviewed and "
            "queue_status=reviewed are included."
        ),
    )
    parent_slice = _filtered_annotation_set(
        source_payload=reviewed_payload,
        assets=parent_assets,
        annotation_set_id=f"{export_id}_parents",
        notes="Parent-object subset of the frozen reviewed-only object-semantics slice.",
    )
    child_slice = _filtered_annotation_set(
        source_payload=reviewed_payload,
        assets=child_assets,
        annotation_set_id=f"{export_id}_children",
        notes="Child-object subset of the frozen reviewed-only object-semantics slice.",
    )

    write_object_semantics_annotation_set(reviewed_slice, reviewed_slice_path)
    write_object_semantics_annotation_set(parent_slice, parent_slice_path)
    write_object_semantics_annotation_set(child_slice, child_slice_path)

    manifest = {
        "export_id": export_id,
        "version": "object_semantics_reviewed_slice_v0",
        "created_at": created_at_value,
        "reviewed_annotation_source_ref": repo_relative_or_absolute(reviewed_annotations),
        "review_queue_source_ref": repo_relative_or_absolute(review_queue),
        "reviewed_slice_ref": repo_relative_or_absolute(reviewed_slice_path),
        "parent_slice_ref": repo_relative_or_absolute(parent_slice_path),
        "child_slice_ref": repo_relative_or_absolute(child_slice_path),
        "asset_count": len(reviewed_assets),
        "parent_asset_count": len(parent_assets),
        "child_asset_count": len(child_assets),
        "categories": categories,
        "notes": (
            "This frozen slice is intended for downstream consumers that must not read "
            "unreviewed AI2-THOR object-semantics candidates."
        ),
    }
    _write_json(manifest, manifest_path)

    return {
        "export_id": export_id,
        "output_dir": str(output_root),
        "reviewed_slice_path": str(reviewed_slice_path),
        "parent_slice_path": str(parent_slice_path),
        "child_slice_path": str(child_slice_path),
        "manifest_path": str(manifest_path),
        "asset_count": len(reviewed_assets),
        "parent_asset_count": len(parent_assets),
        "child_asset_count": len(child_assets),
        "categories": categories,
    }
