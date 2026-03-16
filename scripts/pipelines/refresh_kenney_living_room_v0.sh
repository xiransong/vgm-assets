#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RAW_FILE="${1:-}"

cd "${ROOT_DIR}"

if [[ -n "${RAW_FILE}" ]]; then
  ./scripts/sources/rebuild_kenney_living_room_v0.sh "${RAW_FILE}"
else
  ./scripts/sources/rebuild_kenney_living_room_v0.sh
fi

./scripts/catalogs/refresh_living_room_kenney_v0.sh
