#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_NAME="${VGM_ASSETS_ENV_NAME:-vgm-assets}"
PLAN_PATH="${ROOT_DIR}/sources/objaverse/normalization_plan_objaverse_000_014_v0.json"

source "${ROOT_DIR}/scripts/lib/micromamba.sh"

"${MAMBA_EXE}" run -n "${ENV_NAME}" python \
  "${ROOT_DIR}/tools/validate_asset_catalog.py" \
  normalize-objaverse-furniture-selection \
  --plan "${PLAN_PATH}" \
  "${@}"
