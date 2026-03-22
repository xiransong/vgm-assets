from __future__ import annotations

import json
from pathlib import Path

from vgm_assets.catalog import validate_asset_catalog
from vgm_assets.protocol import validate_instance
from vgm_assets.support_surfaces import validate_support_surface_annotation_set_data


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ROOT = REPO_ROOT.parent / "vgm-protocol"
MAINTAINED_EXPORT_ID = "living_room_kenney_v0_r3"
MAINTAINED_SOURCE_CATALOG_ID = "living_room_kenney_v0"
MAINTAINED_SNAPSHOT_ROOT = REPO_ROOT / "exports" / "scene_engine" / MAINTAINED_EXPORT_ID


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_maintained_asset_anchor_files_exist() -> None:
    expected = {
        "asset_catalog.json",
        "asset_catalog_manifest.json",
        "category_index.json",
        "export_metadata.json",
        "support_surface_annotations_v1.json",
    }
    observed = {path.name for path in MAINTAINED_SNAPSHOT_ROOT.iterdir() if path.is_file()}
    assert expected.issubset(observed)


def test_maintained_asset_anchor_validates_against_protocol() -> None:
    manifest_path = MAINTAINED_SNAPSHOT_ROOT / "asset_catalog_manifest.json"
    catalog_path = MAINTAINED_SNAPSHOT_ROOT / "asset_catalog.json"

    manifest = _load_json(manifest_path)
    validate_instance(
        manifest,
        "schemas/manifests/asset_catalog_manifest.schema.json",
        PROTOCOL_ROOT,
    )
    records = validate_asset_catalog(catalog_path, PROTOCOL_ROOT)

    assert manifest["catalog_id"] == MAINTAINED_EXPORT_ID
    assert manifest["asset_count"] == len(records)


def test_maintained_asset_anchor_metadata_is_consistent() -> None:
    catalog_path = MAINTAINED_SNAPSHOT_ROOT / "asset_catalog.json"
    category_index_path = MAINTAINED_SNAPSHOT_ROOT / "category_index.json"
    metadata_path = MAINTAINED_SNAPSHOT_ROOT / "export_metadata.json"
    annotations_path = MAINTAINED_SNAPSHOT_ROOT / "support_surface_annotations_v1.json"

    records = _load_json(catalog_path)
    category_index = _load_json(category_index_path)
    metadata = _load_json(metadata_path)
    annotations = _load_json(annotations_path)

    validate_support_surface_annotation_set_data(annotations)

    assert metadata["export_id"] == MAINTAINED_EXPORT_ID
    assert metadata["source_catalog_id"] == MAINTAINED_SOURCE_CATALOG_ID
    assert metadata["consumer"] == "vgm-scene-engine"
    assert category_index["catalog_path"] == "asset_catalog.json"
    assert metadata["files"]["asset_catalog"]["path"] == "asset_catalog.json"
    assert metadata["files"]["category_index"]["path"] == "category_index.json"
    assert metadata["files"]["asset_catalog_manifest"]["path"] == "asset_catalog_manifest.json"
    assert metadata["files"]["support_surface_annotations_v1"]["path"] == "support_surface_annotations_v1.json"
    assert metadata["data_snapshot"]["asset_payload_count"] == len(records)

    first_record = records[0]
    assert first_record["files"]["mesh"]["path"].startswith(
        f"exports/scene_engine/{MAINTAINED_EXPORT_ID}/assets/"
    )

