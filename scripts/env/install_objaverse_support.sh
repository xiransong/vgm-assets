#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_NAME="${1:-vgm-assets}"

source "${ROOT_DIR}/scripts/lib/micromamba.sh"

echo "Installing Objaverse download support into '${ENV_NAME}'"
"${MAMBA_EXE}" run -n "${ENV_NAME}" python -m pip install objaverse

echo "Verifying Objaverse install"
"${MAMBA_EXE}" run -n "${ENV_NAME}" python - <<'PY'
from importlib.metadata import version
import objaverse

print("objaverse ok")
print("objaverse", version("objaverse"))
print("module", objaverse.__file__)
PY
