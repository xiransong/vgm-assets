from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from .paths import default_raw_data_root, resolve_under
from .protocol import load_json, repo_root, validator_class_for_schema

OBJAVERSE_FURNITURE_METADATA_HARVEST_SCHEMA = (
    Path("schemas") / "local" / "objaverse_furniture_metadata_harvest_v0.schema.json"
)
OBJAVERSE_FURNITURE_REVIEW_QUEUE_SCHEMA = (
    Path("schemas") / "local" / "objaverse_furniture_review_queue_v0.schema.json"
)
OBJAVERSE_FURNITURE_NARROWING_CONTRACT = (
    Path("sources") / "objaverse" / "narrowing_contract_v0.json"
)
OBJAVERSE_SELECTIVE_GEOMETRY_SCHEMA = (
    Path("schemas") / "local" / "objaverse_selective_geometry_v0.schema.json"
)
OBJAVERSE_SELECTIVE_GEOMETRY_MANIFEST_SCHEMA = (
    Path("schemas") / "local" / "objaverse_selective_geometry_manifest_v0.schema.json"
)


def objaverse_furniture_metadata_harvest_schema_path() -> Path:
    return repo_root() / OBJAVERSE_FURNITURE_METADATA_HARVEST_SCHEMA


def objaverse_furniture_review_queue_schema_path() -> Path:
    return repo_root() / OBJAVERSE_FURNITURE_REVIEW_QUEUE_SCHEMA


def objaverse_furniture_narrowing_contract_path() -> Path:
    return repo_root() / OBJAVERSE_FURNITURE_NARROWING_CONTRACT


def objaverse_selective_geometry_schema_path() -> Path:
    return repo_root() / OBJAVERSE_SELECTIVE_GEOMETRY_SCHEMA


def objaverse_selective_geometry_manifest_schema_path() -> Path:
    return repo_root() / OBJAVERSE_SELECTIVE_GEOMETRY_MANIFEST_SCHEMA


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


def _quality_rule(record: dict, policy: dict) -> tuple[bool, str]:
    quality = policy.get("quality_filters", {})
    if not isinstance(quality, dict):
        return True, "quality_ok"

    min_triangle_count = quality.get("min_triangle_count")
    triangle_count = record.get("triangle_count")
    if isinstance(min_triangle_count, int) and isinstance(triangle_count, int):
        if triangle_count < min_triangle_count:
            return False, "rejected_low_triangles"

    haystack = _metadata_text(record)
    negative_keywords = [
        _normalize_text(value) for value in quality.get("negative_keywords", [])
    ]
    for keyword in negative_keywords:
        if keyword and keyword in haystack:
            return False, f"rejected_quality_keyword:{keyword}"

    return True, "quality_ok"


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
    validator_cls = validator_class_for_schema(schema)
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
    validator_cls = validator_class_for_schema(schema)
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


def validate_objaverse_selective_geometry_data(payload: object) -> dict:
    schema = load_json(objaverse_selective_geometry_schema_path())
    validator_cls = validator_class_for_schema(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, dict):
        raise TypeError("Objaverse selective-geometry payload must be a JSON object after validation")
    return payload


def validate_objaverse_selective_geometry(path: Path) -> dict:
    return validate_objaverse_selective_geometry_data(
        _load_object_payload(path, name="Objaverse selective geometry")
    )


def validate_objaverse_selective_geometry_manifest_data(payload: object) -> dict:
    schema = load_json(objaverse_selective_geometry_manifest_schema_path())
    validator_cls = validator_class_for_schema(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    validator.validate(payload)
    if not isinstance(payload, dict):
        raise TypeError(
            "Objaverse selective-geometry manifest payload must be a JSON object after validation"
        )
    return payload


def validate_objaverse_selective_geometry_manifest(path: Path) -> dict:
    return validate_objaverse_selective_geometry_manifest_data(
        _load_object_payload(path, name="Objaverse selective geometry manifest")
    )


def load_objaverse_furniture_narrowing_contract(path: Path | None = None) -> dict:
    contract_path = path or objaverse_furniture_narrowing_contract_path()
    return _load_object_payload(contract_path, name="Objaverse narrowing contract")


def write_objaverse_selective_geometry_manifest(
    *,
    selection_path: Path,
    harvest_path: Path,
    output_path: Path,
    created_at: str | None = None,
) -> dict:
    selection = validate_objaverse_selective_geometry(selection_path)
    harvest = validate_objaverse_furniture_metadata_harvest(harvest_path)

    records_by_uid = {}
    for record in harvest.get("records", []):
        if isinstance(record, dict):
            object_uid = record.get("object_uid")
            if isinstance(object_uid, str) and object_uid:
                records_by_uid[object_uid] = record

    manifest_candidates: list[dict] = []
    for selected in selection.get("selected_candidates", []):
        object_uid = selected["object_uid"]
        record = records_by_uid.get(object_uid)
        if record is None:
            raise ValueError(
                f"Selected Objaverse candidate '{object_uid}' was not found in harvest {harvest_path}"
            )

        preferred_order = selected.get("expected_formats", [])
        if not isinstance(preferred_order, list) or not preferred_order:
            raise ValueError(
                f"Selected Objaverse candidate '{object_uid}' must define non-empty expected_formats"
            )
        available_formats = record.get("available_formats", [])
        if not isinstance(available_formats, list):
            available_formats = []

        candidate = {
            "object_uid": object_uid,
            "title": record["title"],
            "category_guess": selected["category_guess"],
            "priority": selected["priority"],
            "source_url": record["source_url"],
            "license": record["license"],
            "available_formats": available_formats,
            "preferred_download_order": preferred_order,
            "raw_candidate_rel_dir": (
                Path("sources")
                / "objaverse"
                / "furniture_v0"
                / "geometry"
                / object_uid
                / "raw"
            ).as_posix(),
            "notes": selected.get("notes", ""),
        }
        thumbnail_url = record.get("thumbnail_url")
        if isinstance(thumbnail_url, str) and thumbnail_url:
            candidate["thumbnail_url"] = thumbnail_url
        triangle_count = record.get("triangle_count")
        if isinstance(triangle_count, int):
            candidate["triangle_count"] = triangle_count
        vertex_count = record.get("vertex_count")
        if isinstance(vertex_count, int):
            candidate["vertex_count"] = vertex_count

        validate_objaverse_selective_geometry_manifest_data(
            {
                "manifest_id": "validation_only",
                "selection_id": selection["selection_id"],
                "source_id": selection["source_id"],
                "review_id": selection["review_id"],
                "harvest_artifact": selection["harvest_artifact"],
                "queue_artifact": selection["queue_artifact"],
                "created_at": _timestamp(created_at),
                "raw_data_root_env_var": "VGM_ASSETS_RAW_DATA_ROOT",
                "raw_acquisition_root_rel": "sources/objaverse/furniture_v0/geometry",
                "candidate_count": 1,
                "candidates": [candidate],
            }
        )
        manifest_candidates.append(candidate)

    manifest = {
        "manifest_id": f"{selection['selection_id']}_manifest",
        "selection_id": selection["selection_id"],
        "source_id": selection["source_id"],
        "review_id": selection["review_id"],
        "harvest_artifact": selection["harvest_artifact"],
        "queue_artifact": selection["queue_artifact"],
        "created_at": _timestamp(created_at),
        "raw_data_root_env_var": "VGM_ASSETS_RAW_DATA_ROOT",
        "raw_acquisition_root_rel": "sources/objaverse/furniture_v0/geometry",
        "candidate_count": len(manifest_candidates),
        "candidates": manifest_candidates,
    }
    validate_objaverse_selective_geometry_manifest_data(manifest)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return {
        "selection_id": selection["selection_id"],
        "harvest_path": str(harvest_path.resolve()),
        "output_path": str(output_path.resolve()),
        "candidate_count": manifest["candidate_count"],
    }


def _load_asset_catalog_records(path: Path) -> list[dict]:
    payload = load_json(path)
    if not isinstance(payload, list):
        raise TypeError(f"Asset catalog at {path} must be a JSON array")
    records: list[dict] = []
    for entry in payload:
        if isinstance(entry, dict):
            records.append(entry)
    return records


def _reference_dimensions_by_category(catalog_path: Path) -> dict[str, list[float]]:
    grouped: dict[str, list[list[float]]] = {}
    for record in _load_asset_catalog_records(catalog_path):
        category = record.get("category")
        dimensions = record.get("dimensions")
        if not isinstance(category, str) or not isinstance(dimensions, dict):
            continue
        try:
            values = [
                float(dimensions["width"]),
                float(dimensions["depth"]),
                float(dimensions["height"]),
            ]
        except (KeyError, TypeError, ValueError):
            continue
        grouped.setdefault(category, []).append(sorted(values, reverse=True))

    references: dict[str, list[float]] = {}
    for category, dimension_sets in grouped.items():
        if not dimension_sets:
            continue
        count = len(dimension_sets)
        references[category] = [
            sum(values[index] for values in dimension_sets) / count for index in range(3)
        ]
    return references


def _nearest_common_scale(scale: float) -> tuple[float, str]:
    candidates = [
        (0.001, "millimeter_to_meter"),
        (0.01, "centimeter_to_meter"),
        (0.0254, "inch_to_meter"),
        (0.1, "decimeter_to_meter"),
        (1.0, "meter_to_meter"),
    ]
    best_scale, best_label = candidates[0]
    best_error = abs(math.log(scale) - math.log(best_scale))
    for candidate_scale, label in candidates[1:]:
        error = abs(math.log(scale) - math.log(candidate_scale))
        if error < best_error:
            best_scale = candidate_scale
            best_label = label
            best_error = error
    return best_scale, best_label


def write_objaverse_selective_geometry_inspection(
    *,
    manifest_path: Path,
    reference_catalog_path: Path,
    raw_data_root: Path | None = None,
    output_path: Path,
    created_at: str | None = None,
) -> dict:
    manifest = validate_objaverse_selective_geometry_manifest(manifest_path)
    references = _reference_dimensions_by_category(reference_catalog_path)
    raw_root = raw_data_root or default_raw_data_root()

    import trimesh  # type: ignore

    candidates: list[dict] = []
    for candidate in manifest.get("candidates", []):
        category = candidate["category_guess"]
        reference_sorted_dims = references.get(category)
        if reference_sorted_dims is None:
            raise ValueError(
                f"No reference dimensions available for category '{category}' in {reference_catalog_path}"
            )

        raw_mesh_path = resolve_under(raw_root, Path(candidate["raw_candidate_rel_dir"]) / "model.glb")
        if not raw_mesh_path.exists():
            alt_paths = list(resolve_under(raw_root, candidate["raw_candidate_rel_dir"]).glob("model.*"))
            if not alt_paths:
                raise FileNotFoundError(f"Missing downloaded raw mesh for {candidate['object_uid']}")
            raw_mesh_path = alt_paths[0]

        scene = trimesh.load(raw_mesh_path, force="scene")
        bounds = scene.bounds
        if bounds is None:
            raise ValueError(f"Could not compute bounds for raw mesh {raw_mesh_path}")
        raw_extents = (bounds[1] - bounds[0]).tolist()
        raw_sorted = sorted((float(value) for value in raw_extents), reverse=True)

        ratios = []
        for raw_value, ref_value in zip(raw_sorted, reference_sorted_dims):
            if raw_value <= 0:
                raise ValueError(f"Non-positive raw extent for {candidate['object_uid']}: {raw_sorted}")
            ratios.append(ref_value / raw_value)
        suggested_scale = math.exp(sum(math.log(value) for value in ratios) / len(ratios))
        scaled_sorted = [value * suggested_scale for value in raw_sorted]
        fit_log_rmse = math.sqrt(
            sum((math.log(scaled) - math.log(ref)) ** 2 for scaled, ref in zip(scaled_sorted, reference_sorted_dims))
            / len(reference_sorted_dims)
        )
        nearest_scale, nearest_label = _nearest_common_scale(suggested_scale)

        candidates.append(
            {
                "object_uid": candidate["object_uid"],
                "title": candidate["title"],
                "category_guess": category,
                "raw_mesh_relpath": (
                    Path(candidate["raw_candidate_rel_dir"]) / raw_mesh_path.name
                ).as_posix(),
                "geometry_count": len(scene.geometry),
                "raw_extents_xyz": raw_extents,
                "raw_extents_sorted_desc": raw_sorted,
                "reference_extents_sorted_desc": reference_sorted_dims,
                "suggested_uniform_scale": suggested_scale,
                "scaled_extents_sorted_desc": scaled_sorted,
                "nearest_common_scale": nearest_scale,
                "nearest_common_scale_label": nearest_label,
                "fit_log_rmse": fit_log_rmse,
            }
        )

    report = {
        "report_id": f"{manifest['selection_id']}_inspection_v0",
        "selection_id": manifest["selection_id"],
        "reference_catalog_path": str(reference_catalog_path),
        "created_at": _timestamp(created_at),
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {
        "selection_id": manifest["selection_id"],
        "reference_catalog_path": str(reference_catalog_path.resolve()),
        "output_path": str(output_path.resolve()),
        "candidate_count": len(candidates),
    }


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
        "rejected_quality": 0,
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

        allowed_quality, quality_rule = _quality_rule(record, policy)
        if not allowed_quality:
            skipped_counts["rejected_quality"] += 1
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
                "notes": f"Generated by the v0 rule-based narrowing pass. {quality_rule}.",
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


def review_queue_output_path_for_harvest(
    *,
    spec: dict,
    harvest_path: Path,
    data_root: Path,
) -> Path:
    processed_layout = spec.get("processed_layout")
    if not isinstance(processed_layout, dict):
        raise TypeError("Objaverse metadata source spec must define processed_layout")
    review_queue_root_rel = processed_layout.get("review_queue_root_rel")
    if not isinstance(review_queue_root_rel, str) or not review_queue_root_rel:
        raise ValueError("Objaverse metadata source spec processed_layout is missing review_queue_root_rel")

    harvest_stem = harvest_path.stem
    suffix = "_harvest"
    if harvest_stem.endswith(suffix):
        base_name = harvest_stem[: -len(suffix)]
    else:
        base_name = harvest_stem
    return data_root / Path(review_queue_root_rel) / f"{base_name}_review_queue.json"
