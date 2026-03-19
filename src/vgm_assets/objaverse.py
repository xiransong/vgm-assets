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


def _normalize_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _metadata_text(record: dict) -> str:
    text_parts: list[str] = []
    for key in ("title", "description"):
        text = _normalize_text(record.get(key))
        if text:
            text_parts.append(text)
    for key in ("source_tags", "source_categories"):
        values = record.get(key)
        if isinstance(values, list):
            for value in values:
                text = _normalize_text(value)
                if text:
                    text_parts.append(text)
    return " ".join(text_parts)


def _match_category(record: dict, policy: dict) -> tuple[str | None, str]:
    haystack = _metadata_text(record)
    mapping = policy["category_mapping"]
    categories = policy["scope"]["categories"]

    for category in categories:
        category_policy = mapping.get(category, {})
        positives = [
            _normalize_text(keyword)
            for keyword in category_policy.get("positive_keywords", [])
        ]
        negatives = [
            _normalize_text(keyword)
            for keyword in category_policy.get("negative_keywords", [])
        ]
        if any(keyword and keyword in haystack for keyword in negatives):
            continue
        if any(keyword and keyword in haystack for keyword in positives):
            return category, f"keyword_match:{category}"
    return None, "no_match"


def _pick_mesh_format(record: dict, policy: dict) -> tuple[str | None, str]:
    available = record.get("available_formats")
    preferred = [
        _normalize_text(value)
        for value in policy.get("metadata_filters", {}).get("preferred_mesh_formats", [])
    ]
    if not isinstance(available, list) or not available:
        return None, "format_unknown"

    normalized_available = [_normalize_text(value) for value in available]
    for mesh_format in preferred:
        if mesh_format in normalized_available:
            return mesh_format, "preferred_format_present"

    first_available = next((value for value in normalized_available if value), None)
    return first_available, "preferred_format_missing"


def _license_rule(record: dict, policy: dict) -> tuple[bool, str]:
    license_value = _normalize_text(record.get("license"))
    allow = {_normalize_text(value) for value in policy["license_policy"].get("allow", [])}
    manual_review = {
        _normalize_text(value) for value in policy["license_policy"].get("manual_review", [])
    }
    if license_value in allow:
        return True, "allowed_default"
    if license_value in manual_review:
        return False, "manual_review_allowed"
    return False, "rejected_license"


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


def write_objaverse_furniture_review_queue(
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

    candidates: list[dict] = []
    skipped_counts = {
        "rejected_license": 0,
        "manual_review_license": 0,
        "no_category_match": 0,
    }

    for record in harvest.get("records", []):
        if not isinstance(record, dict):
            continue

        allowed_license, license_rule = _license_rule(record, policy)
        if not allowed_license:
            if license_rule == "manual_review_allowed":
                skipped_counts["manual_review_license"] += 1
            else:
                skipped_counts["rejected_license"] += 1
            continue

        category_guess, category_rule = _match_category(record, policy)
        if category_guess is None:
            skipped_counts["no_category_match"] += 1
            continue

        mesh_format, format_rule = _pick_mesh_format(record, policy)
        preview_url = record.get("thumbnail_url")
        has_preview = isinstance(preview_url, str) and bool(preview_url)

        candidate = {
            "candidate_id": f"{category_guess}__{record['object_uid']}",
            "object_uid": record["object_uid"],
            "source_url": record["source_url"],
            "title": record["title"],
            "license": record["license"],
            "category_guess": category_guess,
            "review_status": contract["default_rules"]["default_review_status"],
            "filter_trace": {
                "license_rule": license_rule,
                "category_rule": category_rule,
                "format_rule": format_rule,
                "notes": "Generated by the v0 rule-based narrowing pass.",
            },
        }

        if mesh_format is not None:
            candidate["mesh_format"] = mesh_format
        if "triangle_count" in record:
            candidate["triangle_count"] = record["triangle_count"]
        if "bounds" in record:
            candidate["bounds"] = record["bounds"]
        if "source_tags" in record:
            candidate["source_tags"] = record["source_tags"]
        if "description" in record:
            candidate["review_notes"] = (
                f"Auto-generated candidate from metadata harvest. Description: {record['description']}"
            )
        if has_preview:
            candidate["has_preview"] = True
            candidate["preview_ref"] = {
                "path": preview_url,
                "kind": "remote_url",
            }
        elif preview_url is not None:
            candidate["has_preview"] = False

        validate_objaverse_furniture_review_queue_data(
            {
                "queue_id": "validation_only",
                "source_id": harvest["source_id"],
                "policy_id": policy["policy_id"],
                "created_at": _timestamp(created_at),
                "candidate_count": 1,
                "candidates": [candidate],
            }
        )
        candidates.append(candidate)

    queue = {
        "queue_id": f"{harvest['harvest_id']}_review_queue_v0",
        "source_id": harvest["source_id"],
        "policy_id": policy["policy_id"],
        "created_at": _timestamp(created_at),
        "candidate_count": len(candidates),
        "notes": (
            "Review queue generated by the first v0 rule-based narrowing pass "
            "from a validated metadata-harvest artifact."
        ),
        "candidates": candidates,
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
        "skipped_counts": skipped_counts,
    }
