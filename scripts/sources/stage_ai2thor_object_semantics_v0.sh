#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHONPATH=src python3 tools/validate_asset_catalog.py register-ai2thor-object-semantics-selection \
  sources/ai2thor/object_semantics_selection_v0.json \
  "$@"
