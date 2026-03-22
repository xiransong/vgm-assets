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
from .wall_fixtures import (
    build_wall_fixture_catalog_manifest,
    build_wall_fixture_category_index,
    validate_wall_fixture_catalog_data,
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
from .support_clutter import validate_support_clutter_compatibility_data
from .support_surfaces import (
    apply_support_surface_annotations_to_asset_records,
    filter_support_surface_annotations_for_asset_records,
    validate_support_surface_annotation_set_data,
)
from .sampling import build_category_index


def _repo_relative_or_absolute(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root()).as_posix()
    except ValueError:
        return str(resolved)


def _replace_directory(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _snapshot_root(export_id: str, data_root: Path) -> tuple[Path, Path]:
    snapshot_root_relative = Path("exports") / "scene_engine" / export_id
    return snapshot_root_relative, data_root / snapshot_root_relative


def _materialize_asset_payload_snapshot(
    *,
    records: list[dict],
    export_id: str,
    data_root: Path,
) -> tuple[list[dict], dict]:
    snapshot_root_relative, snapshot_root = _snapshot_root(export_id, data_root)
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
    snapshot_root_relative, snapshot_root = _snapshot_root(export_id, data_root)
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
    snapshot_root_relative, snapshot_root = _snapshot_root(export_id, data_root)
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
    snapshot_root_relative, snapshot_root = _snapshot_root(export_id, data_root)
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


def _materialize_wall_fixture_payload_snapshot(
    *,
    records: list[dict],
    export_id: str,
    data_root: Path,
) -> tuple[list[dict], dict]:
    snapshot_root_relative, snapshot_root = _snapshot_root(export_id, data_root)
    payload_root = snapshot_root / "wall_fixtures"
    payload_root.mkdir(parents=True, exist_ok=True)

    exported_records: list[dict] = []
    payload_files: list[dict] = []

    for record in records:
        exported_record = deepcopy(record)
        fixture_id = exported_record["fixture_id"]
        category = exported_record["category"]
        files = exported_record.get("files", {})

        for file_key, file_ref in files.items():
            if not isinstance(file_ref, dict) or "path" not in file_ref:
                continue

            source_path = resolve_data_ref(file_ref["path"], data_root=data_root)
            destination_dir = payload_root / category / fixture_id
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
    output_dir = _replace_directory(output_dir)

    catalog_path = catalog_path.resolve()
    category_index_path = category_index_path.resolve()
    manifest_path = manifest_path.resolve()
    data_root = default_data_root()
    _replace_directory(_snapshot_root(export_id, data_root)[1])

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
                "path": _repo_relative_or_absolute(catalog_path),
                "sha256": _sha256(catalog_path),
            },
            "category_index": {
                "path": _repo_relative_or_absolute(category_index_path),
                "sha256": _sha256(category_index_path),
            },
            "asset_catalog_manifest": {
                "path": _repo_relative_or_absolute(manifest_path),
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
    output_dir = _replace_directory(output_dir)

    catalog_path = catalog_path.resolve()
    surface_type_index_path = surface_type_index_path.resolve()
    manifest_path = manifest_path.resolve()
    data_root = default_data_root()
    _replace_directory(_snapshot_root(export_id, data_root)[1])

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
                "path": _repo_relative_or_absolute(catalog_path),
                "sha256": _sha256(catalog_path),
            },
            "surface_type_index": {
                "path": _repo_relative_or_absolute(surface_type_index_path),
                "sha256": _sha256(surface_type_index_path),
            },
            "material_catalog_manifest": {
                "path": _repo_relative_or_absolute(manifest_path),
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
    output_dir = _replace_directory(output_dir)

    catalog_path = catalog_path.resolve()
    opening_type_index_path = opening_type_index_path.resolve()
    manifest_path = manifest_path.resolve()
    data_root = default_data_root()
    _replace_directory(_snapshot_root(export_id, data_root)[1])

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
                "path": _repo_relative_or_absolute(catalog_path),
                "sha256": _sha256(catalog_path),
            },
            "opening_type_index": {
                "path": _repo_relative_or_absolute(opening_type_index_path),
                "sha256": _sha256(opening_type_index_path),
            },
            "assembly_catalog_manifest": {
                "path": _repo_relative_or_absolute(manifest_path),
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
    output_dir = _replace_directory(output_dir)

    catalog_path = catalog_path.resolve()
    fixture_index_path = fixture_index_path.resolve()
    manifest_path = manifest_path.resolve()
    data_root = default_data_root()
    _replace_directory(_snapshot_root(export_id, data_root)[1])

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
                "path": _repo_relative_or_absolute(catalog_path),
                "sha256": _sha256(catalog_path),
            },
            "fixture_index": {
                "path": _repo_relative_or_absolute(fixture_index_path),
                "sha256": _sha256(fixture_index_path),
            },
            "fixture_catalog_manifest": {
                "path": _repo_relative_or_absolute(manifest_path),
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


def export_support_clutter_snapshot(
    *,
    export_id: str,
    source_catalog_id: str,
    catalog_path: Path,
    category_index_path: Path,
    support_compatibility_path: Path,
    manifest_path: Path,
    output_dir: Path,
    notes: str | None = None,
) -> dict:
    output_dir = _replace_directory(output_dir)

    catalog_path = catalog_path.resolve()
    category_index_path = category_index_path.resolve()
    support_compatibility_path = support_compatibility_path.resolve()
    manifest_path = manifest_path.resolve()
    data_root = default_data_root()
    _replace_directory(_snapshot_root(export_id, data_root)[1])

    prop_catalog_out = output_dir / "prop_asset_catalog.json"
    prop_category_index_out = output_dir / "prop_category_index.json"
    support_compatibility_out = output_dir / "support_compatibility.json"
    manifest_out = output_dir / "asset_catalog_manifest.json"

    source_records = json.loads(catalog_path.read_text(encoding="utf-8"))
    exported_records, payload_manifest = _materialize_asset_payload_snapshot(
        records=source_records,
        export_id=export_id,
        data_root=data_root,
    )
    prop_catalog_out.write_text(
        json.dumps(exported_records, indent=2) + "\n",
        encoding="utf-8",
    )

    category_index = build_category_index(prop_catalog_out)
    category_index["catalog_path"] = "prop_asset_catalog.json"
    prop_category_index_out.write_text(
        json.dumps(category_index, indent=2) + "\n",
        encoding="utf-8",
    )

    support_compatibility = json.loads(support_compatibility_path.read_text(encoding="utf-8"))
    validate_support_clutter_compatibility_data(support_compatibility)
    support_compatibility_out.write_text(
        json.dumps(support_compatibility, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = build_catalog_manifest(prop_catalog_out, catalog_id=export_id)
    manifest["catalog_files"][0]["path"] = "prop_asset_catalog.json"
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
            "prop_asset_catalog": {
                "path": _repo_relative_or_absolute(catalog_path),
                "sha256": _sha256(catalog_path),
            },
            "prop_category_index": {
                "path": _repo_relative_or_absolute(category_index_path),
                "sha256": _sha256(category_index_path),
            },
            "support_compatibility": {
                "path": _repo_relative_or_absolute(support_compatibility_path),
                "sha256": _sha256(support_compatibility_path),
            },
            "asset_catalog_manifest": {
                "path": _repo_relative_or_absolute(manifest_path),
                "sha256": _sha256(manifest_path),
            },
        },
        "files": {
            "prop_asset_catalog": {
                "path": "prop_asset_catalog.json",
                "sha256": _sha256(prop_catalog_out),
            },
            "prop_category_index": {
                "path": "prop_category_index.json",
                "sha256": _sha256(prop_category_index_out),
            },
            "support_compatibility": {
                "path": "support_compatibility.json",
                "sha256": _sha256(support_compatibility_out),
            },
            "asset_catalog_manifest": {
                "path": "asset_catalog_manifest.json",
                "sha256": _sha256(manifest_out),
            },
        },
        "data_snapshot": payload_manifest,
        "contract": {
            "compatibility_schema_path": "schemas/local/support_clutter_compatibility_v0.schema.json",
            "support_surface_annotation_path": "catalogs/living_room_kenney_v0/support_surface_annotations_v1.json",
            "prop_annotation_path": "catalogs/support_clutter_ai2thor_v0/prop_annotations_v0.json",
        },
        "notes": notes or "",
    }

    metadata_path = output_dir / "export_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return {
        "export_id": export_id,
        "output_dir": str(output_dir.resolve()),
        "prop_asset_catalog": str(prop_catalog_out.resolve()),
        "prop_category_index": str(prop_category_index_out.resolve()),
        "support_compatibility": str(support_compatibility_out.resolve()),
        "asset_catalog_manifest": str(manifest_out.resolve()),
        "export_metadata": str(metadata_path.resolve()),
        "data_snapshot_root": str(
            (data_root / payload_manifest["data_snapshot_root"]).resolve()
        ),
        "payload_file_count": payload_manifest["payload_file_count"],
    }


def export_wall_fixture_snapshot(
    *,
    export_id: str,
    source_catalog_id: str,
    catalog_path: Path,
    fixture_category_index_path: Path,
    manifest_path: Path,
    output_dir: Path,
    notes: str | None = None,
) -> dict:
    output_dir = _replace_directory(output_dir)

    catalog_path = catalog_path.resolve()
    fixture_category_index_path = fixture_category_index_path.resolve()
    manifest_path = manifest_path.resolve()
    data_root = default_data_root()
    _replace_directory(_snapshot_root(export_id, data_root)[1])

    fixture_catalog_out = output_dir / "wall_fixture_catalog.json"
    fixture_category_index_out = output_dir / "fixture_category_index.json"
    manifest_out = output_dir / "fixture_catalog_manifest.json"

    source_records = json.loads(catalog_path.read_text(encoding="utf-8"))
    validate_wall_fixture_catalog_data(source_records)
    exported_records, payload_manifest = _materialize_wall_fixture_payload_snapshot(
        records=source_records,
        export_id=export_id,
        data_root=data_root,
    )
    validate_wall_fixture_catalog_data(exported_records)
    fixture_catalog_out.write_text(
        json.dumps(exported_records, indent=2) + "\n",
        encoding="utf-8",
    )

    fixture_category_index = build_wall_fixture_category_index(fixture_catalog_out)
    fixture_category_index["catalog_path"] = "wall_fixture_catalog.json"
    fixture_category_index_out.write_text(
        json.dumps(fixture_category_index, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = build_wall_fixture_catalog_manifest(
        fixture_catalog_out, catalog_id=export_id
    )
    manifest["catalog_files"][0]["path"] = "wall_fixture_catalog.json"
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
            "wall_fixture_catalog": {
                "path": _repo_relative_or_absolute(catalog_path),
                "sha256": _sha256(catalog_path),
            },
            "fixture_category_index": {
                "path": _repo_relative_or_absolute(fixture_category_index_path),
                "sha256": _sha256(fixture_category_index_path),
            },
            "fixture_catalog_manifest": {
                "path": _repo_relative_or_absolute(manifest_path),
                "sha256": _sha256(manifest_path),
            },
        },
        "files": {
            "wall_fixture_catalog": {
                "path": "wall_fixture_catalog.json",
                "sha256": _sha256(fixture_catalog_out),
            },
            "fixture_category_index": {
                "path": "fixture_category_index.json",
                "sha256": _sha256(fixture_category_index_out),
            },
            "fixture_catalog_manifest": {
                "path": "fixture_catalog_manifest.json",
                "sha256": _sha256(manifest_out),
            },
        },
        "data_snapshot": payload_manifest,
        "contract": {
            "schema_path": "schemas/local/wall_fixture_catalog_v0.schema.json",
            "consumer_note": "docs/architecture/wall_fixture_catalog_v0.md",
        },
        "notes": notes or "",
    }

    metadata_path = output_dir / "export_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    return {
        "export_id": export_id,
        "output_dir": str(output_dir.resolve()),
        "wall_fixture_catalog": str(fixture_catalog_out.resolve()),
        "fixture_category_index": str(fixture_category_index_out.resolve()),
        "fixture_catalog_manifest": str(manifest_out.resolve()),
        "export_metadata": str(metadata_path.resolve()),
        "data_snapshot_root": str(
            (data_root / payload_manifest["data_snapshot_root"]).resolve()
        ),
        "payload_file_count": payload_manifest["payload_file_count"],
    }


def export_scene_engine_snapshot_with_support_annotations(
    *,
    export_id: str,
    source_catalog_id: str,
    catalog_path: Path,
    category_index_path: Path,
    manifest_path: Path,
    support_annotations_path: Path,
    output_dir: Path,
    notes: str | None = None,
) -> dict:
    output_dir = _replace_directory(output_dir)

    catalog_path = catalog_path.resolve()
    category_index_path = category_index_path.resolve()
    manifest_path = manifest_path.resolve()
    support_annotations_path = support_annotations_path.resolve()
    data_root = default_data_root()
    _replace_directory(_snapshot_root(export_id, data_root)[1])

    asset_catalog_out = output_dir / "asset_catalog.json"
    category_index_out = output_dir / "category_index.json"
    manifest_out = output_dir / "asset_catalog_manifest.json"
    support_annotations_out = output_dir / "support_surface_annotations_v1.json"

    source_records = json.loads(catalog_path.read_text(encoding="utf-8"))
    support_annotations_payload = json.loads(support_annotations_path.read_text(encoding="utf-8"))
    validate_support_surface_annotation_set_data(support_annotations_payload)
    synced_records = apply_support_surface_annotations_to_asset_records(
        source_records,
        support_annotations_payload,
    )
    exported_records, payload_manifest = _materialize_asset_payload_snapshot(
        records=synced_records,
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

    filtered_annotations = filter_support_surface_annotations_for_asset_records(
        exported_records,
        support_annotations_payload,
    )
    support_annotations_out.write_text(
        json.dumps(filtered_annotations, indent=2) + "\n",
        encoding="utf-8",
    )

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
                "path": _repo_relative_or_absolute(catalog_path),
                "sha256": _sha256(catalog_path),
            },
            "category_index": {
                "path": _repo_relative_or_absolute(category_index_path),
                "sha256": _sha256(category_index_path),
            },
            "asset_catalog_manifest": {
                "path": _repo_relative_or_absolute(manifest_path),
                "sha256": _sha256(manifest_path),
            },
            "support_surface_annotations_v1": {
                "path": _repo_relative_or_absolute(support_annotations_path),
                "sha256": _sha256(support_annotations_path),
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
            "support_surface_annotations_v1": {
                "path": "support_surface_annotations_v1.json",
                "sha256": _sha256(support_annotations_out),
            },
        },
        "data_snapshot": payload_manifest,
        "contract": {
            "support_surface_annotation_set_version": filtered_annotations["version"],
            "support_surface_companion_file": "support_surface_annotations_v1.json",
            "canonical_shared_support_field": "support.support_surfaces_v1",
            "compatibility_support_field": "support.support_surfaces",
        },
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
        "support_surface_annotations_v1": str(support_annotations_out.resolve()),
        "export_metadata": str(metadata_path.resolve()),
        "data_snapshot_root": str(
            (data_root / payload_manifest["data_snapshot_root"]).resolve()
        ),
        "payload_file_count": payload_manifest["payload_file_count"],
    }
