#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  export-room-surface-material-snapshot \
  --export-id room_surface_materials_v0_r1 \
  --source-catalog-id room_surface_materials_v0 \
  --catalog catalogs/room_surface_materials_v0/materials.json \
  --surface-type-index catalogs/room_surface_materials_v0/surface_type_index.json \
  --manifest catalogs/room_surface_materials_v0/material_catalog_manifest.json \
  --output-dir exports/scene_engine/room_surface_materials_v0_r1 \
  --notes "Frozen room-surface material snapshot for vgm-scene-engine consumption."
