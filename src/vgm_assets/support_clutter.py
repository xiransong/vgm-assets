from __future__ import annotations

from pathlib import Path

from jsonschema.validators import validator_for

from .protocol import load_json

SUPPORT_CLUTTER_PROP_ANNOTATION_SET_SCHEMA = (
    Path("schemas") / "local" / "support_clutter_prop_annotation_set_v0.schema.json"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def support_clutter_prop_annotation_set_schema_path() -> Path:
    return repo_root() / SUPPORT_CLUTTER_PROP_ANNOTATION_SET_SCHEMA


def load_support_clutter_prop_annotation_set(path: Path) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise TypeError(f"Support-clutter prop annotation set at {path} must be a JSON object")
    return payload


def validate_support_clutter_prop_annotation_set_data(payload: object) -> dict:
    schema = load_json(support_clutter_prop_annotation_set_schema_path())
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, dict):
        raise TypeError("Support-clutter prop annotation payload must be an object after validation")
    return payload


def validate_support_clutter_prop_annotation_set(path: Path) -> dict:
    return validate_support_clutter_prop_annotation_set_data(
        load_support_clutter_prop_annotation_set(path)
    )
