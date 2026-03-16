from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import (
    build_catalog_manifest,
    refresh_catalog_artifacts,
    validate_asset_catalog,
    write_catalog_manifest,
)
from .paths import default_data_root, default_raw_data_root
from .sources import (
    organize_kenney_selection,
    rebuild_kenney_selection,
    register_raw_source,
    unpack_registered_zip,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vgm-assets")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate an asset catalog JSON file against vgm-protocol AssetSpec",
    )
    validate_parser.add_argument("catalog", type=Path)
    validate_parser.add_argument("--protocol-root", type=Path)

    manifest_parser = subparsers.add_parser(
        "write-manifest",
        help="Validate an asset catalog and write an AssetCatalogManifest JSON file",
    )
    manifest_parser.add_argument("catalog", type=Path)
    manifest_parser.add_argument("--catalog-id", required=True)
    manifest_parser.add_argument("--output", type=Path, required=True)
    manifest_parser.add_argument("--protocol-root", type=Path)
    manifest_parser.add_argument("--created-at")

    preview_parser = subparsers.add_parser(
        "print-manifest",
        help="Validate an asset catalog and print its manifest JSON to stdout",
    )
    preview_parser.add_argument("catalog", type=Path)
    preview_parser.add_argument("--catalog-id", required=True)
    preview_parser.add_argument("--protocol-root", type=Path)
    preview_parser.add_argument("--created-at")

    measure_parser = subparsers.add_parser(
        "measure-catalog",
        help="Measure mesh bounds for catalog entries with files.mesh refs",
    )
    measure_parser.add_argument("catalog", type=Path)
    measure_parser.add_argument("--output", type=Path)
    measure_parser.add_argument("--pretty", action="store_true")

    paths_parser = subparsers.add_parser(
        "print-paths",
        help="Print the default RAW_DATA_ROOT and DATA_ROOT for vgm-assets",
    )
    paths_parser.add_argument("--pretty", action="store_true")

    register_parser = subparsers.add_parser(
        "register-raw-source",
        help="Copy a raw source archive into RAW_DATA_ROOT and write source_manifest.json",
    )
    register_parser.add_argument("spec", type=Path)
    register_parser.add_argument("--raw-file", type=Path, required=True)
    register_parser.add_argument("--raw-data-root", type=Path)
    register_parser.add_argument("--acquired-by")
    register_parser.add_argument("--acquired-at")
    register_parser.add_argument("--notes")

    unpack_parser = subparsers.add_parser(
        "unpack-registered-zip",
        help="Unpack a registered zip archive into DATA_ROOT",
    )
    unpack_parser.add_argument("spec", type=Path)
    unpack_parser.add_argument("--raw-data-root", type=Path)
    unpack_parser.add_argument("--data-root", type=Path)

    organize_parser = subparsers.add_parser(
        "organize-kenney-selection",
        help="Build the normalized Kenney selection tree in DATA_ROOT from the unpacked source",
    )
    organize_parser.add_argument("selection", type=Path)
    organize_parser.add_argument("--source-spec", type=Path, required=True)
    organize_parser.add_argument("--raw-data-root", type=Path)
    organize_parser.add_argument("--data-root", type=Path)

    rebuild_parser = subparsers.add_parser(
        "rebuild-kenney-selection",
        help="Register, unpack, and organize the selected Kenney slice in one command",
    )
    rebuild_parser.add_argument("selection", type=Path)
    rebuild_parser.add_argument("--source-spec", type=Path, required=True)
    rebuild_parser.add_argument("--raw-file", type=Path)
    rebuild_parser.add_argument("--raw-data-root", type=Path)
    rebuild_parser.add_argument("--data-root", type=Path)
    rebuild_parser.add_argument("--acquired-by")
    rebuild_parser.add_argument("--acquired-at")
    rebuild_parser.add_argument("--notes")

    refresh_parser = subparsers.add_parser(
        "refresh-catalog-artifacts",
        help="Validate a catalog, refresh its measurement report, and write its manifest",
    )
    refresh_parser.add_argument("catalog", type=Path)
    refresh_parser.add_argument("--catalog-id", required=True)
    refresh_parser.add_argument("--manifest-output", type=Path, required=True)
    refresh_parser.add_argument("--measure-output", type=Path)
    refresh_parser.add_argument("--protocol-root", type=Path)
    refresh_parser.add_argument("--created-at")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "validate":
        records = validate_asset_catalog(args.catalog, args.protocol_root)
        print(f"Validated {len(records)} assets in {args.catalog}")
        return 0

    if args.command == "write-manifest":
        manifest = write_catalog_manifest(
            catalog_path=args.catalog,
            output_path=args.output,
            catalog_id=args.catalog_id,
            protocol_root=args.protocol_root,
            created_at=args.created_at,
        )
        print(
            f"Wrote manifest for {manifest['asset_count']} assets to {args.output}"
        )
        return 0

    if args.command == "print-manifest":
        manifest = build_catalog_manifest(
            catalog_path=args.catalog,
            catalog_id=args.catalog_id,
            protocol_root=args.protocol_root,
            created_at=args.created_at,
        )
        print(json.dumps(manifest, indent=2))
        return 0

    if args.command == "measure-catalog":
        from .measure import measure_catalog_meshes

        report = measure_catalog_meshes(args.catalog)
        text = json.dumps(report, indent=2 if args.pretty or args.output else None)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
            print(f"Wrote measurement report to {args.output}")
        else:
            print(text)
        return 0

    if args.command == "print-paths":
        payload = {
            "raw_data_root": str(default_raw_data_root()),
            "data_root": str(default_data_root()),
        }
        print(json.dumps(payload, indent=2 if args.pretty else None))
        return 0

    if args.command == "register-raw-source":
        manifest = register_raw_source(
            spec_path=args.spec,
            raw_file=args.raw_file,
            raw_data_root=args.raw_data_root,
            acquired_by=args.acquired_by,
            acquired_at=args.acquired_at,
            notes=args.notes,
        )
        print(json.dumps(manifest, indent=2))
        return 0

    if args.command == "unpack-registered-zip":
        manifest = unpack_registered_zip(
            spec_path=args.spec,
            raw_data_root=args.raw_data_root,
            data_root=args.data_root,
        )
        print(json.dumps(manifest, indent=2))
        return 0

    if args.command == "organize-kenney-selection":
        summary = organize_kenney_selection(
            spec_path=args.source_spec,
            selection_path=args.selection,
            raw_data_root=args.raw_data_root,
            data_root=args.data_root,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "rebuild-kenney-selection":
        summary = rebuild_kenney_selection(
            spec_path=args.source_spec,
            selection_path=args.selection,
            raw_file=args.raw_file,
            raw_data_root=args.raw_data_root,
            data_root=args.data_root,
            acquired_by=args.acquired_by,
            acquired_at=args.acquired_at,
            notes=args.notes,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "refresh-catalog-artifacts":
        summary = refresh_catalog_artifacts(
            catalog_path=args.catalog,
            catalog_id=args.catalog_id,
            manifest_output=args.manifest_output,
            measure_output=args.measure_output,
            protocol_root=args.protocol_root,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
