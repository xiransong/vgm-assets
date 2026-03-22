#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  organize-manual-wall-fixture-selection \
  sources/manual/wall_fixture_selection_v0.json \
  --source-spec sources/manual/wall_fixture_source_spec_v0.json
