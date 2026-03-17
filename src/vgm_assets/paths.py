from __future__ import annotations

import os
from pathlib import Path

DEFAULT_RAW_DATA_ROOT = "~/scratch/data/vgm/vgm-assets"
DEFAULT_DATA_ROOT = "~/scratch/processed/vgm/vgm-assets"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_root(env_var: str, default_value: str) -> Path:
    override = os.environ.get(env_var)
    value = override if override else default_value
    return Path(value).expanduser().resolve()


def default_raw_data_root() -> Path:
    return _resolve_root("VGM_ASSETS_RAW_DATA_ROOT", DEFAULT_RAW_DATA_ROOT)


def default_data_root() -> Path:
    return _resolve_root("VGM_ASSETS_DATA_ROOT", DEFAULT_DATA_ROOT)


def resolve_under(root: Path, relative_path: str | Path) -> Path:
    return root / Path(relative_path)


def resolve_data_ref(path_str: str | Path, data_root: Path | None = None) -> Path:
    path = Path(path_str).expanduser()
    if path.is_absolute():
        return path.resolve()
    root = data_root or default_data_root()
    return resolve_under(root, path).resolve()
