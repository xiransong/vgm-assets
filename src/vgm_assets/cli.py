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
from .ceiling_fixtures import (
    refresh_ceiling_light_fixture_catalog,
    validate_ceiling_light_fixture_catalog,
)
from .furniture_assets import refresh_furniture_asset_catalog
from .exports import (
    export_ceiling_light_fixture_snapshot,
    export_opening_assembly_snapshot,
    export_room_surface_material_snapshot,
    export_scene_engine_snapshot,
)
from .opening_assemblies import (
    refresh_opening_assembly_catalog,
    validate_opening_assembly_catalog,
)
from .objaverse import (
    load_objaverse_furniture_narrowing_contract,
    validate_objaverse_furniture_metadata_harvest,
    validate_objaverse_furniture_review_queue,
    validate_objaverse_selective_geometry,
    validate_objaverse_selective_geometry_manifest,
    write_objaverse_selective_geometry_inspection,
    write_objaverse_selective_geometry_manifest,
    write_objaverse_furniture_review_queue,
    write_stub_objaverse_furniture_review_queue,
)
from .paths import default_data_root, default_raw_data_root
from .room_surface_materials import (
    refresh_room_surface_material_catalog,
    validate_room_surface_material_catalog,
)
from .sampling import category_summary, sample_uniform_asset, write_category_index
from .size_normalization import apply_size_normalization
from .support_surfaces import validate_support_surface_annotation_set
from .support_clutter import (
    validate_support_clutter_prop_annotation_set,
    write_ai2thor_support_clutter_measurements,
    write_support_clutter_prop_annotation_set_from_measurements,
)
from .sources import (
    download_objaverse_selective_geometry,
    fetch_poly_haven_room_surface_material,
    generate_objaverse_furniture_review_queue_from_harvest,
    import_objaverse_furniture_metadata_harvest,
    normalize_ai2thor_support_clutter_selection,
    normalize_objaverse_furniture_selection,
    register_ai2thor_support_clutter_selection,
    organize_kenney_ceiling_fixture_selection,
    organize_kenney_selection,
    organize_kenney_opening_selection,
    normalize_poly_haven_room_surface_material,
    rebuild_kenney_selection,
    register_objaverse_raw_metadata_source,
    register_raw_source,
    register_poly_haven_room_surface_material,
    unpack_registered_zip,
    write_poly_haven_room_surface_download_plan,
    write_poly_haven_room_surface_layout_plan,
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

    register_objaverse_metadata_parser = subparsers.add_parser(
        "register-objaverse-raw-metadata-source",
        help="Copy an Objaverse metadata artifact into RAW_DATA_ROOT and write source_manifest.json",
    )
    register_objaverse_metadata_parser.add_argument("spec", type=Path)
    register_objaverse_metadata_parser.add_argument("--raw-file", type=Path, required=True)
    register_objaverse_metadata_parser.add_argument("--raw-data-root", type=Path)
    register_objaverse_metadata_parser.add_argument("--acquired-by")
    register_objaverse_metadata_parser.add_argument("--acquired-at")
    register_objaverse_metadata_parser.add_argument("--notes")

    import_objaverse_metadata_parser = subparsers.add_parser(
        "import-objaverse-furniture-metadata-harvest",
        help="Import a registered Objaverse raw metadata artifact into a schema-valid metadata-harvest file in DATA_ROOT",
    )
    import_objaverse_metadata_parser.add_argument("spec", type=Path)
    import_objaverse_metadata_parser.add_argument("--raw-data-root", type=Path)
    import_objaverse_metadata_parser.add_argument("--data-root", type=Path)
    import_objaverse_metadata_parser.add_argument("--output", type=Path)
    import_objaverse_metadata_parser.add_argument("--created-at")

    generate_objaverse_review_queue_parser = subparsers.add_parser(
        "generate-objaverse-furniture-review-queue",
        help="Generate a rule-based Objaverse review queue from a schema-valid metadata-harvest artifact",
    )
    generate_objaverse_review_queue_parser.add_argument("spec", type=Path)
    generate_objaverse_review_queue_parser.add_argument("--harvest", type=Path, required=True)
    generate_objaverse_review_queue_parser.add_argument("--policy", type=Path, required=True)
    generate_objaverse_review_queue_parser.add_argument("--data-root", type=Path)
    generate_objaverse_review_queue_parser.add_argument("--output", type=Path)
    generate_objaverse_review_queue_parser.add_argument("--contract", type=Path)
    generate_objaverse_review_queue_parser.add_argument("--created-at")

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

    organize_opening_parser = subparsers.add_parser(
        "organize-kenney-opening-selection",
        help="Build the normalized Kenney opening-assembly selection tree in DATA_ROOT from the unpacked source",
    )
    organize_opening_parser.add_argument("selection", type=Path)
    organize_opening_parser.add_argument("--source-spec", type=Path, required=True)
    organize_opening_parser.add_argument(
        "--selection-id",
        action="append",
        dest="selection_ids",
        help="Specific opening selection id to organize; may be passed multiple times",
    )
    organize_opening_parser.add_argument("--raw-data-root", type=Path)
    organize_opening_parser.add_argument("--data-root", type=Path)
    organize_opening_parser.add_argument("--created-at")

    organize_ceiling_fixture_parser = subparsers.add_parser(
        "organize-kenney-ceiling-fixture-selection",
        help="Build the normalized Kenney ceiling-fixture selection tree in DATA_ROOT from the unpacked source",
    )
    organize_ceiling_fixture_parser.add_argument("selection", type=Path)
    organize_ceiling_fixture_parser.add_argument("--source-spec", type=Path, required=True)
    organize_ceiling_fixture_parser.add_argument(
        "--selection-id",
        action="append",
        dest="selection_ids",
        help="Specific ceiling-fixture selection id to organize; may be passed multiple times",
    )
    organize_ceiling_fixture_parser.add_argument("--raw-data-root", type=Path)
    organize_ceiling_fixture_parser.add_argument("--data-root", type=Path)
    organize_ceiling_fixture_parser.add_argument("--created-at")

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

    register_polyhaven_material_parser = subparsers.add_parser(
        "register-poly-haven-room-surface-material",
        help="Register one manually downloaded Poly Haven room-surface material into RAW_DATA_ROOT",
    )
    register_polyhaven_material_parser.add_argument("selection_id")
    register_polyhaven_material_parser.add_argument("--selection", type=Path, required=True)
    register_polyhaven_material_parser.add_argument("--source-spec", type=Path, required=True)
    register_polyhaven_material_parser.add_argument("--raw-material-dir", type=Path, required=True)
    register_polyhaven_material_parser.add_argument("--raw-data-root", type=Path)
    register_polyhaven_material_parser.add_argument("--acquired-at")
    register_polyhaven_material_parser.add_argument("--acquired-by")
    register_polyhaven_material_parser.add_argument("--notes")

    normalize_polyhaven_material_parser = subparsers.add_parser(
        "normalize-poly-haven-room-surface-material",
        help="Normalize one registered Poly Haven room-surface material into DATA_ROOT",
    )
    normalize_polyhaven_material_parser.add_argument("selection_id")
    normalize_polyhaven_material_parser.add_argument("--selection", type=Path, required=True)
    normalize_polyhaven_material_parser.add_argument("--source-spec", type=Path, required=True)
    normalize_polyhaven_material_parser.add_argument("--raw-data-root", type=Path)
    normalize_polyhaven_material_parser.add_argument("--data-root", type=Path)
    normalize_polyhaven_material_parser.add_argument("--created-at")

    fetch_polyhaven_material_parser = subparsers.add_parser(
        "fetch-poly-haven-room-surface-material",
        help="Fetch one Poly Haven room-surface material from the live API into RAW_DATA_ROOT",
    )
    fetch_polyhaven_material_parser.add_argument("selection_id")
    fetch_polyhaven_material_parser.add_argument("--selection", type=Path, required=True)
    fetch_polyhaven_material_parser.add_argument("--source-spec", type=Path, required=True)
    fetch_polyhaven_material_parser.add_argument("--raw-data-root", type=Path)
    fetch_polyhaven_material_parser.add_argument("--acquired-at")
    fetch_polyhaven_material_parser.add_argument("--acquired-by")
    fetch_polyhaven_material_parser.add_argument("--notes")
    fetch_polyhaven_material_parser.add_argument("--user-agent")

    polyhaven_download_plan_parser = subparsers.add_parser(
        "write-poly-haven-room-surface-download-plan",
        help="Write a repo-side Poly Haven room-surface download plan JSON",
    )
    polyhaven_download_plan_parser.add_argument("selection", type=Path)
    polyhaven_download_plan_parser.add_argument("--source-spec", type=Path, required=True)
    polyhaven_download_plan_parser.add_argument("--output", type=Path, required=True)
    polyhaven_download_plan_parser.add_argument("--created-at")

    polyhaven_layout_plan_parser = subparsers.add_parser(
        "write-poly-haven-room-surface-layout-plan",
        help="Write a repo-side normalized bundle layout plan for Poly Haven room-surface materials",
    )
    polyhaven_layout_plan_parser.add_argument("selection", type=Path)
    polyhaven_layout_plan_parser.add_argument("--source-spec", type=Path, required=True)
    polyhaven_layout_plan_parser.add_argument("--output", type=Path, required=True)
    polyhaven_layout_plan_parser.add_argument("--created-at")

    refresh_room_surface_material_catalog_parser = subparsers.add_parser(
        "refresh-room-surface-material-catalog",
        help="Build a room-surface material catalog from normalized bundle manifests and write its index and manifest",
    )
    refresh_room_surface_material_catalog_parser.add_argument(
        "--catalog-id", required=True
    )
    refresh_room_surface_material_catalog_parser.add_argument(
        "--bundle-manifest",
        type=Path,
        action="append",
        required=True,
        dest="bundle_manifests",
    )
    refresh_room_surface_material_catalog_parser.add_argument(
        "--catalog-output", type=Path, required=True
    )
    refresh_room_surface_material_catalog_parser.add_argument(
        "--surface-type-index-output", type=Path, required=True
    )
    refresh_room_surface_material_catalog_parser.add_argument(
        "--manifest-output", type=Path, required=True
    )
    refresh_room_surface_material_catalog_parser.add_argument("--created-at")

    validate_room_surface_material_catalog_parser = subparsers.add_parser(
        "validate-room-surface-material-catalog",
        help="Validate a room-surface material catalog against the local vgm-assets v0 schema",
    )
    validate_room_surface_material_catalog_parser.add_argument("catalog", type=Path)

    refresh_opening_assembly_catalog_parser = subparsers.add_parser(
        "refresh-opening-assembly-catalog",
        help="Build an opening-assembly catalog from normalized bundle manifests and write its index and manifest",
    )
    refresh_opening_assembly_catalog_parser.add_argument("--catalog-id", required=True)
    refresh_opening_assembly_catalog_parser.add_argument(
        "--bundle-manifest",
        type=Path,
        action="append",
        required=True,
        dest="bundle_manifests",
    )
    refresh_opening_assembly_catalog_parser.add_argument(
        "--catalog-output", type=Path, required=True
    )
    refresh_opening_assembly_catalog_parser.add_argument(
        "--opening-type-index-output", type=Path, required=True
    )
    refresh_opening_assembly_catalog_parser.add_argument(
        "--manifest-output", type=Path, required=True
    )
    refresh_opening_assembly_catalog_parser.add_argument("--created-at")

    validate_opening_assembly_catalog_parser = subparsers.add_parser(
        "validate-opening-assembly-catalog",
        help="Validate an opening-assembly catalog against the local vgm-assets v0 schema",
    )
    validate_opening_assembly_catalog_parser.add_argument("catalog", type=Path)

    validate_support_surface_annotation_set_parser = subparsers.add_parser(
        "validate-support-surface-annotation-set",
        help="Validate a local support-surface annotation set against the vgm-assets v1 schema",
    )
    validate_support_surface_annotation_set_parser.add_argument("annotations", type=Path)

    validate_support_clutter_prop_annotation_set_parser = subparsers.add_parser(
        "validate-support-clutter-prop-annotation-set",
        help="Validate a local support-clutter prop annotation set against the vgm-assets v0 schema",
    )
    validate_support_clutter_prop_annotation_set_parser.add_argument("annotations", type=Path)

    write_ai2thor_support_clutter_measurements_parser = subparsers.add_parser(
        "write-ai2thor-support-clutter-measurements",
        help="Derive approximate AI2-THOR prop measurements from Unity prefab colliders and write a measurement report",
    )
    write_ai2thor_support_clutter_measurements_parser.add_argument(
        "--selection-manifest", type=Path, required=True
    )
    write_ai2thor_support_clutter_measurements_parser.add_argument(
        "--output", type=Path, required=True
    )
    write_ai2thor_support_clutter_measurements_parser.add_argument("--raw-data-root", type=Path)
    write_ai2thor_support_clutter_measurements_parser.add_argument("--created-at")

    write_support_clutter_prop_annotations_parser = subparsers.add_parser(
        "write-support-clutter-prop-annotations",
        help="Write a first support-clutter prop annotation set from a measurement report",
    )
    write_support_clutter_prop_annotations_parser.add_argument(
        "--measurements", type=Path, required=True
    )
    write_support_clutter_prop_annotations_parser.add_argument(
        "--output", type=Path, required=True
    )
    write_support_clutter_prop_annotations_parser.add_argument("--created-at")

    register_ai2thor_support_clutter_parser = subparsers.add_parser(
        "register-ai2thor-support-clutter-selection",
        help="Copy the selected local AI2-THOR mug/book source files into RAW_DATA_ROOT",
    )
    register_ai2thor_support_clutter_parser.add_argument("selection", type=Path)
    register_ai2thor_support_clutter_parser.add_argument("--source-repo-root", type=Path)
    register_ai2thor_support_clutter_parser.add_argument(
        "--selection-id", action="append", dest="selection_ids"
    )
    register_ai2thor_support_clutter_parser.add_argument("--raw-data-root", type=Path)
    register_ai2thor_support_clutter_parser.add_argument("--acquired-by")
    register_ai2thor_support_clutter_parser.add_argument("--acquired-at")
    register_ai2thor_support_clutter_parser.add_argument("--notes")

    normalize_ai2thor_support_clutter_parser = subparsers.add_parser(
        "normalize-ai2thor-support-clutter-selection",
        help="Normalize the selected AI2-THOR mug/book raw payloads into DATA_ROOT",
    )
    normalize_ai2thor_support_clutter_parser.add_argument("selection", type=Path)
    normalize_ai2thor_support_clutter_parser.add_argument(
        "--selection-id", action="append", dest="selection_ids"
    )
    normalize_ai2thor_support_clutter_parser.add_argument("--raw-data-root", type=Path)
    normalize_ai2thor_support_clutter_parser.add_argument("--data-root", type=Path)
    normalize_ai2thor_support_clutter_parser.add_argument("--created-at")

    validate_objaverse_metadata_harvest_parser = subparsers.add_parser(
        "validate-objaverse-furniture-metadata-harvest",
        help="Validate an Objaverse furniture metadata-harvest artifact against the local vgm-assets schema",
    )
    validate_objaverse_metadata_harvest_parser.add_argument("harvest", type=Path)

    validate_objaverse_review_queue_parser = subparsers.add_parser(
        "validate-objaverse-furniture-review-queue",
        help="Validate an Objaverse furniture review-queue artifact against the local vgm-assets schema",
    )
    validate_objaverse_review_queue_parser.add_argument("queue", type=Path)

    validate_objaverse_selective_geometry_parser = subparsers.add_parser(
        "validate-objaverse-selective-geometry",
        help="Validate an Objaverse selective-geometry artifact against the local vgm-assets schema",
    )
    validate_objaverse_selective_geometry_parser.add_argument("selection", type=Path)

    validate_objaverse_selective_geometry_manifest_parser = subparsers.add_parser(
        "validate-objaverse-selective-geometry-manifest",
        help="Validate an Objaverse selective-geometry manifest against the local vgm-assets schema",
    )
    validate_objaverse_selective_geometry_manifest_parser.add_argument("manifest", type=Path)

    write_objaverse_selective_geometry_manifest_parser = subparsers.add_parser(
        "write-objaverse-selective-geometry-manifest",
        help="Resolve an accepted Objaverse shortlist against a harvested metadata artifact and write a selective-geometry manifest",
    )
    write_objaverse_selective_geometry_manifest_parser.add_argument(
        "--selection", type=Path, required=True
    )
    write_objaverse_selective_geometry_manifest_parser.add_argument(
        "--harvest", type=Path, required=True
    )
    write_objaverse_selective_geometry_manifest_parser.add_argument(
        "--output", type=Path, required=True
    )
    write_objaverse_selective_geometry_manifest_parser.add_argument("--created-at")

    write_objaverse_selective_geometry_inspection_parser = subparsers.add_parser(
        "write-objaverse-selective-geometry-inspection",
        help="Inspect downloaded Objaverse selective-geometry meshes against a reference catalog and write a scale-suggestion report",
    )
    write_objaverse_selective_geometry_inspection_parser.add_argument(
        "--manifest", type=Path, required=True
    )
    write_objaverse_selective_geometry_inspection_parser.add_argument(
        "--reference-catalog", type=Path, required=True
    )
    write_objaverse_selective_geometry_inspection_parser.add_argument(
        "--output", type=Path, required=True
    )
    write_objaverse_selective_geometry_inspection_parser.add_argument("--raw-data-root", type=Path)
    write_objaverse_selective_geometry_inspection_parser.add_argument("--created-at")

    normalize_objaverse_furniture_selection_parser = subparsers.add_parser(
        "normalize-objaverse-furniture-selection",
        help="Normalize a small Objaverse furniture slice into DATA_ROOT from a reviewed normalization plan",
    )
    normalize_objaverse_furniture_selection_parser.add_argument("--plan", type=Path, required=True)
    normalize_objaverse_furniture_selection_parser.add_argument("--raw-data-root", type=Path)
    normalize_objaverse_furniture_selection_parser.add_argument("--data-root", type=Path)
    normalize_objaverse_furniture_selection_parser.add_argument("--created-at")

    refresh_furniture_asset_catalog_parser = subparsers.add_parser(
        "refresh-furniture-asset-catalog",
        help="Build a furniture asset catalog from normalized bundle manifests and write its index and manifest",
    )
    refresh_furniture_asset_catalog_parser.add_argument("--catalog-id", required=True)
    refresh_furniture_asset_catalog_parser.add_argument(
        "--bundle-manifest",
        type=Path,
        action="append",
        required=True,
        dest="bundle_manifests",
    )
    refresh_furniture_asset_catalog_parser.add_argument("--catalog-output", type=Path, required=True)
    refresh_furniture_asset_catalog_parser.add_argument(
        "--category-index-output", type=Path, required=True
    )
    refresh_furniture_asset_catalog_parser.add_argument("--manifest-output", type=Path, required=True)
    refresh_furniture_asset_catalog_parser.add_argument("--created-at")

    download_objaverse_selective_geometry_parser = subparsers.add_parser(
        "download-objaverse-selective-geometry",
        help="Download only the accepted Objaverse shortlist from a selective-geometry manifest and register the raw payloads under RAW_DATA_ROOT",
    )
    download_objaverse_selective_geometry_parser.add_argument(
        "--manifest", type=Path, required=True
    )
    download_objaverse_selective_geometry_parser.add_argument("--raw-data-root", type=Path)
    download_objaverse_selective_geometry_parser.add_argument(
        "--download-processes", type=int, default=2
    )
    download_objaverse_selective_geometry_parser.add_argument(
        "--download-previews", action="store_true"
    )
    download_objaverse_selective_geometry_parser.add_argument("--acquired-by")
    download_objaverse_selective_geometry_parser.add_argument("--acquired-at")
    download_objaverse_selective_geometry_parser.add_argument("--notes")

    write_stub_objaverse_review_queue_parser = subparsers.add_parser(
        "write-stub-objaverse-furniture-review-queue",
        help="Validate Objaverse planning inputs and write a schema-valid stub review queue",
    )
    write_stub_objaverse_review_queue_parser.add_argument(
        "--harvest", type=Path, required=True
    )
    write_stub_objaverse_review_queue_parser.add_argument(
        "--policy", type=Path, required=True
    )
    write_stub_objaverse_review_queue_parser.add_argument(
        "--output", type=Path, required=True
    )
    write_stub_objaverse_review_queue_parser.add_argument(
        "--contract", type=Path
    )
    write_stub_objaverse_review_queue_parser.add_argument("--created-at")

    narrow_objaverse_harvest_parser = subparsers.add_parser(
        "narrow-objaverse-furniture-harvest",
        help="Run the first rule-based Objaverse furniture narrowing pass and write a review queue",
    )
    narrow_objaverse_harvest_parser.add_argument("--harvest", type=Path, required=True)
    narrow_objaverse_harvest_parser.add_argument("--policy", type=Path, required=True)
    narrow_objaverse_harvest_parser.add_argument("--output", type=Path, required=True)
    narrow_objaverse_harvest_parser.add_argument("--contract", type=Path)
    narrow_objaverse_harvest_parser.add_argument("--created-at")

    refresh_ceiling_light_fixture_catalog_parser = subparsers.add_parser(
        "refresh-ceiling-light-fixture-catalog",
        help="Build a ceiling-light fixture catalog from normalized bundle manifests and write its index and manifest",
    )
    refresh_ceiling_light_fixture_catalog_parser.add_argument("--catalog-id", required=True)
    refresh_ceiling_light_fixture_catalog_parser.add_argument(
        "--bundle-manifest",
        type=Path,
        action="append",
        required=True,
        dest="bundle_manifests",
    )
    refresh_ceiling_light_fixture_catalog_parser.add_argument(
        "--catalog-output", type=Path, required=True
    )
    refresh_ceiling_light_fixture_catalog_parser.add_argument(
        "--fixture-index-output", type=Path, required=True
    )
    refresh_ceiling_light_fixture_catalog_parser.add_argument(
        "--manifest-output", type=Path, required=True
    )
    refresh_ceiling_light_fixture_catalog_parser.add_argument("--created-at")

    validate_ceiling_light_fixture_catalog_parser = subparsers.add_parser(
        "validate-ceiling-light-fixture-catalog",
        help="Validate a ceiling-light fixture catalog against the local vgm-assets v0 schema",
    )
    validate_ceiling_light_fixture_catalog_parser.add_argument("catalog", type=Path)

    refresh_parser = subparsers.add_parser(
        "refresh-catalog-artifacts",
        help="Validate a catalog, refresh its measurement report, and write its manifest",
    )
    refresh_parser.add_argument("catalog", type=Path)
    refresh_parser.add_argument("--catalog-id", required=True)
    refresh_parser.add_argument("--manifest-output", type=Path, required=True)
    refresh_parser.add_argument("--measure-output", type=Path)
    refresh_parser.add_argument("--category-index-output", type=Path)
    refresh_parser.add_argument("--protocol-root", type=Path)
    refresh_parser.add_argument("--created-at")

    normalize_sizes_parser = subparsers.add_parser(
        "apply-size-normalization",
        help="Apply a repo-side size-normalization plan to an asset catalog",
    )
    normalize_sizes_parser.add_argument("catalog", type=Path)
    normalize_sizes_parser.add_argument("--plan", type=Path, required=True)
    normalize_sizes_parser.add_argument("--output", type=Path)

    summary_parser = subparsers.add_parser(
        "summarize-categories",
        help="Print category counts and current v0 sampling policy for a catalog",
    )
    summary_parser.add_argument("catalog", type=Path)
    summary_parser.add_argument("--pretty", action="store_true")

    sample_parser = subparsers.add_parser(
        "sample-category-asset",
        help="Sample one asset uniformly at random from a category",
    )
    sample_parser.add_argument("catalog", type=Path)
    sample_parser.add_argument("category")
    sample_parser.add_argument("--seed", type=int)
    sample_parser.add_argument("--pretty", action="store_true")

    index_parser = subparsers.add_parser(
        "write-category-index",
        help="Write a category-to-asset-id index JSON for a catalog",
    )
    index_parser.add_argument("catalog", type=Path)
    index_parser.add_argument("--output", type=Path, required=True)
    index_parser.add_argument("--pretty", action="store_true")

    export_parser = subparsers.add_parser(
        "export-scene-engine-snapshot",
        help="Export a frozen scene-engine snapshot from current catalog artifacts",
    )
    export_parser.add_argument("--export-id", required=True)
    export_parser.add_argument("--source-catalog-id", required=True)
    export_parser.add_argument("--catalog", type=Path, required=True)
    export_parser.add_argument("--category-index", type=Path, required=True)
    export_parser.add_argument("--manifest", type=Path, required=True)
    export_parser.add_argument("--output-dir", type=Path, required=True)
    export_parser.add_argument("--notes")

    material_export_parser = subparsers.add_parser(
        "export-room-surface-material-snapshot",
        help="Export a frozen scene-engine snapshot from room-surface material catalog artifacts",
    )
    material_export_parser.add_argument("--export-id", required=True)
    material_export_parser.add_argument("--source-catalog-id", required=True)
    material_export_parser.add_argument("--catalog", type=Path, required=True)
    material_export_parser.add_argument("--surface-type-index", type=Path, required=True)
    material_export_parser.add_argument("--manifest", type=Path, required=True)
    material_export_parser.add_argument("--output-dir", type=Path, required=True)
    material_export_parser.add_argument("--notes")

    opening_export_parser = subparsers.add_parser(
        "export-opening-assembly-snapshot",
        help="Export a frozen scene-engine snapshot from opening-assembly catalog artifacts",
    )
    opening_export_parser.add_argument("--export-id", required=True)
    opening_export_parser.add_argument("--source-catalog-id", required=True)
    opening_export_parser.add_argument("--catalog", type=Path, required=True)
    opening_export_parser.add_argument("--opening-type-index", type=Path, required=True)
    opening_export_parser.add_argument("--manifest", type=Path, required=True)
    opening_export_parser.add_argument("--output-dir", type=Path, required=True)
    opening_export_parser.add_argument("--notes")

    ceiling_fixture_export_parser = subparsers.add_parser(
        "export-ceiling-light-fixture-snapshot",
        help="Export a frozen scene-engine snapshot from ceiling-light fixture catalog artifacts",
    )
    ceiling_fixture_export_parser.add_argument("--export-id", required=True)
    ceiling_fixture_export_parser.add_argument("--source-catalog-id", required=True)
    ceiling_fixture_export_parser.add_argument("--catalog", type=Path, required=True)
    ceiling_fixture_export_parser.add_argument("--fixture-index", type=Path, required=True)
    ceiling_fixture_export_parser.add_argument("--manifest", type=Path, required=True)
    ceiling_fixture_export_parser.add_argument("--output-dir", type=Path, required=True)
    ceiling_fixture_export_parser.add_argument("--notes")

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

    if args.command == "register-objaverse-raw-metadata-source":
        manifest = register_objaverse_raw_metadata_source(
            spec_path=args.spec,
            raw_file=args.raw_file,
            raw_data_root=args.raw_data_root,
            acquired_by=args.acquired_by,
            acquired_at=args.acquired_at,
            notes=args.notes,
        )
        print(json.dumps(manifest, indent=2))
        return 0

    if args.command == "import-objaverse-furniture-metadata-harvest":
        summary = import_objaverse_furniture_metadata_harvest(
            spec_path=args.spec,
            raw_data_root=args.raw_data_root,
            data_root=args.data_root,
            output_path=args.output,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "generate-objaverse-furniture-review-queue":
        if args.contract is not None:
            load_objaverse_furniture_narrowing_contract(args.contract)
        summary = generate_objaverse_furniture_review_queue_from_harvest(
            spec_path=args.spec,
            harvest_path=args.harvest,
            policy_path=args.policy,
            data_root=args.data_root,
            output_path=args.output,
            contract_path=args.contract,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
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

    if args.command == "organize-kenney-opening-selection":
        summary = organize_kenney_opening_selection(
            spec_path=args.source_spec,
            selection_path=args.selection,
            selection_ids=args.selection_ids,
            raw_data_root=args.raw_data_root,
            data_root=args.data_root,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "organize-kenney-ceiling-fixture-selection":
        summary = organize_kenney_ceiling_fixture_selection(
            spec_path=args.source_spec,
            selection_path=args.selection,
            selection_ids=args.selection_ids,
            raw_data_root=args.raw_data_root,
            data_root=args.data_root,
            created_at=args.created_at,
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

    if args.command == "register-poly-haven-room-surface-material":
        summary = register_poly_haven_room_surface_material(
            spec_path=args.source_spec,
            selection_path=args.selection,
            selection_id=args.selection_id,
            raw_material_dir=args.raw_material_dir,
            raw_data_root=args.raw_data_root,
            acquired_at=args.acquired_at,
            acquired_by=args.acquired_by,
            notes=args.notes,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "normalize-poly-haven-room-surface-material":
        summary = normalize_poly_haven_room_surface_material(
            spec_path=args.source_spec,
            selection_path=args.selection,
            selection_id=args.selection_id,
            raw_data_root=args.raw_data_root,
            data_root=args.data_root,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "fetch-poly-haven-room-surface-material":
        summary = fetch_poly_haven_room_surface_material(
            spec_path=args.source_spec,
            selection_path=args.selection,
            selection_id=args.selection_id,
            raw_data_root=args.raw_data_root,
            acquired_at=args.acquired_at,
            acquired_by=args.acquired_by,
            notes=args.notes,
            user_agent=args.user_agent,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "write-poly-haven-room-surface-download-plan":
        summary = write_poly_haven_room_surface_download_plan(
            spec_path=args.source_spec,
            selection_path=args.selection,
            output_path=args.output,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "write-poly-haven-room-surface-layout-plan":
        summary = write_poly_haven_room_surface_layout_plan(
            spec_path=args.source_spec,
            selection_path=args.selection,
            output_path=args.output,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "refresh-room-surface-material-catalog":
        summary = refresh_room_surface_material_catalog(
            catalog_id=args.catalog_id,
            bundle_manifest_paths=args.bundle_manifests,
            catalog_output=args.catalog_output,
            surface_type_index_output=args.surface_type_index_output,
            manifest_output=args.manifest_output,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "validate-room-surface-material-catalog":
        records = validate_room_surface_material_catalog(args.catalog)
        print(f"Validated {len(records)} room-surface materials in {args.catalog}")
        return 0

    if args.command == "refresh-opening-assembly-catalog":
        summary = refresh_opening_assembly_catalog(
            catalog_id=args.catalog_id,
            bundle_manifest_paths=args.bundle_manifests,
            catalog_output=args.catalog_output,
            opening_type_index_output=args.opening_type_index_output,
            manifest_output=args.manifest_output,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "validate-opening-assembly-catalog":
        records = validate_opening_assembly_catalog(args.catalog)
        print(f"Validated {len(records)} opening assemblies in {args.catalog}")
        return 0

    if args.command == "validate-support-surface-annotation-set":
        payload = validate_support_surface_annotation_set(args.annotations)
        print(
            f"Validated support-surface annotation set {payload['annotation_set_id']} "
            f"with {len(payload['assets'])} assets in {args.annotations}"
        )
        return 0

    if args.command == "validate-support-clutter-prop-annotation-set":
        payload = validate_support_clutter_prop_annotation_set(args.annotations)
        print(
            f"Validated support-clutter prop annotation set {payload['annotation_set_id']} "
            f"with {len(payload['props'])} props in {args.annotations}"
        )
        return 0

    if args.command == "write-ai2thor-support-clutter-measurements":
        summary = write_ai2thor_support_clutter_measurements(
            selection_manifest_path=args.selection_manifest,
            output_path=args.output,
            raw_data_root=args.raw_data_root,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "write-support-clutter-prop-annotations":
        summary = write_support_clutter_prop_annotation_set_from_measurements(
            measurements_path=args.measurements,
            output_path=args.output,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "register-ai2thor-support-clutter-selection":
        summary = register_ai2thor_support_clutter_selection(
            selection_path=args.selection,
            source_repo_root=args.source_repo_root,
            selection_ids=args.selection_ids,
            raw_data_root=args.raw_data_root,
            acquired_by=args.acquired_by,
            acquired_at=args.acquired_at,
            notes=args.notes,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "normalize-ai2thor-support-clutter-selection":
        summary = normalize_ai2thor_support_clutter_selection(
            selection_path=args.selection,
            selection_ids=args.selection_ids,
            raw_data_root=args.raw_data_root,
            data_root=args.data_root,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "validate-objaverse-furniture-metadata-harvest":
        payload = validate_objaverse_furniture_metadata_harvest(args.harvest)
        print(
            f"Validated {payload['record_count']} Objaverse harvested records in {args.harvest}"
        )
        return 0

    if args.command == "validate-objaverse-furniture-review-queue":
        payload = validate_objaverse_furniture_review_queue(args.queue)
        print(
            f"Validated {payload['candidate_count']} Objaverse review candidates in {args.queue}"
        )
        return 0

    if args.command == "validate-objaverse-selective-geometry":
        payload = validate_objaverse_selective_geometry(args.selection)
        print(
            f"Validated {payload['selected_count']} Objaverse selective geometry candidates in {args.selection}"
        )
        return 0

    if args.command == "validate-objaverse-selective-geometry-manifest":
        payload = validate_objaverse_selective_geometry_manifest(args.manifest)
        print(
            f"Validated {payload['candidate_count']} Objaverse selective geometry manifest candidates in {args.manifest}"
        )
        return 0

    if args.command == "write-objaverse-selective-geometry-manifest":
        summary = write_objaverse_selective_geometry_manifest(
            selection_path=args.selection,
            harvest_path=args.harvest,
            output_path=args.output,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "write-objaverse-selective-geometry-inspection":
        summary = write_objaverse_selective_geometry_inspection(
            manifest_path=args.manifest,
            reference_catalog_path=args.reference_catalog,
            raw_data_root=args.raw_data_root,
            output_path=args.output,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "normalize-objaverse-furniture-selection":
        summary = normalize_objaverse_furniture_selection(
            plan_path=args.plan,
            raw_data_root=args.raw_data_root,
            data_root=args.data_root,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "download-objaverse-selective-geometry":
        summary = download_objaverse_selective_geometry(
            manifest_path=args.manifest,
            raw_data_root=args.raw_data_root,
            download_processes=args.download_processes,
            download_previews=args.download_previews,
            acquired_by=args.acquired_by,
            acquired_at=args.acquired_at,
            notes=args.notes,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "write-stub-objaverse-furniture-review-queue":
        if args.contract is not None:
            load_objaverse_furniture_narrowing_contract(args.contract)
        summary = write_stub_objaverse_furniture_review_queue(
            harvest_path=args.harvest,
            policy_path=args.policy,
            output_path=args.output,
            contract_path=args.contract,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "narrow-objaverse-furniture-harvest":
        if args.contract is not None:
            load_objaverse_furniture_narrowing_contract(args.contract)
        summary = write_objaverse_furniture_review_queue(
            harvest_path=args.harvest,
            policy_path=args.policy,
            output_path=args.output,
            contract_path=args.contract,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "refresh-ceiling-light-fixture-catalog":
        summary = refresh_ceiling_light_fixture_catalog(
            catalog_id=args.catalog_id,
            bundle_manifest_paths=args.bundle_manifests,
            catalog_output=args.catalog_output,
            fixture_index_output=args.fixture_index_output,
            manifest_output=args.manifest_output,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "refresh-furniture-asset-catalog":
        summary = refresh_furniture_asset_catalog(
            catalog_id=args.catalog_id,
            bundle_manifest_paths=args.bundle_manifests,
            catalog_output=args.catalog_output,
            category_index_output=args.category_index_output,
            manifest_output=args.manifest_output,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "validate-ceiling-light-fixture-catalog":
        records = validate_ceiling_light_fixture_catalog(args.catalog)
        print(f"Validated {len(records)} ceiling-light fixtures in {args.catalog}")
        return 0

    if args.command == "refresh-catalog-artifacts":
        summary = refresh_catalog_artifacts(
            catalog_path=args.catalog,
            catalog_id=args.catalog_id,
            manifest_output=args.manifest_output,
            measure_output=args.measure_output,
            category_index_output=args.category_index_output,
            protocol_root=args.protocol_root,
            created_at=args.created_at,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "apply-size-normalization":
        summary = apply_size_normalization(
            catalog_path=args.catalog,
            plan_path=args.plan,
            output_path=args.output,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "summarize-categories":
        summary = category_summary(args.catalog)
        print(json.dumps(summary, indent=2 if args.pretty else None))
        return 0

    if args.command == "sample-category-asset":
        summary = sample_uniform_asset(
            catalog_path=args.catalog,
            category=args.category,
            seed=args.seed,
        )
        print(json.dumps(summary, indent=2 if args.pretty else None))
        return 0

    if args.command == "write-category-index":
        index = write_category_index(args.catalog, args.output)
        if args.pretty:
            print(json.dumps(index, indent=2))
        else:
            print(
                json.dumps(
                    {
                        "catalog_path": index["catalog_path"],
                        "output": str(args.output.resolve()),
                        "category_count": index["category_count"],
                    }
                )
            )
        return 0

    if args.command == "export-scene-engine-snapshot":
        summary = export_scene_engine_snapshot(
            export_id=args.export_id,
            source_catalog_id=args.source_catalog_id,
            catalog_path=args.catalog,
            category_index_path=args.category_index,
            manifest_path=args.manifest,
            output_dir=args.output_dir,
            notes=args.notes,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "export-room-surface-material-snapshot":
        summary = export_room_surface_material_snapshot(
            export_id=args.export_id,
            source_catalog_id=args.source_catalog_id,
            catalog_path=args.catalog,
            surface_type_index_path=args.surface_type_index,
            manifest_path=args.manifest,
            output_dir=args.output_dir,
            notes=args.notes,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "export-opening-assembly-snapshot":
        summary = export_opening_assembly_snapshot(
            export_id=args.export_id,
            source_catalog_id=args.source_catalog_id,
            catalog_path=args.catalog,
            opening_type_index_path=args.opening_type_index,
            manifest_path=args.manifest,
            output_dir=args.output_dir,
            notes=args.notes,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "export-ceiling-light-fixture-snapshot":
        summary = export_ceiling_light_fixture_snapshot(
            export_id=args.export_id,
            source_catalog_id=args.source_catalog_id,
            catalog_path=args.catalog,
            fixture_index_path=args.fixture_index,
            manifest_path=args.manifest,
            output_dir=args.output_dir,
            notes=args.notes,
        )
        print(json.dumps(summary, indent=2))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
