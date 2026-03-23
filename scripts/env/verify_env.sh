#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_NAME="${1:-vgm-assets}"

source "${ROOT_DIR}/scripts/lib/micromamba.sh"

"${MAMBA_EXE}" run -n "${ENV_NAME}" python - <<'PY'
from importlib.metadata import version

import jsonschema
import trimesh

jsonschema_version = version("jsonschema")
major, minor, *_ = [int(part) for part in jsonschema_version.split(".")]
if (major, minor) < (4, 23):
    raise SystemExit(
        f"jsonschema>={{4.23}} is required for Draft 2020-12 validation; found {jsonschema_version}"
    )

print("python stack ok")
print("trimesh", trimesh.__version__)
print("jsonschema", jsonschema_version)
PY
