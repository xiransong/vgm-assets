#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHONPATH=src /home/ubuntu/scratch/micromamba/bin/micromamba run -n vgm-assets \
  python tools/validate_asset_catalog.py refresh-ai2thor-object-semantics-review-workspace \
  sources/ai2thor/object_semantics_selection_v0.json \
  "$@"
