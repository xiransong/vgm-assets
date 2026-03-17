#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  refresh-opening-assembly-catalog \
  --catalog-id opening_assemblies_v0 \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/assemblies/openings/kenney/opening_assemblies_v0/door/kenney_wall_doorway_01/bundle_manifest.json \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/assemblies/openings/kenney/opening_assemblies_v0/window/kenney_wall_window_01/bundle_manifest.json \
  --catalog-output catalogs/opening_assemblies_v0/assemblies.json \
  --opening-type-index-output catalogs/opening_assemblies_v0/opening_type_index.json \
  --manifest-output catalogs/opening_assemblies_v0/assembly_catalog_manifest.json
