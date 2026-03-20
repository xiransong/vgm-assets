#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

register_args=()
normalize_args=()

while (($#)); do
  case "$1" in
    --source-repo-root)
      register_args+=("$1" "$2")
      shift 2
      ;;
    --raw-data-root)
      register_args+=("$1" "$2")
      normalize_args+=("$1" "$2")
      shift 2
      ;;
    --data-root)
      normalize_args+=("$1" "$2")
      shift 2
      ;;
    --selection-id)
      register_args+=("$1" "$2")
      normalize_args+=("$1" "$2")
      shift 2
      ;;
    --acquired-by|--acquired-at|--notes)
      register_args+=("$1" "$2")
      shift 2
      ;;
    --created-at)
      normalize_args+=("$1" "$2")
      shift 2
      ;;
    *)
      echo "Unsupported argument for refresh_ai2thor_support_clutter_v0.sh: $1" >&2
      exit 2
      ;;
  esac
done

"${ROOT_DIR}/scripts/sources/register_ai2thor_support_clutter_v0.sh" "${register_args[@]}"
"${ROOT_DIR}/scripts/sources/normalize_ai2thor_support_clutter_v0.sh" "${normalize_args[@]}"
