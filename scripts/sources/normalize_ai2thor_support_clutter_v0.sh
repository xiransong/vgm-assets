#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

PYTHONPATH="${ROOT_DIR}/src" python3 "${ROOT_DIR}/tools/validate_asset_catalog.py" \
  normalize-ai2thor-support-clutter-selection \
  "${ROOT_DIR}/sources/ai2thor/support_clutter_selection_v0.json" \
  "$@"
