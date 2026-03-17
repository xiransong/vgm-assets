#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  organize-kenney-ceiling-fixture-selection \
  sources/kenney/ceiling_fixture_selection_v0.json \
  --source-spec sources/kenney/source_spec_v0.json \
  --selection-id kenney_ceiling_fixture_lamp_square_ceiling_v0
