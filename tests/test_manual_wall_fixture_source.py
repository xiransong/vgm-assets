from __future__ import annotations

import json
from pathlib import Path

from vgm_assets.sources import organize_manual_wall_fixture_selection


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_organize_manual_wall_fixture_selection_writes_normalized_bundle(
    tmp_path: Path,
) -> None:
    raw_root = tmp_path / "raw"
    data_root = tmp_path / "data"

    raw_asset_dir = (
        raw_root
        / "sources"
        / "manual"
        / "wall_fixtures_v0"
        / "painting"
        / "candidate_painting_01"
    )
    raw_asset_dir.mkdir(parents=True, exist_ok=True)
    (raw_asset_dir / "model.glb").write_text("mesh", encoding="utf-8")
    (raw_asset_dir / "preview.png").write_text("preview", encoding="utf-8")

    spec_path = _write_json(
        tmp_path / "wall_fixture_source_spec_v0.json",
        {
            "source_id": "manual_wall_fixtures_v0",
            "source_url": "manual_curated_wall_fixture_shortlist",
            "license": "per_asset_manual_review",
            "processing": {
                "raw_root_relpath": "sources/manual/wall_fixtures_v0",
                "normalized_root_relpath": "fixtures/wall/manual/wall_fixtures_v0",
            },
        },
    )
    selection_path = _write_json(
        tmp_path / "wall_fixture_selection_v0.json",
        [
            {
                "selection_id": "manual_wall_fixture_painting_01_v0",
                "category": "painting",
                "source_pack": "manual_curated",
                "source_url": "https://example.org/manual-wall-fixtures/painting-01",
                "license": "CC0",
                "source_name": "candidate_painting_01",
                "raw_model_rel": "painting/candidate_painting_01/model.glb",
                "raw_preview_rel": "painting/candidate_painting_01/preview.png",
                "fixture_id": "manual_painting_01",
                "display_name": "Manual Painting 01",
                "dimensions": {
                    "width_m": 0.8,
                    "height_m": 0.55,
                    "depth_m": 0.04
                },
                "mount": {
                    "mount_type": "wall_mounted",
                    "mount_plane": "vertical_wall",
                    "usable_margin_m": 0.05
                },
                "style_tags": ["wall_art"],
                "preferred_room_types": ["living_room"],
                "review_status": "approved",
                "normalized_rel_dir": "fixtures/wall/manual/wall_fixtures_v0/painting/manual_painting_01",
            }
        ],
    )

    summary = organize_manual_wall_fixture_selection(
        spec_path=spec_path,
        selection_path=selection_path,
        raw_data_root=raw_root,
        data_root=data_root,
        created_at="2026-03-22T00:00:00+00:00",
    )

    bundle_dir = (
        data_root
        / "fixtures"
        / "wall"
        / "manual"
        / "wall_fixtures_v0"
        / "painting"
        / "manual_painting_01"
    )
    bundle_manifest = json.loads(
        (bundle_dir / "bundle_manifest.json").read_text(encoding="utf-8")
    )
    source_metadata = json.loads(
        (bundle_dir / "source_metadata.json").read_text(encoding="utf-8")
    )
    selection_manifest = json.loads(
        (Path(summary["slice_root"]) / "selection_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert summary["fixture_count"] == 1
    assert (bundle_dir / "model.glb").exists()
    assert (bundle_dir / "preview.png").exists()
    assert bundle_manifest["fixture_id"] == "manual_painting_01"
    assert bundle_manifest["files"]["mesh"]["path"] == (
        "fixtures/wall/manual/wall_fixtures_v0/painting/manual_painting_01/model.glb"
    )
    assert source_metadata["source_url"] == "https://example.org/manual-wall-fixtures/painting-01"
    assert selection_manifest["fixture_count"] == 1
    assert selection_manifest["fixtures"][0]["normalized_dir"] == "manual_painting_01"
