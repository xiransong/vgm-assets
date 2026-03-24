#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT_DIR="${ROOT_DIR}/exports/object_semantics/ai2thor_reviewed_object_semantics_v0_r1"
REVIEW_ROOT="${HOME}/scratch/processed/vgm/vgm-assets/review/object_semantics/ai2thor/object_semantics_v0"

cd "${ROOT_DIR}"

PYTHONPATH=src /home/ubuntu/scratch/micromamba/bin/micromamba run -n vgm-assets \
  python tools/validate_asset_catalog.py \
  promote-reviewed-object-semantics-slice \
  --reviewed-annotations "${REVIEW_ROOT}/reviewed_annotations_v0.json" \
  --review-queue "${REVIEW_ROOT}/review_queue_v0.json" \
  --output-dir "${OUTPUT_DIR}" \
  --export-id ai2thor_reviewed_object_semantics_v0_r1 \
  "$@"
