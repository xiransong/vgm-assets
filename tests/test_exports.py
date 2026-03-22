from __future__ import annotations

import json
from pathlib import Path

from vgm_assets.exports import export_scene_engine_snapshot


REPO_ROOT = Path(__file__).resolve().parents[1]


def _seed_asset_record() -> dict:
    catalog_path = REPO_ROOT / "catalogs" / "living_room_kenney_v0" / "assets.json"
    record = json.loads(catalog_path.read_text(encoding="utf-8"))[0]
    return json.loads(json.dumps(record))


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_export_inputs(tmp_path: Path) -> tuple[Path, Path, Path, dict]:
    data_root = tmp_path / "data_root"
    asset_dir = data_root / "fake" / "asset1"
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / "model.glb").write_text("mesh1", encoding="utf-8")
    (asset_dir / "preview.png").write_text("preview1", encoding="utf-8")

    record = _seed_asset_record()
    record["files"]["mesh"]["path"] = "fake/asset1/model.glb"
    record["files"]["preview_image"]["path"] = "fake/asset1/preview.png"

    catalog_path = _write_json(tmp_path / "inputs" / "assets.json", [record])
    category_index_path = _write_json(
        tmp_path / "inputs" / "category_index.json",
        {
            "catalog_path": str(catalog_path.resolve()),
            "category_count": 1,
            "categories": {
                record["category"]: {
                    "sampling_policy": "uniform",
                    "asset_count": 1,
                    "asset_ids": [record["asset_id"]],
                }
            },
        },
    )
    manifest_path = _write_json(
        tmp_path / "inputs" / "asset_catalog_manifest.json",
        {
            "catalog_id": "source_catalog",
            "asset_count": 1,
            "catalog_files": [{"path": str(catalog_path.resolve()), "format": "json"}],
            "protocol_version": "v0",
            "producer": {"repo": "test", "version": "0", "commit": "test"},
            "created_at": "2026-03-22T00:00:00+00:00",
        },
    )
    return catalog_path, category_index_path, manifest_path, record


def test_export_scene_engine_snapshot_supports_output_outside_repo(
    tmp_path: Path, monkeypatch
) -> None:
    catalog_path, category_index_path, manifest_path, _ = _write_export_inputs(tmp_path)
    monkeypatch.setenv("VGM_ASSETS_DATA_ROOT", str(tmp_path / "data_root"))

    output_dir = tmp_path / "external_output"
    result = export_scene_engine_snapshot(
        export_id="test_export_outside_repo",
        source_catalog_id="source_catalog",
        catalog_path=catalog_path,
        category_index_path=category_index_path,
        manifest_path=manifest_path,
        output_dir=output_dir,
    )

    export_metadata = json.loads((output_dir / "export_metadata.json").read_text(encoding="utf-8"))
    assert result["output_dir"] == str(output_dir.resolve())
    assert (output_dir / "asset_catalog.json").exists()
    assert export_metadata["source_artifacts"]["asset_catalog"]["path"] == str(
        catalog_path.resolve()
    )
    assert export_metadata["source_artifacts"]["category_index"]["path"] == str(
        category_index_path.resolve()
    )


def test_export_scene_engine_snapshot_replaces_existing_payload_snapshot(
    tmp_path: Path, monkeypatch
) -> None:
    catalog_path, category_index_path, manifest_path, record = _write_export_inputs(tmp_path)
    monkeypatch.setenv("VGM_ASSETS_DATA_ROOT", str(tmp_path / "data_root"))

    output_dir = tmp_path / "external_output"
    export_id = "test_export_rerun"

    export_scene_engine_snapshot(
        export_id=export_id,
        source_catalog_id="source_catalog",
        catalog_path=catalog_path,
        category_index_path=category_index_path,
        manifest_path=manifest_path,
        output_dir=output_dir,
    )

    empty_catalog_path = _write_json(tmp_path / "inputs" / "assets_empty.json", [])
    result = export_scene_engine_snapshot(
        export_id=export_id,
        source_catalog_id="source_catalog",
        catalog_path=empty_catalog_path,
        category_index_path=category_index_path,
        manifest_path=manifest_path,
        output_dir=output_dir,
    )

    stale_payload = (
        tmp_path
        / "data_root"
        / "exports"
        / "scene_engine"
        / export_id
        / "assets"
        / record["category"]
        / record["asset_id"]
        / "model.glb"
    )
    exported_catalog = json.loads((output_dir / "asset_catalog.json").read_text(encoding="utf-8"))

    assert result["payload_file_count"] == 0
    assert exported_catalog == []
    assert not stale_payload.exists()
