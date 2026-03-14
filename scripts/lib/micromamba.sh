#!/usr/bin/env bash

DEFAULT_MAMBA_ROOT="${HOME}/scratch/micromamba"
DEFAULT_CACHE_ROOT="${HOME}/scratch/.cache"
DEFAULT_TMP_ROOT="${HOME}/scratch/tmp"
FALLBACK_CACHE_ROOT="/tmp/vgm-assets-cache"
FALLBACK_TMP_ROOT="/tmp/vgm-assets-tmp"

_vgm_assets_dir_writable() {
  local dir="$1"
  local probe
  if ! mkdir -p "${dir}" >/dev/null 2>&1; then
    return 1
  fi
  probe="${dir}/.vgm_assets_write_probe_$$"
  if ! ( : > "${probe}" ) >/dev/null 2>&1; then
    return 1
  fi
  rm -f "${probe}" >/dev/null 2>&1 || true
  return 0
}

if [ -z "${MAMBA_ROOT_PREFIX:-}" ]; then
  export MAMBA_ROOT_PREFIX="${DEFAULT_MAMBA_ROOT}"
fi

if [ -z "${XDG_CACHE_HOME:-}" ]; then
  export XDG_CACHE_HOME="${DEFAULT_CACHE_ROOT}"
fi

if [ -z "${TMPDIR:-}" ]; then
  export TMPDIR="${DEFAULT_TMP_ROOT}"
fi

if [ -z "${PIP_CACHE_DIR:-}" ]; then
  export PIP_CACHE_DIR="${XDG_CACHE_HOME}/pip"
fi

if ! _vgm_assets_dir_writable "${XDG_CACHE_HOME}" || ! _vgm_assets_dir_writable "${TMPDIR}" || ! _vgm_assets_dir_writable "${PIP_CACHE_DIR}"; then
  export XDG_CACHE_HOME="${FALLBACK_CACHE_ROOT}"
  export TMPDIR="${FALLBACK_TMP_ROOT}"
  export PIP_CACHE_DIR="${XDG_CACHE_HOME}/pip"
  mkdir -p "${XDG_CACHE_HOME}" "${TMPDIR}" "${PIP_CACHE_DIR}"
fi

if [ -n "${MAMBA_EXE:-}" ] && [ -x "${MAMBA_EXE}" ]; then
  _VGM_ASSETS_MICROMAMBA="${MAMBA_EXE}"
elif [ -x "${MAMBA_ROOT_PREFIX}/bin/micromamba" ]; then
  _VGM_ASSETS_MICROMAMBA="${MAMBA_ROOT_PREFIX}/bin/micromamba"
elif command -v micromamba >/dev/null 2>&1; then
  _VGM_ASSETS_MICROMAMBA="$(command -v micromamba)"
else
  echo "micromamba was not found."
  echo "Expected at ${MAMBA_ROOT_PREFIX}/bin/micromamba or on PATH."
  echo "You can also set MAMBA_EXE to an explicit binary path."
  return 1
fi

export MAMBA_EXE="${_VGM_ASSETS_MICROMAMBA}"
