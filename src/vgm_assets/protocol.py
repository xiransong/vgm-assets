from __future__ import annotations

import json
import os
from pathlib import Path

from jsonschema.validators import validator_for

try:
    from referencing import Registry, Resource
except ImportError:  # pragma: no cover - exercised only in older fallback envs
    Registry = None
    Resource = None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_protocol_root() -> Path:
    override = os.environ.get("VGM_PROTOCOL_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return repo_root().parent / "vgm-protocol"


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_schema(schema_rel_path: str, protocol_root: Path | None = None) -> dict:
    root = (protocol_root or default_protocol_root()).resolve()
    schema_path = root / schema_rel_path
    schema = load_json(schema_path)
    if not isinstance(schema, dict):
        raise TypeError(f"Schema at {schema_path} is not a JSON object")
    return schema


def build_store(protocol_root: Path | None = None) -> dict[str, dict]:
    root = (protocol_root or default_protocol_root()).resolve()
    schema_root = root / "schemas"
    store: dict[str, dict] = {}
    for path in sorted(schema_root.rglob("*.json")):
        contents = load_json(path)
        if not isinstance(contents, dict):
            raise TypeError(f"Schema at {path} is not a JSON object")
        schema_id = contents.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ValueError(f"Schema at {path} is missing a valid $id")
        store[schema_id] = contents
    return store


def build_registry(protocol_root: Path | None = None):
    if Registry is None or Resource is None:
        return None

    registry = Registry()
    for schema_id, contents in build_store(protocol_root).items():
        registry = registry.with_resource(schema_id, Resource.from_contents(contents))
    return registry


def validate_instance(
    instance: object,
    schema_rel_path: str,
    protocol_root: Path | None = None,
) -> None:
    schema = load_schema(schema_rel_path, protocol_root)
    store = build_store(protocol_root)
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    registry = build_registry(protocol_root)
    if registry is not None:
        try:
            validator = validator_cls(schema, registry=registry)
        except TypeError:
            registry = None
        else:
            validator.validate(instance)
            return

    from jsonschema import RefResolver

    resolver = RefResolver.from_schema(schema, store=store)
    validator = validator_cls(schema, resolver=resolver)
    validator.validate(instance)
