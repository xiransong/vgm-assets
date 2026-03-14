from __future__ import annotations

from pathlib import Path

import trimesh

from .catalog import load_asset_specs


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

    mesh_path = Path(mesh_ref["path"]).expanduser().resolve()
    mins, maxs = _scene_bounds(mesh_path)
    extents = [maxs[i] - mins[i] for i in range(3)]

    return {
        "asset_id": asset["asset_id"],
        "category": asset["category"],
        "mesh_path": str(mesh_path),
        "bounds_min": {"x": mins[0], "y": mins[1], "z": mins[2]},
        "bounds_max": {"x": maxs[0], "y": maxs[1], "z": maxs[2]},
        "extents": {
            "x": extents[0],
            "y": extents[1],
            "z": extents[2],
        },
        "current_dimensions": asset.get("dimensions"),
    }


def measure_catalog_meshes(catalog_path: Path) -> dict:
    assets = load_asset_specs(catalog_path)
    measurements = [_measurement_for_asset(asset) for asset in assets]
    return {
        "catalog_path": str(catalog_path.resolve()),
        "asset_count": len(measurements),
        "measurements": measurements,
    }
