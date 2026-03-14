from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import build_catalog_manifest, validate_asset_catalog, write_catalog_manifest
from .measure import measure_catalog_meshes


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
        report = measure_catalog_meshes(args.catalog)
        text = json.dumps(report, indent=2 if args.pretty or args.output else None)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
            print(f"Wrote measurement report to {args.output}")
        else:
            print(text)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
