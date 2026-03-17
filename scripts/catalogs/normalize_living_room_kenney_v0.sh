#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

PYTHONPATH=src python3 tools/validate_asset_catalog.py \
  apply-size-normalization \
  catalogs/living_room_kenney_v0/assets.json \
  --plan catalogs/living_room_kenney_v0/size_normalization_v1.json \
  --output catalogs/living_room_kenney_v0/assets.json
