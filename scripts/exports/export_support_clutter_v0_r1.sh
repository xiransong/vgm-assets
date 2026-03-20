#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_DIR="${ROOT_DIR}/exports/scene_engine/support_clutter_v0_r1"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  export-support-clutter-snapshot \
  --export-id support_clutter_v0_r1 \
  --source-catalog-id support_clutter_ai2thor_v0 \
  --catalog "${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/assets.json" \
  --category-index "${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/category_index.json" \
  --support-compatibility "${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/support_compatibility.json" \
  --manifest "${ROOT_DIR}/catalogs/support_clutter_ai2thor_v0/asset_catalog_manifest.json" \
  --output-dir "${OUTPUT_DIR}" \
  "$@"
