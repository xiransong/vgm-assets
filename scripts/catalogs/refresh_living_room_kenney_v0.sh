#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_NAME="${VGM_ASSETS_ENV_NAME:-vgm-assets}"

cd "${ROOT_DIR}"
source scripts/lib/micromamba.sh
"${MAMBA_EXE}" run -n "${ENV_NAME}" python tools/validate_asset_catalog.py \
  refresh-catalog-artifacts \
  catalogs/living_room_kenney_v0/assets.json \
  --catalog-id living_room_kenney_v0 \
  --measure-output catalogs/living_room_kenney_v0/measurements.json \
  --category-index-output catalogs/living_room_kenney_v0/category_index.json \
  --manifest-output catalogs/living_room_kenney_v0/asset_catalog_manifest.json
