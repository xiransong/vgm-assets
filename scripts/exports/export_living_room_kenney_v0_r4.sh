#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  export-scene-engine-snapshot-with-support-annotations \
  --export-id living_room_kenney_v0_r4 \
  --source-catalog-id living_room_kenney_v0 \
  --catalog catalogs/living_room_kenney_v0/assets.json \
  --category-index catalogs/living_room_kenney_v0/category_index.json \
  --manifest catalogs/living_room_kenney_v0/asset_catalog_manifest.json \
  --support-annotations catalogs/living_room_kenney_v0/support_surface_annotations_v1.json \
  --output-dir exports/scene_engine/living_room_kenney_v0_r4 \
  --notes "Frozen size-normalized snapshot with protocol-aligned support_surfaces_v1, thin compatibility support, and local support-surface companion annotations."
