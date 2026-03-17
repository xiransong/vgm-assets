#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"
PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  export-opening-assembly-snapshot \
  --export-id opening_assemblies_v0_r1 \
  --source-catalog-id opening_assemblies_v0 \
  --catalog catalogs/opening_assemblies_v0/assemblies.json \
  --opening-type-index catalogs/opening_assemblies_v0/opening_type_index.json \
  --manifest catalogs/opening_assemblies_v0/assembly_catalog_manifest.json \
  --output-dir exports/scene_engine/opening_assemblies_v0_r1 \
  --notes "Frozen opening-assembly snapshot for vgm-scene-engine consumption."
