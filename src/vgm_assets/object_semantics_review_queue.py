from __future__ import annotations

import json
from pathlib import Path

from .protocol import load_json, validator_class_for_schema

OBJECT_SEMANTICS_REVIEW_QUEUE_SCHEMA = (
    Path("schemas") / "local" / "object_semantics_review_queue_v0.schema.json"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def object_semantics_review_queue_schema_path() -> Path:
    return repo_root() / OBJECT_SEMANTICS_REVIEW_QUEUE_SCHEMA


def load_object_semantics_review_queue(path: Path) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise TypeError(f"Object-semantics review queue at {path} must be a JSON object")
    return payload


def validate_object_semantics_review_queue_data(payload: object) -> dict:
    schema = load_json(object_semantics_review_queue_schema_path())
    validator_cls = validator_class_for_schema(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, dict):
        raise TypeError("Object-semantics review queue payload must be an object after validation")
    return payload


def validate_object_semantics_review_queue(path: Path) -> dict:
    return validate_object_semantics_review_queue_data(load_object_semantics_review_queue(path))


def write_object_semantics_review_queue(payload: dict, output_path: Path) -> dict:
    validated = validate_object_semantics_review_queue_data(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(validated, indent=2) + "\n", encoding="utf-8")
    return validated
