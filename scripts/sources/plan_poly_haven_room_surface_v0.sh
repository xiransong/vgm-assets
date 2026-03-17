#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  write-poly-haven-room-surface-download-plan \
  sources/poly_haven/room_surface_selection_v0.json \
  --source-spec sources/poly_haven/source_spec_v0.json \
  --output sources/poly_haven/room_surface_download_plan_v0.json

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  write-poly-haven-room-surface-layout-plan \
  sources/poly_haven/room_surface_selection_v0.json \
  --source-spec sources/poly_haven/source_spec_v0.json \
  --output materials/poly_haven/room_surface_bundle_layout_v0.json
