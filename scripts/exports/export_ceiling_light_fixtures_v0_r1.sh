#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  export-ceiling-light-fixture-snapshot \
  --export-id ceiling_light_fixtures_v0_r1 \
  --source-catalog-id ceiling_light_fixtures_v0 \
  --catalog catalogs/ceiling_light_fixtures_v0/fixtures.json \
  --fixture-index catalogs/ceiling_light_fixtures_v0/fixture_index.json \
  --manifest catalogs/ceiling_light_fixtures_v0/fixture_catalog_manifest.json \
  --output-dir exports/scene_engine/ceiling_light_fixtures_v0_r1 \
  --notes "Frozen v0 ceiling-light fixture snapshot for vgm-scene-engine. Single Kenney flush-mount ceiling fixture."
