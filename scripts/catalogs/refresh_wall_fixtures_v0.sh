#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  refresh-wall-fixture-catalog \
  --catalog-id wall_fixtures_v0 \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/fixtures/wall/manual/wall_fixtures_v0/painting/manual_painting_01/bundle_manifest.json \
  --bundle-manifest /home/ubuntu/scratch/processed/vgm/vgm-assets/fixtures/wall/manual/wall_fixtures_v0/clock/manual_clock_01/bundle_manifest.json \
  --catalog-output catalogs/wall_fixtures_v0/wall_fixture_catalog.json \
  --fixture-category-index-output catalogs/wall_fixtures_v0/fixture_category_index.json \
  --manifest-output catalogs/wall_fixtures_v0/fixture_catalog_manifest.json
