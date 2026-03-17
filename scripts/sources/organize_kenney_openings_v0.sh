#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  organize-kenney-opening-selection \
  sources/kenney/opening_selection_v0.json \
  --source-spec sources/kenney/source_spec_v0.json \
  --selection-id kenney_opening_door_wall_doorway_v0 \
  --selection-id kenney_opening_window_wall_window_v0
