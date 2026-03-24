#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_NAME="${1:-vgm-assets}"
ENV_FILE="${ROOT_DIR}/env/environment.yml"

source "${ROOT_DIR}/scripts/lib/micromamba.sh"

if ! "${MAMBA_EXE}" run -n "${ENV_NAME}" python -V >/dev/null 2>&1; then
  echo "Environment '${ENV_NAME}' does not exist yet."
  echo "Create it first with: ./scripts/env/create_env.sh ${ENV_NAME}"
  exit 1
fi

echo "Updating '${ENV_NAME}' from ${ENV_FILE}"
"${MAMBA_EXE}" env update -n "${ENV_NAME}" -f "${ENV_FILE}" --prune
"${MAMBA_EXE}" run -n "${ENV_NAME}" python -m pip install --no-build-isolation -e "${ROOT_DIR}"

echo "Environment updated: ${ENV_NAME}"
