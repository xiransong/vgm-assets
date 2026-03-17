#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <selection_id> <raw_material_dir>" >&2
  exit 2
fi

SELECTION_ID="$1"
RAW_MATERIAL_DIR="$2"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  register-poly-haven-room-surface-material \
  "${SELECTION_ID}" \
  --selection sources/poly_haven/room_surface_selection_v0.json \
  --source-spec sources/poly_haven/source_spec_v0.json \
  --raw-material-dir "${RAW_MATERIAL_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  normalize-poly-haven-room-surface-material \
  "${SELECTION_ID}" \
  --selection sources/poly_haven/room_surface_selection_v0.json \
  --source-spec sources/poly_haven/source_spec_v0.json
