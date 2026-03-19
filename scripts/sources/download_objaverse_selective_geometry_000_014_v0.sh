#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_NAME="${VGM_ASSETS_ENV_NAME:-vgm-assets}"
DOWNLOAD_PROCESSES="${VGM_ASSETS_OBJAVERSE_DOWNLOAD_PROCESSES:-2}"
SELECTION_MANIFEST="${ROOT_DIR}/sources/objaverse/selective_geometry_manifest_objaverse_000_014_v0.json"

source "${ROOT_DIR}/scripts/lib/micromamba.sh"

"${MAMBA_EXE}" run -n "${ENV_NAME}" python \
  "${ROOT_DIR}/tools/validate_asset_catalog.py" \
  download-objaverse-selective-geometry \
  --manifest "${SELECTION_MANIFEST}" \
  --download-processes "${DOWNLOAD_PROCESSES}" \
  "${@}"
