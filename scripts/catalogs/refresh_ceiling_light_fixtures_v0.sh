#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  refresh-ceiling-light-fixture-catalog \
  --catalog-id ceiling_light_fixtures_v0 \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/fixtures/ceiling/kenney/ceiling_light_fixtures_v0/kenney_lamp_square_ceiling_01/bundle_manifest.json \
  --catalog-output catalogs/ceiling_light_fixtures_v0/fixtures.json \
  --fixture-index-output catalogs/ceiling_light_fixtures_v0/fixture_index.json \
  --manifest-output catalogs/ceiling_light_fixtures_v0/fixture_catalog_manifest.json
