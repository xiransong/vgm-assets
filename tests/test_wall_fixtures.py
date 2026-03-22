from __future__ import annotations

import json
from pathlib import Path

from vgm_assets.exports import export_wall_fixture_snapshot
from vgm_assets.wall_fixtures import refresh_wall_fixture_catalog


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _write_bundle_manifest(
    *,
    data_root: Path,
    fixture_id: str,
    category: str,
    selection_id: str,
) -> Path:
    bundle_dir = (
        data_root / "sources" / "kenney" / "wall_fixtures_v0" / category / fixture_id
    )
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "model.glb").write_text(f"mesh:{fixture_id}", encoding="utf-8")
    (bundle_dir / "preview.png").write_text(f"preview:{fixture_id}", encoding="utf-8")

    normalized_rel_dir = bundle_dir.relative_to(data_root).as_posix()
    bundle_manifest_path = bundle_dir / "bundle_manifest.json"
    _write_json(
        bundle_manifest_path,
        {
            "selection_id": selection_id,
            "fixture_id": fixture_id,
            "category": category,
            "display_name": fixture_id.replace("_", " ").title(),
            "dimensions": {
                "width_m": 0.8,
                "height_m": 0.5,
                "depth_m": 0.04,
            },
            "mount": {
                "mount_type": "wall_mounted",
                "mount_plane": "vertical_wall",
                "usable_margin_m": 0.05,
            },
            "files": {
                "mesh": {
                    "path": f"{normalized_rel_dir}/model.glb",
                    "format": "glb",
                },
                "preview_image": {
                    "path": f"{normalized_rel_dir}/preview.png",
                    "format": "png",
                },
            },
            "normalized_rel_dir": normalized_rel_dir,
            "source": "kenney",
            "style_tags": ["starter"],
            "preferred_room_types": ["living_room"],
            "review_status": "approved",
            "license": "CC0",
        },
    )
    _write_json(
        bundle_dir / "source_metadata.json",
        {
            "source_url": f"https://example.com/{fixture_id}",
        },
    )
    return bundle_manifest_path


def test_refresh_wall_fixture_catalog_writes_catalog_index_and_manifest(
    tmp_path: Path,
) -> None:
    data_root = tmp_path / "data_root"
    bundle_manifest_path = _write_bundle_manifest(
        data_root=data_root,
        fixture_id="painting_frame_01",
        category="painting",
        selection_id="kenney.painting_frame_01",
    )

    catalog_path = tmp_path / "catalogs" / "wall_fixtures_v0" / "wall_fixture_catalog.json"
    fixture_category_index_path = (
        tmp_path / "catalogs" / "wall_fixtures_v0" / "fixture_category_index.json"
    )
    manifest_path = tmp_path / "catalogs" / "wall_fixtures_v0" / "fixture_catalog_manifest.json"

    summary = refresh_wall_fixture_catalog(
        catalog_id="wall_fixtures_v0",
        bundle_manifest_paths=[bundle_manifest_path],
        catalog_output=catalog_path,
        fixture_category_index_output=fixture_category_index_path,
        manifest_output=manifest_path,
        created_at="2026-03-22T00:00:00+00:00",
    )

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    fixture_category_index = json.loads(
        fixture_category_index_path.read_text(encoding="utf-8")
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert summary["catalog_id"] == "wall_fixtures_v0"
    assert summary["fixture_count"] == 1
    assert summary["category_count"] == 1
    assert catalog[0]["fixture_id"] == "painting_frame_01"
    assert catalog[0]["source_url"] == "https://example.com/painting_frame_01"
    assert fixture_category_index["categories"]["painting"]["fixture_ids"] == [
        "painting_frame_01"
    ]
    assert manifest["catalog_id"] == "wall_fixtures_v0"
    assert manifest["fixture_count"] == 1


def test_export_wall_fixture_snapshot_replaces_existing_payload_snapshot(
    tmp_path: Path, monkeypatch
) -> None:
    data_root = tmp_path / "data_root"
    monkeypatch.setenv("VGM_ASSETS_DATA_ROOT", str(data_root))

    input_dir = tmp_path / "inputs"
    bundle_manifest_path = _write_bundle_manifest(
        data_root=data_root,
        fixture_id="painting_frame_01",
        category="painting",
        selection_id="kenney.painting_frame_01",
    )
    catalog_path = input_dir / "wall_fixture_catalog.json"
    fixture_category_index_path = input_dir / "fixture_category_index.json"
    manifest_path = input_dir / "fixture_catalog_manifest.json"

    refresh_wall_fixture_catalog(
        catalog_id="wall_fixtures_v0",
        bundle_manifest_paths=[bundle_manifest_path],
        catalog_output=catalog_path,
        fixture_category_index_output=fixture_category_index_path,
        manifest_output=manifest_path,
        created_at="2026-03-22T00:00:00+00:00",
    )

    output_dir = tmp_path / "export"
    export_id = "wall_fixtures_v0_r1"
    result = export_wall_fixture_snapshot(
        export_id=export_id,
        source_catalog_id="wall_fixtures_v0",
        catalog_path=catalog_path,
        fixture_category_index_path=fixture_category_index_path,
        manifest_path=manifest_path,
        output_dir=output_dir,
    )

    exported_catalog = json.loads(
        (output_dir / "wall_fixture_catalog.json").read_text(encoding="utf-8")
    )
    export_metadata = json.loads(
        (output_dir / "export_metadata.json").read_text(encoding="utf-8")
    )
    exported_mesh_path = exported_catalog[0]["files"]["mesh"]["path"]
    stale_payload = (
        data_root
        / "exports"
        / "scene_engine"
        / export_id
        / "wall_fixtures"
        / "painting"
        / "painting_frame_01"
        / "model.glb"
    )

    assert result["payload_file_count"] == 2
    assert exported_mesh_path.startswith(
        f"exports/scene_engine/{export_id}/wall_fixtures/painting/painting_frame_01/"
    )
    assert export_metadata["files"]["wall_fixture_catalog"]["path"] == "wall_fixture_catalog.json"
    assert export_metadata["data_snapshot"]["fixture_payload_count"] == 1
    assert stale_payload.exists()

    empty_catalog_path = _write_json(input_dir / "wall_fixture_catalog_empty.json", [])
    result = export_wall_fixture_snapshot(
        export_id=export_id,
        source_catalog_id="wall_fixtures_v0",
        catalog_path=empty_catalog_path,
        fixture_category_index_path=fixture_category_index_path,
        manifest_path=manifest_path,
        output_dir=output_dir,
    )

    exported_catalog = json.loads(
        (output_dir / "wall_fixture_catalog.json").read_text(encoding="utf-8")
    )

    assert result["payload_file_count"] == 0
    assert exported_catalog == []
    assert not stale_payload.exists()
