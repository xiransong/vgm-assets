from __future__ import annotations

import json
from pathlib import Path

import pytest

from vgm_assets.protocol import validate_instance


REPO_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_ROOT = REPO_ROOT.parent / "vgm-protocol"


def test_validate_instance_accepts_valid_asset_spec() -> None:
    record = json.loads(
        (
            REPO_ROOT / "catalogs" / "living_room_kenney_v0" / "assets.json"
        ).read_text(encoding="utf-8")
    )[0]

    validate_instance(
        record,
        "schemas/core/asset_spec.schema.json",
        PROTOCOL_ROOT,
    )


def test_validate_instance_rejects_invalid_asset_spec() -> None:
    with pytest.raises(Exception):
        validate_instance(
            {},
            "schemas/core/asset_spec.schema.json",
            PROTOCOL_ROOT,
        )
