from __future__ import annotations

import json
from pathlib import Path

from vgm_assets.sources import register_ai2thor_object_semantics_selection


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_register_ai2thor_object_semantics_selection_stages_benchmark_slice(
    tmp_path: Path,
) -> None:
    raw_root = tmp_path / "raw"
    summary = register_ai2thor_object_semantics_selection(
        REPO_ROOT / "sources" / "ai2thor" / "object_semantics_selection_v0.json",
        raw_data_root=raw_root,
        acquired_by="pytest",
        acquired_at="2026-03-24T00:00:00+00:00",
    )

    assert summary["selection_id"] == "ai2thor_object_semantics_v0"
    assert summary["asset_count"] == 6

    slice_root = raw_root / "sources" / "ai2thor" / "object_semantics_v0"
    selection_manifest = json.loads((slice_root / "selection_manifest.json").read_text())
    assert selection_manifest["asset_count"] == 6

    bowl_raw_dir = slice_root / "bowl" / "ai2thor_bowl_01" / "raw"
    bowl_manifest = json.loads((bowl_raw_dir / "source_manifest.json").read_text())
    assert bowl_manifest["asset_role"] == "child_object"
    assert bowl_manifest["category"] == "bowl"
    assert bowl_manifest["raw_files"]["model"]["path"].endswith("source_model.fbx")
    assert "Bowl_Decals_1_AlbedoTransparency.png" in bowl_manifest["raw_material_files"]

    shelf_raw_dir = slice_root / "bookshelf" / "ai2thor_bookshelf_01" / "raw"
    shelf_manifest = json.loads((shelf_raw_dir / "source_manifest.json").read_text())
    assert shelf_manifest["asset_role"] == "parent_object"
    assert shelf_manifest["raw_files"]["prefab"]["path"].endswith("source_prefab.prefab")
    assert Path(shelf_raw_dir / "source_model.fbx").exists()
