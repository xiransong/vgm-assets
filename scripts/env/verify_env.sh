#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_NAME="${1:-vgm-assets}"

source "${ROOT_DIR}/scripts/lib/micromamba.sh"

"${MAMBA_EXE}" run -n "${ENV_NAME}" python - <<'PY'
from importlib.metadata import version

import jsonschema
import trimesh

print("python stack ok")
print("trimesh", trimesh.__version__)
print("jsonschema", version("jsonschema"))
PY
