from __future__ import annotations

import json
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from .catalog import _sha256, build_catalog_manifest
from .ceiling_fixtures import (
    build_ceiling_light_fixture_catalog_manifest,
    build_fixture_index,
    validate_ceiling_light_fixture_catalog_data,
)
from .paths import default_data_root, resolve_data_ref
from .opening_assemblies import (
    build_opening_assembly_catalog_manifest,
    build_opening_type_index,
    validate_opening_assembly_catalog_data,
)
from .protocol import repo_root
from .room_surface_materials import (
    build_material_catalog_manifest,
    build_surface_type_index,
    validate_room_surface_material_catalog_data,
)
from .sampling import build_category_index


def _materialize_asset_payload_snapshot(
    *,
    records: list[dict],
    export_id: str,
    data_root: Path,
) -> tuple[list[dict], dict]:
    snapshot_root_relative = Path("exports") / "scene_engine" / export_id
    snapshot_root = data_root / snapshot_root_relative
    payload_root = snapshot_root / "assets"
    payload_root.mkdir(parents=True, exist_ok=True)

    exported_records: list[dict] = []
    payload_files: list[dict] = []

    for record in records:
        exported_record = deepcopy(record)
        asset_id = exported_record["asset_id"]
        category = exported_record["category"]
        files = exported_record.get("files", {})

        for file_key, file_ref in files.items():
            if not isinstance(file_ref, dict) or "path" not in file_ref:
                continue

            source_path = resolve_data_ref(file_ref["path"], data_root=data_root)
            destination_dir = payload_root / category / asset_id
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination_path = destination_dir / source_path.name
            shutil.copy2(source_path, destination_path)

            relative_destination = destination_path.relative_to(data_root)
            file_ref["path"] = relative_destination.as_posix()

            payload_files.append(
                {
                    "asset_id": asset_id,
                    "file_key": file_key,
                    "path": relative_destination.as_posix(),
                    "sha256": _sha256(destination_path),
                    "size_bytes": destination_path.stat().st_size,
                }
            )

        exported_records.append(exported_record)

    payload_manifest = {
        "data_snapshot_root": snapshot_root_relative.as_posix(),
        "asset_payload_count": len(exported_records),
        "payload_file_count": len(payload_files),
        "payload_files": payload_files,
    }
    return exported_records, payload_manifest


def _materialize_room_surface_payload_snapshot(
    *,
    records: list[dict],
    export_id: str,
    data_root: Path,
) -> tuple[list[dict], dict]:
    snapshot_root_relative = Path("exports") / "scene_engine" / export_id
    snapshot_root = data_root / snapshot_root_relative
    payload_root = snapshot_root / "materials"
    payload_root.mkdir(parents=True, exist_ok=True)

    exported_records: list[dict] = []
    payload_files: list[dict] = []

    for record in records:
        exported_record = deepcopy(record)
        material_id = exported_record["material_id"]
        surface_type = exported_record["surface_type"]
        files = exported_record.get("files", {})

        for file_key, file_ref in files.items():
            if not isinstance(file_ref, dict) or "path" not in file_ref:
                continue

            source_path = resolve_data_ref(file_ref["path"], data_root=data_root)
            destination_dir = payload_root / surface_type / material_id
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination_path = destination_dir / source_path.name
            shutil.copy2(source_path, destination_path)

            relative_destination = destination_path.relative_to(data_root)
            file_ref["path"] = relative_destination.as_posix()

            payload_files.append(
                {
                    "material_id": material_id,
                    "file_key": file_key,
                    "path": relative_destination.as_posix(),
                    "sha256": _sha256(destination_path),
                    "size_bytes": destination_path.stat().st_size,
                }
            )

        exported_records.append(exported_record)

    payload_manifest = {
        "data_snapshot_root": snapshot_root_relative.as_posix(),
        "material_payload_count": len(exported_records),
        "payload_file_count": len(payload_files),
        "payload_files": payload_files,
    }
    return exported_records, payload_manifest


def _materialize_opening_payload_snapshot(
    *,
    records: list[dict],
    export_id: str,
    data_root: Path,
) -> tuple[list[dict], dict]:
    snapshot_root_relative = Path("exports") / "scene_engine" / export_id
    snapshot_root = data_root / snapshot_root_relative
    payload_root = snapshot_root / "assemblies"
    payload_root.mkdir(parents=True, exist_ok=True)

    exported_records: list[dict] = []
    payload_files: list[dict] = []

    for record in records:
        exported_record = deepcopy(record)
        assembly_id = exported_record["assembly_id"]
        opening_type = exported_record["opening_type"]
        files = exported_record.get("files", {})

        for file_key, file_ref in files.items():
            if not isinstance(file_ref, dict) or "path" not in file_ref:
                continue

            source_path = resolve_data_ref(file_ref["path"], data_root=data_root)
            destination_dir = payload_root / opening_type / assembly_id
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination_path = destination_dir / source_path.name
            shutil.copy2(source_path, destination_path)

            relative_destination = destination_path.relative_to(data_root)
            file_ref["path"] = relative_destination.as_posix()

            payload_files.append(
                {
                    "assembly_id": assembly_id,
                    "file_key": file_key,
                    "path": relative_destination.as_posix(),
                    "sha256": _sha256(destination_path),
                    "size_bytes": destination_path.stat().st_size,
                }
            )

        exported_records.append(exported_record)

    payload_manifest = {
        "data_snapshot_root": snapshot_root_relative.as_posix(),
        "assembly_payload_count": len(exported_records),
        "payload_file_count": len(payload_files),
        "payload_files": payload_files,
    }
    return exported_records, payload_manifest


def _materialize_ceiling_fixture_payload_snapshot(
    *,
    records: list[dict],
    export_id: str,
    data_root: Path,
) -> tuple[list[dict], dict]:
    snapshot_root_relative = Path("exports") / "scene_engine" / export_id
    snapshot_root = data_root / snapshot_root_relative
    payload_root = snapshot_root / "fixtures"
    payload_root.mkdir(parents=True, exist_ok=True)

    exported_records: list[dict] = []
    payload_files: list[dict] = []

    for record in records:
        exported_record = deepcopy(record)
        fixture_id = exported_record["fixture_id"]
        mount_type = exported_record["mount_type"]
        files = exported_record.get("files", {})

        for file_key, file_ref in files.items():
            if not isinstance(file_ref, dict) or "path" not in file_ref:
                continue

            source_path = resolve_data_ref(file_ref["path"], data_root=data_root)
            destination_dir = payload_root / mount_type / fixture_id
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination_path = destination_dir / source_path.name
            shutil.copy2(source_path, destination_path)

            relative_destination = destination_path.relative_to(data_root)
            file_ref["path"] = relative_destination.as_posix()

            payload_files.append(
                {
                    "fixture_id": fixture_id,
                    "file_key": file_key,
                    "path": relative_destination.as_posix(),
                    "sha256": _sha256(destination_path),
                    "size_bytes": destination_path.stat().st_size,
                }
            )

        exported_records.append(exported_record)

    payload_manifest = {
        "data_snapshot_root": snapshot_root_relative.as_posix(),
        "fixture_payload_count": len(exported_records),
        "payload_file_count": len(payload_files),
        "payload_files": payload_files,
    }
    return exported_records, payload_manifest


def export_scene_engine_snapshot(
    *,
    export_id: str,
    source_catalog_id: str,
    catalog_path: Path,
    category_index_path: Path,
    manifest_path: Path,
    output_dir: Path,
    notes: str | None = None,
) -> dict:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    catalog_path = catalog_path.resolve()
    category_index_path = category_index_path.resolve()
    manifest_path = manifest_path.resolve()
    data_root = default_data_root()

    asset_catalog_out = output_dir / "asset_catalog.json"
    category_index_out = output_dir / "category_index.json"
    manifest_out = output_dir / "asset_catalog_manifest.json"

    source_records = json.loads(catalog_path.read_text(encoding="utf-8"))
    exported_records, payload_manifest = _materialize_asset_payload_snapshot(
        records=source_records,
        export_id=export_id,
        data_root=data_root,
    )
    asset_catalog_out.write_text(
        json.dumps(exported_records, indent=2) + "\n",
        encoding="utf-8",
    )

    category_index = build_category_index(asset_catalog_out)
    category_index["catalog_path"] = "asset_catalog.json"
    category_index_out.write_text(
        json.dumps(category_index, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = build_catalog_manifest(asset_catalog_out, catalog_id=export_id)
    manifest["catalog_files"][0]["path"] = "asset_catalog.json"
    manifest_out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    metadata = {
        "export_id": export_id,
        "consumer": "vgm-scene-engine",
        "source_catalog_id": source_catalog_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "producer": {
            "repo": "vgm-assets",
            "version": "0.1.0-dev",
            "commit": "working_tree",
        },
        "source_artifacts": {
            "asset_catalog": {
                "path": catalog_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(catalog_path),
            },
            "category_index": {
                "path": category_index_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(category_index_path),
            },
            "asset_catalog_manifest": {
                "path": manifest_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(manifest_path),
            },
        },
        "files": {
            "asset_catalog": {
                "path": "asset_catalog.json",
                "sha256": _sha256(asset_catalog_out),
            },
            "category_index": {
                "path": "category_index.json",
                "sha256": _sha256(category_index_out),
            },
            "asset_catalog_manifest": {
                "path": "asset_catalog_manifest.json",
                "sha256": _sha256(manifest_out),
            },
        },
        "data_snapshot": payload_manifest,
        "notes": notes or "",
    }

    metadata_path = output_dir / "export_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return {
        "export_id": export_id,
        "output_dir": str(output_dir.resolve()),
        "asset_catalog": str(asset_catalog_out.resolve()),
        "category_index": str(category_index_out.resolve()),
        "asset_catalog_manifest": str(manifest_out.resolve()),
        "export_metadata": str(metadata_path.resolve()),
        "data_snapshot_root": str(
            (data_root / payload_manifest["data_snapshot_root"]).resolve()
        ),
        "payload_file_count": payload_manifest["payload_file_count"],
    }


def export_room_surface_material_snapshot(
    *,
    export_id: str,
    source_catalog_id: str,
    catalog_path: Path,
    surface_type_index_path: Path,
    manifest_path: Path,
    output_dir: Path,
    notes: str | None = None,
) -> dict:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    catalog_path = catalog_path.resolve()
    surface_type_index_path = surface_type_index_path.resolve()
    manifest_path = manifest_path.resolve()
    data_root = default_data_root()

    material_catalog_out = output_dir / "room_surface_material_catalog.json"
    surface_type_index_out = output_dir / "surface_type_index.json"
    manifest_out = output_dir / "material_catalog_manifest.json"

    source_records = json.loads(catalog_path.read_text(encoding="utf-8"))
    validate_room_surface_material_catalog_data(source_records)
    exported_records, payload_manifest = _materialize_room_surface_payload_snapshot(
        records=source_records,
        export_id=export_id,
        data_root=data_root,
    )
    validate_room_surface_material_catalog_data(exported_records)
    material_catalog_out.write_text(
        json.dumps(exported_records, indent=2) + "\n",
        encoding="utf-8",
    )

    surface_type_index = build_surface_type_index(material_catalog_out)
    surface_type_index["catalog_path"] = "room_surface_material_catalog.json"
    surface_type_index_out.write_text(
        json.dumps(surface_type_index, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = build_material_catalog_manifest(
        material_catalog_out, catalog_id=export_id
    )
    manifest["catalog_files"][0]["path"] = "room_surface_material_catalog.json"
    manifest_out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    metadata = {
        "export_id": export_id,
        "consumer": "vgm-scene-engine",
        "source_catalog_id": source_catalog_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "producer": {
            "repo": "vgm-assets",
            "version": "0.1.0-dev",
            "commit": "working_tree",
        },
        "source_artifacts": {
            "room_surface_material_catalog": {
                "path": catalog_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(catalog_path),
            },
            "surface_type_index": {
                "path": surface_type_index_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(surface_type_index_path),
            },
            "material_catalog_manifest": {
                "path": manifest_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(manifest_path),
            },
        },
        "files": {
            "room_surface_material_catalog": {
                "path": "room_surface_material_catalog.json",
                "sha256": _sha256(material_catalog_out),
            },
            "surface_type_index": {
                "path": "surface_type_index.json",
                "sha256": _sha256(surface_type_index_out),
            },
            "material_catalog_manifest": {
                "path": "material_catalog_manifest.json",
                "sha256": _sha256(manifest_out),
            },
        },
        "data_snapshot": payload_manifest,
        "contract": {
            "schema_path": "schemas/local/room_surface_material_catalog_v0.schema.json",
            "consumer_guarantees_note": "docs/architecture/room_surface_material_consumer_guarantees_v0.md",
        },
        "notes": notes or "",
    }

    metadata_path = output_dir / "export_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return {
        "export_id": export_id,
        "output_dir": str(output_dir.resolve()),
        "room_surface_material_catalog": str(material_catalog_out.resolve()),
        "surface_type_index": str(surface_type_index_out.resolve()),
        "material_catalog_manifest": str(manifest_out.resolve()),
        "export_metadata": str(metadata_path.resolve()),
        "data_snapshot_root": str(
            (data_root / payload_manifest["data_snapshot_root"]).resolve()
        ),
        "payload_file_count": payload_manifest["payload_file_count"],
    }


def export_opening_assembly_snapshot(
    *,
    export_id: str,
    source_catalog_id: str,
    catalog_path: Path,
    opening_type_index_path: Path,
    manifest_path: Path,
    output_dir: Path,
    notes: str | None = None,
) -> dict:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    catalog_path = catalog_path.resolve()
    opening_type_index_path = opening_type_index_path.resolve()
    manifest_path = manifest_path.resolve()
    data_root = default_data_root()

    assembly_catalog_out = output_dir / "opening_assembly_catalog.json"
    opening_type_index_out = output_dir / "opening_type_index.json"
    manifest_out = output_dir / "assembly_catalog_manifest.json"

    source_records = json.loads(catalog_path.read_text(encoding="utf-8"))
    validate_opening_assembly_catalog_data(source_records)
    exported_records, payload_manifest = _materialize_opening_payload_snapshot(
        records=source_records,
        export_id=export_id,
        data_root=data_root,
    )
    validate_opening_assembly_catalog_data(exported_records)
    assembly_catalog_out.write_text(
        json.dumps(exported_records, indent=2) + "\n",
        encoding="utf-8",
    )

    opening_type_index = build_opening_type_index(assembly_catalog_out)
    opening_type_index["catalog_path"] = "opening_assembly_catalog.json"
    opening_type_index_out.write_text(
        json.dumps(opening_type_index, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = build_opening_assembly_catalog_manifest(
        assembly_catalog_out, catalog_id=export_id
    )
    manifest["catalog_files"][0]["path"] = "opening_assembly_catalog.json"
    manifest_out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    metadata = {
        "export_id": export_id,
        "consumer": "vgm-scene-engine",
        "source_catalog_id": source_catalog_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "producer": {
            "repo": "vgm-assets",
            "version": "0.1.0-dev",
            "commit": "working_tree",
        },
        "source_artifacts": {
            "opening_assembly_catalog": {
                "path": catalog_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(catalog_path),
            },
            "opening_type_index": {
                "path": opening_type_index_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(opening_type_index_path),
            },
            "assembly_catalog_manifest": {
                "path": manifest_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(manifest_path),
            },
        },
        "files": {
            "opening_assembly_catalog": {
                "path": "opening_assembly_catalog.json",
                "sha256": _sha256(assembly_catalog_out),
            },
            "opening_type_index": {
                "path": "opening_type_index.json",
                "sha256": _sha256(opening_type_index_out),
            },
            "assembly_catalog_manifest": {
                "path": "assembly_catalog_manifest.json",
                "sha256": _sha256(manifest_out),
            },
        },
        "data_snapshot": payload_manifest,
        "contract": {
            "schema_path": "schemas/local/opening_assembly_catalog_v0.schema.json",
            "consumer_note": "docs/architecture/opening_assemblies_scene_engine_consumer_v0.md",
        },
        "notes": notes or "",
    }

    metadata_path = output_dir / "export_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return {
        "export_id": export_id,
        "output_dir": str(output_dir.resolve()),
        "opening_assembly_catalog": str(assembly_catalog_out.resolve()),
        "opening_type_index": str(opening_type_index_out.resolve()),
        "assembly_catalog_manifest": str(manifest_out.resolve()),
        "export_metadata": str(metadata_path.resolve()),
        "data_snapshot_root": str(
            (data_root / payload_manifest["data_snapshot_root"]).resolve()
        ),
        "payload_file_count": payload_manifest["payload_file_count"],
    }


def export_ceiling_light_fixture_snapshot(
    *,
    export_id: str,
    source_catalog_id: str,
    catalog_path: Path,
    fixture_index_path: Path,
    manifest_path: Path,
    output_dir: Path,
    notes: str | None = None,
) -> dict:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    catalog_path = catalog_path.resolve()
    fixture_index_path = fixture_index_path.resolve()
    manifest_path = manifest_path.resolve()
    data_root = default_data_root()

    fixture_catalog_out = output_dir / "ceiling_light_fixture_catalog.json"
    fixture_index_out = output_dir / "fixture_index.json"
    manifest_out = output_dir / "fixture_catalog_manifest.json"

    source_records = json.loads(catalog_path.read_text(encoding="utf-8"))
    validate_ceiling_light_fixture_catalog_data(source_records)
    exported_records, payload_manifest = _materialize_ceiling_fixture_payload_snapshot(
        records=source_records,
        export_id=export_id,
        data_root=data_root,
    )
    validate_ceiling_light_fixture_catalog_data(exported_records)
    fixture_catalog_out.write_text(
        json.dumps(exported_records, indent=2) + "\n",
        encoding="utf-8",
    )

    fixture_index = build_fixture_index(fixture_catalog_out)
    fixture_index["catalog_path"] = "ceiling_light_fixture_catalog.json"
    fixture_index_out.write_text(
        json.dumps(fixture_index, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = build_ceiling_light_fixture_catalog_manifest(
        fixture_catalog_out, catalog_id=export_id
    )
    manifest["catalog_files"][0]["path"] = "ceiling_light_fixture_catalog.json"
    manifest_out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    metadata = {
        "export_id": export_id,
        "consumer": "vgm-scene-engine",
        "source_catalog_id": source_catalog_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "producer": {
            "repo": "vgm-assets",
            "version": "0.1.0-dev",
            "commit": "working_tree",
        },
        "source_artifacts": {
            "ceiling_light_fixture_catalog": {
                "path": catalog_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(catalog_path),
            },
            "fixture_index": {
                "path": fixture_index_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(fixture_index_path),
            },
            "fixture_catalog_manifest": {
                "path": manifest_path.relative_to(repo_root()).as_posix(),
                "sha256": _sha256(manifest_path),
            },
        },
        "files": {
            "ceiling_light_fixture_catalog": {
                "path": "ceiling_light_fixture_catalog.json",
                "sha256": _sha256(fixture_catalog_out),
            },
            "fixture_index": {
                "path": "fixture_index.json",
                "sha256": _sha256(fixture_index_out),
            },
            "fixture_catalog_manifest": {
                "path": "fixture_catalog_manifest.json",
                "sha256": _sha256(manifest_out),
            },
        },
        "data_snapshot": payload_manifest,
        "contract": {
            "schema_path": "schemas/local/ceiling_light_fixture_catalog_v0.schema.json",
            "consumer_note": "docs/architecture/ceiling_light_fixtures_scene_engine_consumer_v0.md",
        },
        "notes": notes or "",
    }

    metadata_path = output_dir / "export_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return {
        "export_id": export_id,
        "output_dir": str(output_dir.resolve()),
        "ceiling_light_fixture_catalog": str(fixture_catalog_out.resolve()),
        "fixture_index": str(fixture_index_out.resolve()),
        "fixture_catalog_manifest": str(manifest_out.resolve()),
        "export_metadata": str(metadata_path.resolve()),
        "data_snapshot_root": str(
            (data_root / payload_manifest["data_snapshot_root"]).resolve()
        ),
        "payload_file_count": payload_manifest["payload_file_count"],
    }
