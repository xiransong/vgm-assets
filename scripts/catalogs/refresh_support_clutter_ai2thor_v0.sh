#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DATA_ROOT="${VGM_ASSETS_DATA_ROOT:-$HOME/scratch/processed/vgm/vgm-assets}"
SELECTION_MANIFEST="${DATA_ROOT}/assets/props/ai2thor/support_clutter_v0/selection_manifest.json"
MEASUREMENTS="${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/measurements.json"
PROP_ANNOTATIONS="${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/prop_annotations_v0.json"
SUPPORT_SURFACE_ANNOTATIONS="${ROOT_DIR}/catalogs/living_room_kenney_v0/support_surface_annotations_v1.json"
CATALOG_OUTPUT="${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/assets.json"
CATEGORY_INDEX_OUTPUT="${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/category_index.json"
SUPPORT_COMPATIBILITY_OUTPUT="${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/support_compatibility.json"
MANIFEST_OUTPUT="${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/asset_catalog_manifest.json"

created_at_args=()

while (($#)); do
  case "$1" in
    --selection-manifest)
      SELECTION_MANIFEST="$2"
      shift 2
      ;;
    --created-at)
      created_at_args+=("$1" "$2")
      shift 2
      ;;
    *)
      echo "Unsupported argument for refresh_support_clutter_ai2thor_v0.sh: $1" >&2
      exit 2
      ;;
  esac
done

cd "${ROOT_DIR}"

bash ./scripts/catalogs/refresh_ai2thor_support_clutter_metadata_v0.sh "${created_at_args[@]}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  refresh-support-clutter-asset-catalog \
  --catalog-id support_clutter_ai2thor_v0 \
  --selection-manifest "${SELECTION_MANIFEST}" \
  --measurements "${MEASUREMENTS}" \
  --prop-annotations "${PROP_ANNOTATIONS}" \
  --support-surface-annotations "${SUPPORT_SURFACE_ANNOTATIONS}" \
  --catalog-output "${CATALOG_OUTPUT}" \
  --category-index-output "${CATEGORY_INDEX_OUTPUT}" \
  --support-compatibility-output "${SUPPORT_COMPATIBILITY_OUTPUT}" \
  --manifest-output "${MANIFEST_OUTPUT}" \
  "${created_at_args[@]}"
