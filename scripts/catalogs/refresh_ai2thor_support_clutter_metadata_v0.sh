#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

RAW_DATA_ROOT="${VGM_ASSETS_RAW_DATA_ROOT:-$HOME/scratch/data/vgm/vgm-assets}"
DATA_ROOT="${VGM_ASSETS_DATA_ROOT:-$HOME/scratch/processed/vgm/vgm-assets}"
SELECTION_MANIFEST="${DATA_ROOT}/assets/props/ai2thor/support_clutter_v0/selection_manifest.json"
MEASUREMENTS_OUTPUT="${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/measurements.json"
ANNOTATIONS_OUTPUT="${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/prop_annotations_v0.json"

created_at_args=()

while (($#)); do
  case "$1" in
    --raw-data-root)
      RAW_DATA_ROOT="$2"
      shift 2
      ;;
    --selection-manifest)
      SELECTION_MANIFEST="$2"
      shift 2
      ;;
    --created-at)
      created_at_args+=("$1" "$2")
      shift 2
      ;;
    *)
      echo "Unsupported argument for refresh_ai2thor_support_clutter_metadata_v0.sh: $1" >&2
      exit 2
      ;;
  esac
done

mkdir -p "$(dirname "${MEASUREMENTS_OUTPUT}")"

cd "${ROOT_DIR}"
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  write-ai2thor-support-clutter-measurements \
  --selection-manifest "${SELECTION_MANIFEST}" \
  --output "${MEASUREMENTS_OUTPUT}" \
  --raw-data-root "${RAW_DATA_ROOT}" \
  "${created_at_args[@]}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  write-support-clutter-prop-annotations \
  --measurements "${MEASUREMENTS_OUTPUT}" \
  --output "${ANNOTATIONS_OUTPUT}" \
  "${created_at_args[@]}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  validate-support-clutter-prop-annotation-set \
  "${ANNOTATIONS_OUTPUT}"
