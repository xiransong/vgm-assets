from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema.validators import validator_for

from .protocol import load_json, repo_root

OBJAVERSE_FURNITURE_METADATA_HARVEST_SCHEMA = (
    Path("schemas") / "local" / "objaverse_furniture_metadata_harvest_v0.schema.json"
)
OBJAVERSE_FURNITURE_REVIEW_QUEUE_SCHEMA = (
    Path("schemas") / "local" / "objaverse_furniture_review_queue_v0.schema.json"
)
OBJAVERSE_FURNITURE_NARROWING_CONTRACT = (
    Path("sources") / "objaverse" / "narrowing_contract_v0.json"
)


def objaverse_furniture_metadata_harvest_schema_path() -> Path:
    return repo_root() / OBJAVERSE_FURNITURE_METADATA_HARVEST_SCHEMA


def objaverse_furniture_review_queue_schema_path() -> Path:
    return repo_root() / OBJAVERSE_FURNITURE_REVIEW_QUEUE_SCHEMA


def objaverse_furniture_narrowing_contract_path() -> Path:
    return repo_root() / OBJAVERSE_FURNITURE_NARROWING_CONTRACT


def _load_object_payload(path: Path, *, name: str) -> dict:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise TypeError(f"{name} at {path} must be a JSON object")
    return payload


def _timestamp(value: str | None = None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def load_objaverse_furniture_narrowing_contract(path: Path | None = None) -> dict:
    contract_path = path or objaverse_furniture_narrowing_contract_path()
    return _load_object_payload(contract_path, name="Objaverse narrowing contract")


def write_stub_objaverse_furniture_review_queue(
    *,
    harvest_path: Path,
    policy_path: Path,
    output_path: Path,
    contract_path: Path | None = None,
    created_at: str | None = None,
) -> dict:
    harvest = validate_objaverse_furniture_metadata_harvest(harvest_path)
    policy = _load_object_payload(policy_path, name="Objaverse ingestion policy")
    contract = load_objaverse_furniture_narrowing_contract(contract_path)

    queue = {
        "queue_id": f"{harvest['harvest_id']}_stub_review_queue_v0",
        "source_id": harvest["source_id"],
        "policy_id": policy["policy_id"],
        "created_at": _timestamp(created_at),
        "candidate_count": 0,
        "notes": (
            "Stub review queue generated from a validated metadata-harvest artifact. "
            "Real narrowing logic is not implemented yet; no candidates have been emitted."
        ),
        "candidates": [],
    }
    validate_objaverse_furniture_review_queue_data(queue)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")

    return {
        "harvest_path": str(harvest_path.resolve()),
        "policy_id": policy["policy_id"],
        "contract_id": contract["contract_id"],
        "output_path": str(output_path.resolve()),
        "record_count": harvest["record_count"],
        "candidate_count": queue["candidate_count"],
    }
