from __future__ import annotations

from pathlib import Path

from jsonschema.validators import validator_for

from .protocol import load_json, repo_root

OBJAVERSE_FURNITURE_METADATA_HARVEST_SCHEMA = (
    Path("schemas") / "local" / "objaverse_furniture_metadata_harvest_v0.schema.json"
)
OBJAVERSE_FURNITURE_REVIEW_QUEUE_SCHEMA = (
    Path("schemas") / "local" / "objaverse_furniture_review_queue_v0.schema.json"
)


def objaverse_furniture_metadata_harvest_schema_path() -> Path:
    return repo_root() / OBJAVERSE_FURNITURE_METADATA_HARVEST_SCHEMA


def objaverse_furniture_review_queue_schema_path() -> Path:
    return repo_root() / OBJAVERSE_FURNITURE_REVIEW_QUEUE_SCHEMA


def _load_object_payload(path: Path, *, name: str) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise TypeError(f"{name} at {path} must be a JSON object")
    return payload


def validate_objaverse_furniture_metadata_harvest_data(payload: object) -> dict:
    schema = load_json(objaverse_furniture_metadata_harvest_schema_path())
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, dict):
        raise TypeError("Objaverse metadata-harvest payload must be a JSON object after validation")
    return payload


def validate_objaverse_furniture_metadata_harvest(path: Path) -> dict:
    return validate_objaverse_furniture_metadata_harvest_data(
        _load_object_payload(path, name="Objaverse metadata harvest")
    )


def validate_objaverse_furniture_review_queue_data(payload: object) -> dict:
    schema = load_json(objaverse_furniture_review_queue_schema_path())
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, dict):
        raise TypeError("Objaverse review-queue payload must be a JSON object after validation")
    return payload


def validate_objaverse_furniture_review_queue(path: Path) -> dict:
    return validate_objaverse_furniture_review_queue_data(
        _load_object_payload(path, name="Objaverse review queue")
    )
