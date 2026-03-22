from __future__ import annotations

from pathlib import Path
from typing import Any

import trimesh

from .catalog import load_asset_specs
from .paths import data_root_relative_or_absolute, repo_relative_or_absolute, resolve_data_ref


def _scene_bounds(mesh_path: Path) -> tuple[list[float], list[float]]:
    loaded = trimesh.load(mesh_path, force="scene")
    bounds = loaded.bounds
    if bounds is None:
        raise ValueError(f"Mesh at {mesh_path} has no bounds")
    mins = [float(v) for v in bounds[0]]
    maxs = [float(v) for v in bounds[1]]
    return mins, maxs


def _measurement_for_asset(asset: dict) -> dict:
    files = asset.get("files") or {}
    mesh_ref = files.get("mesh")
    if not isinstance(mesh_ref, dict):
        raise ValueError(f"Asset {asset.get('asset_id')} has no files.mesh ref")
    mesh_path_value = mesh_ref.get("path")
    if not isinstance(mesh_path_value, str) or not mesh_path_value:
        raise ValueError(f"Asset {asset.get('asset_id')} has an invalid files.mesh.path")

    mesh_path = resolve_data_ref(mesh_path_value)
    mins, maxs = _scene_bounds(mesh_path)
    extents = [maxs[i] - mins[i] for i in range(3)]

    return {
        "asset_id": asset["asset_id"],
        "category": asset["category"],
        "mesh_path": data_root_relative_or_absolute(mesh_path),
        "bounds_min": {"x": mins[0], "y": mins[1], "z": mins[2]},
        "bounds_max": {"x": maxs[0], "y": maxs[1], "z": maxs[2]},
        "extents": {
            "x": extents[0],
            "y": extents[1],
            "z": extents[2],
        },
        "current_dimensions": asset.get("dimensions"),
    }


def _skipped_asset(asset: dict[str, Any], reason: str) -> dict[str, Any]:
    skipped = {
        "asset_id": asset.get("asset_id"),
        "category": asset.get("category"),
        "reason": reason,
    }
    return skipped


def measure_catalog_meshes(
    catalog_path: Path,
    *,
    require_mesh_for_all: bool = False,
) -> dict:
    assets = load_asset_specs(catalog_path)
    measurements: list[dict] = []
    skipped_assets: list[dict[str, Any]] = []
    for asset in assets:
        files = asset.get("files") or {}
        if not isinstance(files.get("mesh"), dict):
            if require_mesh_for_all:
                raise ValueError(f"Asset {asset.get('asset_id')} has no files.mesh ref")
            skipped_assets.append(_skipped_asset(asset, "missing_files_mesh"))
            continue
        measurements.append(_measurement_for_asset(asset))
    return {
        "catalog_path": repo_relative_or_absolute(catalog_path),
        "asset_count": len(assets),
        "measured_asset_count": len(measurements),
        "skipped_asset_count": len(skipped_assets),
        "measurements": measurements,
        "skipped_assets": skipped_assets,
    }
