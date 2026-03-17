#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  export-scene-engine-snapshot \
  --export-id living_room_kenney_v0_r1 \
  --source-catalog-id living_room_kenney_v0 \
  --catalog catalogs/living_room_kenney_v0/assets.json \
  --category-index catalogs/living_room_kenney_v0/category_index.json \
  --manifest catalogs/living_room_kenney_v0/asset_catalog_manifest.json \
  --output-dir exports/scene_engine/living_room_kenney_v0_r1 \
  --notes "Frozen snapshot for vgm-scene-engine consumption."
