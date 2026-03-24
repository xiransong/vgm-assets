from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ai2thor_object_semantics import _measure_parent_prefab_bounds
from .object_semantics import (
    load_object_semantics_annotation_set,
    validate_object_semantics_annotation_set,
    validate_object_semantics_asset_record_data,
    write_object_semantics_annotation_set,
)
from .protocol import load_json, repo_root
from .sources import _default_ai2thor_repo_root, load_selection_list
from .support_clutter import _measure_prefab_bounds

DEFAULT_CANDIDATE_ANNOTATIONS = (
    Path("catalogs") / "object_semantics_v0" / "ai2thor_candidate_annotations_v0.json"
)
DEFAULT_REVIEWED_ANNOTATIONS = (
    Path("catalogs") / "object_semantics_v0" / "ai2thor_reviewed_annotations_v0.json"
)
DEFAULT_SELECTION_PATH = Path("sources") / "ai2thor" / "object_semantics_selection_v0.json"
DEFAULT_FRONTEND_DIST = Path("frontend_dist") / "object_semantics_explorer_v0"


@dataclass(frozen=True)
class ObjectSemanticsExplorerConfig:
    candidate_path: Path
    reviewed_path: Path
    selection_path: Path
    source_repo_root: Path
    frontend_dist_path: Path


def default_object_semantics_explorer_config(
    *,
    candidate_path: Path | None = None,
    reviewed_path: Path | None = None,
    selection_path: Path | None = None,
    source_repo_root: Path | None = None,
    frontend_dist_path: Path | None = None,
) -> ObjectSemanticsExplorerConfig:
    root = repo_root()
    return ObjectSemanticsExplorerConfig(
        candidate_path=(candidate_path or (root / DEFAULT_CANDIDATE_ANNOTATIONS)).resolve(),
        reviewed_path=(reviewed_path or (root / DEFAULT_REVIEWED_ANNOTATIONS)).resolve(),
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


def _source_prefab_path(selection_entry: dict[str, Any], source_repo_root: Path) -> Path:
    source_prefab_rel = selection_entry.get("source_prefab_rel")
    if not isinstance(source_prefab_rel, str) or not source_prefab_rel.strip():
        raise ValueError(f"Selection entry for {selection_entry.get('asset_id')} has no source_prefab_rel")
    return (source_repo_root / source_prefab_rel).resolve()


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


def _source_refs_for_selection_entry(
    *,
    asset_id: str,
    selection_entry: dict[str, Any],
    source_repo_root: Path,
) -> dict[str, Any]:
    prefab_path = _source_prefab_path(selection_entry, source_repo_root)
    model_pack_path = _model_pack_path_for_prefab(prefab_path)
    preview_path = _preview_path_for_prefab(prefab_path)

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
    candidate_map = _load_asset_map(candidate_payload)
    reviewed_map = _load_asset_map(reviewed_payload) if reviewed_payload is not None else {}
    selection_map = _load_selection_map(config.selection_path)

    summaries: list[dict[str, Any]] = []
    for asset_id in _asset_ids_in_order(candidate_payload):
        candidate_asset = candidate_map[asset_id]
        current_asset = reviewed_map.get(asset_id, candidate_asset)
        selection_entry = selection_map.get(asset_id, {})
        source_refs = _source_refs_for_selection_entry(
            asset_id=asset_id,
            selection_entry=selection_entry,
            source_repo_root=config.source_repo_root,
        )
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
            }
        )
    return summaries


def get_object_semantics_asset_detail(
    config: ObjectSemanticsExplorerConfig,
    asset_id: str,
) -> dict[str, Any]:
    candidate_payload = _candidate_payload(config)
    reviewed_payload = _reviewed_payload(config)
    candidate_map = _load_asset_map(candidate_payload)
    reviewed_map = _load_asset_map(reviewed_payload) if reviewed_payload is not None else {}
    selection_map = _load_selection_map(config.selection_path)

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
        "source_record": selection_entry,
        "source_refs": _source_refs_for_selection_entry(
            asset_id=asset_id,
            selection_entry=selection_entry,
            source_repo_root=config.source_repo_root,
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
