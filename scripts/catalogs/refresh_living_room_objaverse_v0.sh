#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_NAME="${VGM_ASSETS_ENV_NAME:-vgm-assets}"
CATALOG_DIR="${ROOT_DIR}/catalogs/living_room_objaverse_v0"
DATA_ROOT="${VGM_ASSETS_DATA_ROOT:-${HOME}/scratch/processed/vgm/vgm-assets}"

source "${ROOT_DIR}/scripts/lib/micromamba.sh"

declare -a BUNDLE_MANIFESTS=(
  "${DATA_ROOT}/assets/furniture/objaverse/living_room_objaverse_v0/sofa/objaverse_leather_fabric_sofa_01/bundle_manifest.json"
  "${DATA_ROOT}/assets/furniture/objaverse/living_room_objaverse_v0/coffee_table/objaverse_table_70s_01/bundle_manifest.json"
  "${DATA_ROOT}/assets/furniture/objaverse/living_room_objaverse_v0/side_table/objaverse_nightstand_01/bundle_manifest.json"
)

CMD=(
  "${MAMBA_EXE}" run -n "${ENV_NAME}" python
  "${ROOT_DIR}/tools/validate_asset_catalog.py"
  refresh-furniture-asset-catalog
  --catalog-id "living_room_objaverse_v0"
  --catalog-output "${CATALOG_DIR}/assets.json"
  --category-index-output "${CATALOG_DIR}/category_index.json"
  --manifest-output "${CATALOG_DIR}/asset_catalog_manifest.json"
)

for bundle in "${BUNDLE_MANIFESTS[@]}"; do
  CMD+=(--bundle-manifest "${bundle}")
done

"${CMD[@]}" "$@"
