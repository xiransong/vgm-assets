#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$ROOT_DIR"

/home/ubuntu/scratch/micromamba/bin/micromamba run -n "${1:-vgm-assets}" \
  uvicorn vgm_assets.object_semantics_explorer_app:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
