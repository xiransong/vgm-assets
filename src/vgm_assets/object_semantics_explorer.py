from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
from typing import Any

from .ai2thor_review_workspace import (
    ai2thor_object_semantics_candidate_path,
    ai2thor_object_semantics_review_queue_path,
    ai2thor_object_semantics_reviewed_path,
    refresh_ai2thor_object_semantics_review_queue,
)
from .ai2thor_object_semantics import _measure_parent_prefab_bounds
from .object_semantics import (
    load_object_semantics_annotation_set,
    validate_object_semantics_annotation_set,
    validate_object_semantics_asset_record_data,
    write_object_semantics_annotation_set,
)
from .object_semantics_review_queue import validate_object_semantics_review_queue
from .protocol import load_json, repo_root
from .sources import _default_ai2thor_repo_root, load_selection_list
from .support_clutter import (
    _parse_game_object_file_id,
    _parse_scalar,
    _parse_unity_prefab_documents,
    _parse_vector3,
    _measure_prefab_bounds,
)

DEFAULT_CANDIDATE_ANNOTATIONS = (
    Path("catalogs") / "object_semantics_v0" / "ai2thor_candidate_annotations_v0.json"
)
DEFAULT_REVIEWED_ANNOTATIONS = (
    Path("catalogs") / "object_semantics_v0" / "ai2thor_reviewed_annotations_v0.json"
)
DEFAULT_REVIEW_QUEUE = Path("catalogs") / "object_semantics_v0" / "ai2thor_review_queue_v0.json"
DEFAULT_SELECTION_PATH = Path("sources") / "ai2thor" / "object_semantics_selection_v0.json"
DEFAULT_FRONTEND_DIST = Path("frontend_dist") / "object_semantics_explorer_v0"

_MESH_REF_RE = re.compile(
    r"^\s*m_Mesh:\s+\{fileID:\s*(?P<file_id>-?\d+),\s*guid:\s*(?P<guid>[0-9a-f]{32}),\s*type:\s*(?P<type>\d+)\}\s*$"
)
_VECTOR4_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z0-9_]+):\s+\{x:\s*(?P<x>[^,]+),\s*y:\s*(?P<y>[^,]+),\s*z:\s*(?P<z>[^,]+),\s*w:\s*(?P<w>[^}]+)\}\s*$"
)


@dataclass(frozen=True)
class ObjectSemanticsExplorerConfig:
    candidate_path: Path
    reviewed_path: Path
    review_queue_path: Path | None
    selection_path: Path
    source_repo_root: Path
    frontend_dist_path: Path


def default_object_semantics_explorer_config(
    *,
    candidate_path: Path | None = None,
    reviewed_path: Path | None = None,
    review_queue_path: Path | None = None,
    selection_path: Path | None = None,
    source_repo_root: Path | None = None,
    frontend_dist_path: Path | None = None,
) -> ObjectSemanticsExplorerConfig:
    root = repo_root()
    processed_candidate_path = ai2thor_object_semantics_candidate_path()
    processed_reviewed_path = ai2thor_object_semantics_reviewed_path()
    processed_review_queue_path = ai2thor_object_semantics_review_queue_path()
    default_candidate_path = (
        processed_candidate_path if processed_candidate_path.exists() else (root / DEFAULT_CANDIDATE_ANNOTATIONS)
    )
    default_reviewed_path = (
        processed_reviewed_path if processed_candidate_path.exists() else (root / DEFAULT_REVIEWED_ANNOTATIONS)
    )
    default_review_queue_path = (
        processed_review_queue_path if processed_candidate_path.exists() else (root / DEFAULT_REVIEW_QUEUE)
    )
    return ObjectSemanticsExplorerConfig(
        candidate_path=(candidate_path or default_candidate_path).resolve(),
        reviewed_path=(reviewed_path or default_reviewed_path).resolve(),
        review_queue_path=(review_queue_path or default_review_queue_path).resolve(),
        selection_path=(selection_path or (root / DEFAULT_SELECTION_PATH)).resolve(),
        source_repo_root=(source_repo_root or _default_ai2thor_repo_root()).resolve(),
        frontend_dist_path=(frontend_dist_path or (root / DEFAULT_FRONTEND_DIST)).resolve(),
    )


def _load_asset_map(payload: dict) -> dict[str, dict[str, Any]]:
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise TypeError("Object-semantics annotation payload must define an assets list")
    return {
        str(asset["asset_id"]): asset
        for asset in assets
        if isinstance(asset, dict) and isinstance(asset.get("asset_id"), str)
    }


def _load_selection_map(selection_path: Path) -> dict[str, dict[str, Any]]:
    return {
        str(entry["asset_id"]): entry
        for entry in load_selection_list(selection_path)
        if isinstance(entry.get("asset_id"), str)
    }


def _candidate_payload(config: ObjectSemanticsExplorerConfig) -> dict:
    return validate_object_semantics_annotation_set(config.candidate_path)


def _reviewed_payload(config: ObjectSemanticsExplorerConfig) -> dict | None:
    if not config.reviewed_path.exists():
        return None
    return validate_object_semantics_annotation_set(config.reviewed_path)


def _review_queue_payload(config: ObjectSemanticsExplorerConfig) -> dict | None:
    if config.review_queue_path is None or not config.review_queue_path.exists():
        return None
    return validate_object_semantics_review_queue(config.review_queue_path)


def _initial_reviewed_payload(candidate_payload: dict) -> dict:
    reviewed = deepcopy(candidate_payload)
    reviewed["annotation_set_id"] = f"{candidate_payload['annotation_set_id']}_reviewed"
    notes = candidate_payload.get("notes", "")
    reviewed["notes"] = (
        "Reviewed working copy derived from "
        f"{candidate_payload['annotation_set_id']}. {notes}".strip()
    )
    return reviewed


def _asset_ids_in_order(candidate_payload: dict) -> list[str]:
    return [str(asset["asset_id"]) for asset in candidate_payload.get("assets", [])]


def _review_queue_batches_by_asset(queue_payload: dict | None) -> tuple[dict[str, dict[str, Any]], list[str], list[dict[str, Any]]]:
    if queue_payload is None:
        return {}, [], []
    entries_by_asset: dict[str, dict[str, Any]] = {}
    ordered_asset_ids: list[str] = []
    batch_summaries: list[dict[str, Any]] = []
    for batch_index, batch in enumerate(queue_payload.get("batches", [])):
        if not isinstance(batch, dict):
            continue
        entries = batch.get("entries", [])
        reviewed_count = 0
        needs_fix_count = 0
        rejected_count = 0
        pending_count = 0
        for queue_index, entry in enumerate(entries):
            if not isinstance(entry, dict) or not isinstance(entry.get("asset_id"), str):
                continue
            asset_id = str(entry["asset_id"])
            ordered_asset_ids.append(asset_id)
            queue_status = str(entry.get("queue_status", "pending"))
            if queue_status == "reviewed":
                reviewed_count += 1
            elif queue_status == "needs_fix":
                needs_fix_count += 1
            elif queue_status == "rejected":
                rejected_count += 1
            else:
                pending_count += 1
            entries_by_asset[asset_id] = {
                "batch_id": str(batch.get("batch_id", "")),
                "batch_title": str(batch.get("title", "")),
                "batch_status": str(batch.get("status", "")),
                "batch_index": batch_index,
                "queue_index": queue_index,
                "queue_status": queue_status,
                "recommended_session_asset_count": batch.get("recommended_session_asset_count"),
            }
        batch_summaries.append(
            {
                "batch_id": str(batch.get("batch_id", "")),
                "title": str(batch.get("title", "")),
                "status": str(batch.get("status", "")),
                "asset_count": len(entries),
                "reviewed_count": reviewed_count,
                "needs_fix_count": needs_fix_count,
                "rejected_count": rejected_count,
                "pending_count": pending_count,
                "recommended_session_asset_count": batch.get("recommended_session_asset_count"),
            }
        )
    return entries_by_asset, ordered_asset_ids, batch_summaries


def get_object_semantics_review_queue(config: ObjectSemanticsExplorerConfig) -> dict[str, Any] | None:
    queue_payload = _review_queue_payload(config)
    if queue_payload is None:
        return None
    _, _, batch_summaries = _review_queue_batches_by_asset(queue_payload)
    return {
        "queue_id": queue_payload["queue_id"],
        "version": queue_payload["version"],
        "source_id": queue_payload["source_id"],
        "created_at": queue_payload["created_at"],
        "review_scope_v0": list(queue_payload.get("review_scope_v0", [])),
        "item_count": queue_payload["item_count"],
        "batch_count": queue_payload["batch_count"],
        "batches": batch_summaries,
    }


def _source_prefab_path(selection_entry: dict[str, Any], source_repo_root: Path) -> Path:
    source_prefab_rel = selection_entry.get("source_prefab_rel")
    if not isinstance(source_prefab_rel, str) or not source_prefab_rel.strip():
        raise ValueError(f"Selection entry for {selection_entry.get('asset_id')} has no source_prefab_rel")
    return (source_repo_root / source_prefab_rel).resolve()


def _parse_vector4(lines: list[str], key: str) -> tuple[float, float, float, float] | None:
    prefix = f"{key}:"
    for index, line in enumerate(lines):
        if not line.lstrip().startswith(prefix):
            continue
        candidate = line
        if index + 1 < len(lines) and "w:" not in candidate and lines[index + 1].lstrip().startswith("w:"):
            candidate = f"{candidate.strip()} {lines[index + 1].strip()}"
        match = _VECTOR4_RE.match(candidate)
        if match is None:
            raise ValueError(f"Malformed vector4 line for {key}: {candidate}")
        return (
            float(match.group("x")),
            float(match.group("y")),
            float(match.group("z")),
            float(match.group("w")),
        )
    return None


def _parse_mesh_ref(lines: list[str]) -> dict[str, str] | None:
    for line in lines:
        match = _MESH_REF_RE.match(line)
        if match is not None:
            return {
                "file_id": match.group("file_id"),
                "guid": match.group("guid"),
                "type": match.group("type"),
            }
    return None


@lru_cache(maxsize=2)
def _meta_path_by_guid(source_repo_root: Path) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for meta_path in source_repo_root.rglob("*.meta"):
        try:
            with meta_path.open("r", encoding="utf-8") as handle:
                first_lines = [next(handle).rstrip("\n") for _ in range(6)]
        except (OSError, StopIteration):
            try:
                text = meta_path.read_text(encoding="utf-8")
            except OSError:
                continue
            first_lines = text.splitlines()[:6]
        for line in first_lines:
            if not line.startswith("guid: "):
                continue
            guid = line.split(":", 1)[1].strip()
            if len(guid) == 32 and guid not in mapping:
                mapping[guid] = meta_path.resolve()
            break
    return mapping


@lru_cache(maxsize=32)
def _unity_meta_file_id_name_map(meta_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    in_table = False
    for raw_line in meta_path.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("  fileIDToRecycleName:"):
            in_table = True
            continue
        if not in_table:
            continue
        if not raw_line.startswith("    "):
            break
        line = raw_line.strip()
        if ":" not in line:
            continue
        file_id, name = line.split(":", 1)
        mapping[file_id.strip()] = name.strip()
    return mapping


def _extract_prefab_mesh_records(prefab_path: Path) -> list[dict[str, Any]]:
    documents = _parse_unity_prefab_documents(prefab_path)
    game_objects: dict[str, dict[str, Any]] = {}
    transforms: dict[str, dict[str, Any]] = {}
    mesh_filters: list[dict[str, Any]] = []

    for document in documents:
        lines = document["lines"]
        type_id = document["type_id"]
        file_id = document["file_id"]
        if type_id == 1:
            game_objects[file_id] = {
                "name": _parse_scalar(lines, "m_Name") or "",
                "active": (_parse_scalar(lines, "m_IsActive") or "1") == "1",
            }
        elif type_id == 4:
            game_object_id = _parse_game_object_file_id(lines)
            if game_object_id is None:
                continue
            transforms[game_object_id] = {
                "local_position": _parse_vector3(lines, "m_LocalPosition") or (0.0, 0.0, 0.0),
                "local_scale": _parse_vector3(lines, "m_LocalScale") or (1.0, 1.0, 1.0),
                "local_rotation": _parse_vector4(lines, "m_LocalRotation") or (0.0, 0.0, 0.0, 1.0),
            }
        elif type_id == 33:
            game_object_id = _parse_game_object_file_id(lines)
            mesh_ref = _parse_mesh_ref(lines)
            if game_object_id is None or mesh_ref is None:
                continue
            mesh_filters.append(
                {
                    "mesh_filter_file_id": file_id,
                    "game_object_id": game_object_id,
                    "mesh_ref": mesh_ref,
                }
            )

    records: list[dict[str, Any]] = []
    for mesh_filter in mesh_filters:
        game_object = game_objects.get(mesh_filter["game_object_id"], {"name": "", "active": True})
        transform = transforms.get(
            mesh_filter["game_object_id"],
            {
                "local_position": (0.0, 0.0, 0.0),
                "local_scale": (1.0, 1.0, 1.0),
                "local_rotation": (0.0, 0.0, 0.0, 1.0),
            },
        )
        records.append(
            {
                "game_object_name": game_object["name"],
                "game_object_id": mesh_filter["game_object_id"],
                "mesh_file_id": mesh_filter["mesh_ref"]["file_id"],
                "mesh_guid": mesh_filter["mesh_ref"]["guid"],
                "mesh_type": mesh_filter["mesh_ref"]["type"],
                "local_position": transform["local_position"],
                "local_scale": transform["local_scale"],
                "local_rotation": transform["local_rotation"],
                "active": bool(game_object["active"]),
            }
        )
    return records


def _review_mesh_payload_for_prefab(
    *,
    prefab_path: Path,
    source_repo_root: Path,
    asset_id: str,
) -> dict[str, Any] | None:
    mesh_records = [record for record in _extract_prefab_mesh_records(prefab_path) if record["active"]]
    if not mesh_records:
        return None

    guid_to_meta_path = _meta_path_by_guid(source_repo_root)
    instances: list[dict[str, Any]] = []
    model_pack_path: Path | None = None

    for record in mesh_records:
        meta_path = guid_to_meta_path.get(record["mesh_guid"])
        if meta_path is None:
            continue
        file_id_name_map = _unity_meta_file_id_name_map(meta_path)
        mesh_name = file_id_name_map.get(record["mesh_file_id"])
        if not mesh_name:
            continue
        pack_path = meta_path.with_suffix("")
        if not pack_path.exists():
            continue
        if model_pack_path is None:
            model_pack_path = pack_path
        elif model_pack_path != pack_path:
            return None
        instances.append(
            {
                "mesh_name": mesh_name,
                "mesh_file_id": record["mesh_file_id"],
                "game_object_name": record["game_object_name"],
                "local_position_m": {
                    "x": round(record["local_position"][0], 6),
                    "y": round(record["local_position"][1], 6),
                    "z": round(record["local_position"][2], 6),
                },
                "local_scale": {
                    "x": round(record["local_scale"][0], 6),
                    "y": round(record["local_scale"][1], 6),
                    "z": round(record["local_scale"][2], 6),
                },
                "local_rotation_xyzw": {
                    "x": round(record["local_rotation"][0], 6),
                    "y": round(record["local_rotation"][1], 6),
                    "z": round(record["local_rotation"][2], 6),
                    "w": round(record["local_rotation"][3], 6),
                },
            }
        )

    if model_pack_path is None or not instances:
        return None
    return {
        "format": model_pack_path.suffix.lstrip(".") or "bin",
        "path": str(model_pack_path),
        "url": f"/api/object-semantics/assets/{asset_id}/source-file/review-mesh",
        "mesh_instances": instances,
        "note": "Explorer v0 loads the grouped AI2-THOR source asset and keeps only the mesh nodes referenced by the prefab.",
    }


def _model_pack_path_for_prefab(prefab_path: Path) -> Path | None:
    seen: set[Path] = set()
    for ancestor in prefab_path.parents:
        models_dir = ancestor / "Models"
        if not models_dir.is_dir():
            continue
        fbx_files = sorted(models_dir.glob("*.fbx"))
        for path in fbx_files:
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                return resolved
    return None


def _preview_path_for_prefab(prefab_path: Path) -> Path | None:
    preview_candidates: list[Path] = []
    for ancestor in prefab_path.parents:
        for extension in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            preview_candidates.extend(sorted(ancestor.glob(extension)))
        if preview_candidates:
            break
    return preview_candidates[0].resolve() if preview_candidates else None


def _proxy_bounds_for_selection_entry(
    *,
    selection_entry: dict[str, Any],
    prefab_path: Path,
) -> dict[str, Any]:
    asset_role = selection_entry.get("asset_role")
    if asset_role == "parent_object":
        return _measure_parent_prefab_bounds(prefab_path)
    if asset_role == "child_object":
        return _measure_prefab_bounds(prefab_path)
    raise ValueError(f"Unsupported asset_role {asset_role!r} for {selection_entry.get('asset_id')}")


def _canonical_bounds_for_selection_entry(
    *,
    selection_entry: dict[str, Any],
    prefab_path: Path,
) -> dict[str, Any]:
    bounds = deepcopy(
        _proxy_bounds_for_selection_entry(
            selection_entry=selection_entry,
            prefab_path=prefab_path,
        )
    )
    bounds["normalization_source"] = "ai2thor_prefab_collider"
    bounds["review_display_source"] = "canonical"
    bounds["notes"] = (
        "Explorer v0 treats AI2-THOR prefab collider bounds as the canonical metric size for "
        "review and review-mesh fitting."
    )
    return bounds


def _source_refs_for_selection_entry(
    *,
    asset_id: str,
    selection_entry: dict[str, Any],
    source_repo_root: Path,
) -> dict[str, Any]:
    prefab_path = _source_prefab_path(selection_entry, source_repo_root)
    model_pack_path = _model_pack_path_for_prefab(prefab_path)
    preview_path = _preview_path_for_prefab(prefab_path)
    review_mesh = _review_mesh_payload_for_prefab(
        prefab_path=prefab_path,
        source_repo_root=source_repo_root,
        asset_id=asset_id,
    )

    refs: dict[str, Any] = {
        "prefab": {
            "path": str(prefab_path),
            "format": prefab_path.suffix.lstrip(".") or "prefab",
            "exists": prefab_path.exists(),
            "url": f"/api/object-semantics/assets/{asset_id}/source-file/prefab",
        },
        "mesh": None,
        "model_pack": None,
        "preview": None,
        "review_mesh": review_mesh,
    }
    if model_pack_path is not None:
        refs["model_pack"] = {
            "path": str(model_pack_path),
            "format": model_pack_path.suffix.lstrip(".") or "bin",
            "exists": model_pack_path.exists(),
            "url": f"/api/object-semantics/assets/{asset_id}/source-file/model-pack",
            "note": "AI2-THOR model pack files usually contain grouped assets, so they are not treated as exact per-asset meshes in Explorer v0.",
        }
    if preview_path is not None:
        refs["preview"] = {
            "path": str(preview_path),
            "format": preview_path.suffix.lstrip(".") or "bin",
            "exists": preview_path.exists(),
            "url": f"/api/object-semantics/assets/{asset_id}/source-file/preview",
        }
    return refs


def list_object_semantics_assets(config: ObjectSemanticsExplorerConfig) -> list[dict[str, Any]]:
    candidate_payload = _candidate_payload(config)
    reviewed_payload = _reviewed_payload(config)
    queue_payload = _review_queue_payload(config)
    candidate_map = _load_asset_map(candidate_payload)
    reviewed_map = _load_asset_map(reviewed_payload) if reviewed_payload is not None else {}
    selection_map = _load_selection_map(config.selection_path)
    queue_entries_by_asset, ordered_asset_ids, _ = _review_queue_batches_by_asset(queue_payload)
    asset_ids = ordered_asset_ids or _asset_ids_in_order(candidate_payload)

    summaries: list[dict[str, Any]] = []
    for asset_id in asset_ids:
        candidate_asset = candidate_map[asset_id]
        current_asset = reviewed_map.get(asset_id, candidate_asset)
        selection_entry = selection_map.get(asset_id, {})
        source_refs = _source_refs_for_selection_entry(
            asset_id=asset_id,
            selection_entry=selection_entry,
            source_repo_root=config.source_repo_root,
        )
        queue_entry = queue_entries_by_asset.get(asset_id, {})
        summaries.append(
            {
                "asset_id": asset_id,
                "display_name": selection_entry.get("display_name", asset_id),
                "asset_role": current_asset["asset_role"],
                "category": current_asset["category"],
                "review_status": current_asset["review_status"],
                "has_reviewed_override": asset_id in reviewed_map,
                "has_preview": source_refs["preview"] is not None,
                "has_model_pack": source_refs["model_pack"] is not None,
                "has_review_mesh": source_refs["review_mesh"] is not None,
                "queue_status": queue_entry.get("queue_status", "pending"),
                "batch_id": queue_entry.get("batch_id"),
                "batch_title": queue_entry.get("batch_title"),
                "batch_status": queue_entry.get("batch_status"),
                "batch_index": queue_entry.get("batch_index"),
                "queue_index": queue_entry.get("queue_index"),
            }
        )
    return summaries


def get_object_semantics_asset_detail(
    config: ObjectSemanticsExplorerConfig,
    asset_id: str,
) -> dict[str, Any]:
    candidate_payload = _candidate_payload(config)
    reviewed_payload = _reviewed_payload(config)
    queue_payload = _review_queue_payload(config)
    candidate_map = _load_asset_map(candidate_payload)
    reviewed_map = _load_asset_map(reviewed_payload) if reviewed_payload is not None else {}
    selection_map = _load_selection_map(config.selection_path)
    queue_entries_by_asset, _, batch_summaries = _review_queue_batches_by_asset(queue_payload)

    if asset_id not in candidate_map:
        raise KeyError(f"Unknown object-semantics asset_id: {asset_id}")
    if asset_id not in selection_map:
        raise KeyError(f"Missing selection metadata for asset_id: {asset_id}")

    candidate_asset = deepcopy(candidate_map[asset_id])
    current_asset = deepcopy(reviewed_map.get(asset_id, candidate_asset))
    selection_entry = deepcopy(selection_map[asset_id])
    prefab_path = _source_prefab_path(selection_entry, config.source_repo_root)

    return {
        "asset": current_asset,
        "candidate_asset": candidate_asset,
        "current_source": "reviewed" if asset_id in reviewed_map else "candidate",
        "queue_entry": queue_entries_by_asset.get(asset_id),
        "review_queue": get_object_semantics_review_queue(config),
        "batch_summary": next(
            (
                batch
                for batch in batch_summaries
                if batch["batch_id"] == queue_entries_by_asset.get(asset_id, {}).get("batch_id")
            ),
            None,
        ),
        "source_record": selection_entry,
        "source_refs": _source_refs_for_selection_entry(
            asset_id=asset_id,
            selection_entry=selection_entry,
            source_repo_root=config.source_repo_root,
        ),
        "canonical_bounds": _canonical_bounds_for_selection_entry(
            selection_entry=selection_entry,
            prefab_path=prefab_path,
        ),
        "proxy_bounds": _proxy_bounds_for_selection_entry(
            selection_entry=selection_entry,
            prefab_path=prefab_path,
        ),
    }


def save_reviewed_object_semantics_asset(
    config: ObjectSemanticsExplorerConfig,
    asset_id: str,
    asset_payload: dict[str, Any],
) -> dict[str, Any]:
    if asset_payload.get("asset_id") != asset_id:
        raise ValueError(
            f"Posted asset payload asset_id {asset_payload.get('asset_id')!r} does not match {asset_id!r}"
        )
    validated_asset = validate_object_semantics_asset_record_data(asset_payload)

    candidate_payload = _candidate_payload(config)
    if asset_id not in _load_asset_map(candidate_payload):
        raise KeyError(f"Unknown object-semantics asset_id: {asset_id}")

    reviewed_payload = _reviewed_payload(config)
    if reviewed_payload is None:
        reviewed_payload = _initial_reviewed_payload(candidate_payload)

    ordered_assets: list[dict[str, Any]] = []
    for candidate_asset in candidate_payload.get("assets", []):
        if not isinstance(candidate_asset, dict):
            continue
        if candidate_asset.get("asset_id") == asset_id:
            ordered_assets.append(deepcopy(validated_asset))
            continue
        existing = next(
            (
                reviewed_asset
                for reviewed_asset in reviewed_payload.get("assets", [])
                if isinstance(reviewed_asset, dict)
                and reviewed_asset.get("asset_id") == candidate_asset.get("asset_id")
            ),
            None,
        )
        ordered_assets.append(deepcopy(existing or candidate_asset))

    reviewed_payload["assets"] = ordered_assets
    write_object_semantics_annotation_set(reviewed_payload, config.reviewed_path)
    if config.review_queue_path is not None:
        refresh_ai2thor_object_semantics_review_queue(
            candidate_path=config.candidate_path,
            reviewed_path=config.reviewed_path,
            queue_path=config.review_queue_path,
            data_root=None,
        )
    return get_object_semantics_asset_detail(config, asset_id)


def source_file_path_for_asset(
    config: ObjectSemanticsExplorerConfig,
    asset_id: str,
    kind: str,
) -> Path:
    selection_map = _load_selection_map(config.selection_path)
    if asset_id not in selection_map:
        raise KeyError(f"Missing selection metadata for asset_id: {asset_id}")
    selection_entry = selection_map[asset_id]
    prefab_path = _source_prefab_path(selection_entry, config.source_repo_root)

    if kind == "prefab":
        return prefab_path
    if kind == "review-mesh":
        review_mesh = _review_mesh_payload_for_prefab(
            prefab_path=prefab_path,
            source_repo_root=config.source_repo_root,
            asset_id=asset_id,
        )
        if review_mesh is None:
            raise FileNotFoundError(f"No review-mesh source file could be resolved for {asset_id}")
        return Path(str(review_mesh["path"]))
    if kind == "model-pack":
        model_pack_path = _model_pack_path_for_prefab(prefab_path)
        if model_pack_path is None:
            raise FileNotFoundError(f"No model-pack file could be resolved for {asset_id}")
        return model_pack_path
    if kind == "preview":
        preview_path = _preview_path_for_prefab(prefab_path)
        if preview_path is None:
            raise FileNotFoundError(f"No preview file could be resolved for {asset_id}")
        return preview_path
    raise ValueError(f"Unsupported source-file kind: {kind}")


def load_object_semantics_schema() -> dict[str, Any]:
    return load_json(repo_root() / "schemas" / "local" / "object_semantics_annotation_set_v0.schema.json")
