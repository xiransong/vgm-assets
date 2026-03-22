#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  export-wall-fixture-snapshot \
  --export-id wall_fixtures_v0_r1 \
  --source-catalog-id wall_fixtures_v0 \
  --catalog catalogs/wall_fixtures_v0/wall_fixture_catalog.json \
  --fixture-category-index catalogs/wall_fixtures_v0/fixture_category_index.json \
  --manifest catalogs/wall_fixtures_v0/fixture_catalog_manifest.json \
  --output-dir exports/scene_engine/wall_fixtures_v0_r1 \
  --notes "Frozen v0 wall-fixture snapshot for vgm-scene-engine. First metadata-reviewed manual pair: one framed painting and one wall clock."
