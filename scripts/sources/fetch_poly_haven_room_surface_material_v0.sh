#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <selection_id>" >&2
  exit 2
fi

SELECTION_ID="$1"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  fetch-poly-haven-room-surface-material \
  "${SELECTION_ID}" \
  --selection sources/poly_haven/room_surface_selection_v0.json \
  --source-spec sources/poly_haven/source_spec_v0.json

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  normalize-poly-haven-room-surface-material \
  "${SELECTION_ID}" \
  --selection sources/poly_haven/room_surface_selection_v0.json \
  --source-spec sources/poly_haven/source_spec_v0.json
