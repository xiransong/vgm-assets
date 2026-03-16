#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RAW_FILE="${1:-}"

ARGS=(
  tools/validate_asset_catalog.py
  rebuild-kenney-selection
  sources/kenney/selection_v0.json
  --source-spec
  sources/kenney/source_spec_v0.json
)

if [[ -n "${RAW_FILE}" ]]; then
  ARGS+=(--raw-file "${RAW_FILE}")
fi

cd "${ROOT_DIR}"
PYTHONPATH=src python3 "${ARGS[@]}"
