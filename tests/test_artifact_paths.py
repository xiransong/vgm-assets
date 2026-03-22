from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path

from vgm_assets.sampling import build_category_index


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_build_category_index_uses_repo_relative_catalog_path(tmp_path: Path) -> None:
    catalog_path = REPO_ROOT / "cache" / f"{tmp_path.name}_portable_category_index_catalog.json"
    payload = [
        {
            "asset_id": "portable_asset_01",
            "category": "chair",
        }
    ]
    try:
        catalog_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        index = build_category_index(catalog_path)

        assert index["catalog_path"] == f"cache/{catalog_path.name}"
    finally:
        catalog_path.unlink(missing_ok=True)


def test_measure_catalog_meshes_uses_portable_paths(
    tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "data_root"
    mesh_path = data_root / "meshes" / "chair.glb"
    mesh_path.parent.mkdir(parents=True, exist_ok=True)
    mesh_path.write_text("fake mesh", encoding="utf-8")

    catalog_path = REPO_ROOT / "cache" / f"{tmp_path.name}_portable_measure_catalog.json"
    try:
        catalog_path.write_text(
            json.dumps(
                [
                    {
                        "asset_id": "portable_asset_01",
                        "category": "chair",
                        "files": {
                            "mesh": {
                                "path": "meshes/chair.glb",
                                "format": "glb",
                            }
                        }
                    },
                ],
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("VGM_ASSETS_DATA_ROOT", str(data_root))
        monkeypatch.setitem(
            sys.modules,
            "trimesh",
            types.SimpleNamespace(load=lambda *args, **kwargs: None),
        )

        measure_module = importlib.import_module("vgm_assets.measure")
        original = measure_module._scene_bounds
        measure_module._scene_bounds = lambda _: ([0.0, 0.0, 0.0], [1.0, 2.0, 3.0])
        try:
            report = measure_module.measure_catalog_meshes(catalog_path)
        finally:
            measure_module._scene_bounds = original
    finally:
        catalog_path.unlink(missing_ok=True)

    assert report["catalog_path"] == f"cache/{catalog_path.name}"
    assert report["asset_count"] == 1
    assert report["measured_asset_count"] == 1
    assert report["skipped_asset_count"] == 0
    assert report["measurements"][0]["mesh_path"] == "meshes/chair.glb"


def test_measure_catalog_meshes_skips_meshless_assets_by_default(
    tmp_path: Path, monkeypatch
) -> None:
    catalog_path = REPO_ROOT / "cache" / f"{tmp_path.name}_meshless_measure_catalog.json"
    try:
        catalog_path.write_text(
            json.dumps(
                [
                    {
                        "asset_id": "mesh_asset_01",
                        "category": "chair",
                        "files": {"mesh": {"path": "meshes/chair.glb", "format": "glb"}},
                    },
                    {
                        "asset_id": "meshless_asset_01",
                        "category": "sofa",
                    },
                ],
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setitem(
            sys.modules,
            "trimesh",
            types.SimpleNamespace(load=lambda *args, **kwargs: None),
        )

        measure_module = importlib.import_module("vgm_assets.measure")
        original = measure_module._scene_bounds
        measure_module._scene_bounds = lambda _: ([0.0, 0.0, 0.0], [1.0, 2.0, 3.0])
        try:
            report = measure_module.measure_catalog_meshes(catalog_path)
        finally:
            measure_module._scene_bounds = original
    finally:
        catalog_path.unlink(missing_ok=True)

    assert report["asset_count"] == 2
    assert report["measured_asset_count"] == 1
    assert report["skipped_asset_count"] == 1
    assert report["skipped_assets"] == [
        {
            "asset_id": "meshless_asset_01",
            "category": "sofa",
            "reason": "missing_files_mesh",
        }
    ]


def test_measure_catalog_meshes_can_require_mesh_for_all(
    tmp_path: Path, monkeypatch
) -> None:
    import pytest

    catalog_path = REPO_ROOT / "cache" / f"{tmp_path.name}_strict_measure_catalog.json"
    try:
        catalog_path.write_text(
            json.dumps(
                [
                    {
                        "asset_id": "meshless_asset_01",
                        "category": "sofa",
                    }
                ],
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setitem(
            sys.modules,
            "trimesh",
            types.SimpleNamespace(load=lambda *args, **kwargs: None),
        )

        measure_module = importlib.import_module("vgm_assets.measure")
        with pytest.raises(ValueError, match="has no files.mesh ref"):
            measure_module.measure_catalog_meshes(
                catalog_path,
                require_mesh_for_all=True,
            )
    finally:
        catalog_path.unlink(missing_ok=True)
