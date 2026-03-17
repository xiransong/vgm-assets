#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  refresh-room-surface-material-catalog \
  --catalog-id room_surface_materials_v0 \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/materials/room_surfaces/poly_haven/floor/polyhaven_wood_floor_01/bundle_manifest.json \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/materials/room_surfaces/poly_haven/floor/polyhaven_laminate_floor_02/bundle_manifest.json \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/materials/room_surfaces/poly_haven/wall/polyhaven_white_plaster_wall_02/bundle_manifest.json \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/materials/room_surfaces/poly_haven/wall/polyhaven_plaster_grey_wall_04/bundle_manifest.json \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/materials/room_surfaces/poly_haven/ceiling/polyhaven_white_plaster_ceiling_02/bundle_manifest.json \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/materials/room_surfaces/poly_haven/ceiling/polyhaven_plaster_grey_ceiling_04/bundle_manifest.json \
  --catalog-output catalogs/room_surface_materials_v0/materials.json \
  --surface-type-index-output catalogs/room_surface_materials_v0/surface_type_index.json \
  --manifest-output catalogs/room_surface_materials_v0/material_catalog_manifest.json
