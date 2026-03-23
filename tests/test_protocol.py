from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from vgm_assets.protocol import (
    load_json,
    validate_instance,
    validator_class_for_schema,
)


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


def test_validator_class_for_draft202012_schema_avoids_deprecation_warning() -> None:
    schema = load_json(REPO_ROOT / "schemas" / "local" / "wall_fixture_catalog_v0.schema.json")
    assert isinstance(schema, dict)

    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        validator_cls = validator_class_for_schema(schema)
        validator_cls.check_schema(schema)

    assert validator_cls.__name__ == "Draft202012Validator"
    deprecations = [warning for warning in recorded if issubclass(warning.category, DeprecationWarning)]
    assert deprecations == []
