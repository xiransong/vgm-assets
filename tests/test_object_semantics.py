from __future__ import annotations

from pathlib import Path

import pytest

from vgm_assets.object_semantics import (
    validate_object_semantics_annotation_set,
    validate_object_semantics_annotation_set_data,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_parent_object_semantics_example_validates() -> None:
    payload = validate_object_semantics_annotation_set(
        REPO_ROOT / "catalogs" / "object_semantics_v0" / "parent_object_annotations_v0.json"
    )
    assert payload["version"] == "object_semantics_annotation_set_v0"
    assert len(payload["assets"]) == 2
    assert payload["assets"][0]["asset_role"] == "parent_object"


def test_child_object_semantics_example_validates() -> None:
    payload = validate_object_semantics_annotation_set(
        REPO_ROOT / "catalogs" / "object_semantics_v0" / "child_object_annotations_v0.json"
    )
    assert payload["version"] == "object_semantics_annotation_set_v0"
    assert len(payload["assets"]) == 3
    assert payload["assets"][0]["asset_role"] == "child_object"


def test_child_object_semantics_requires_child_placement() -> None:
    with pytest.raises(Exception):
        validate_object_semantics_annotation_set_data(
            {
                "annotation_set_id": "broken_child_example",
                "version": "object_semantics_annotation_set_v0",
                "assets": [
                    {
                        "asset_id": "broken_child_01",
                        "asset_role": "child_object",
                        "category": "mug",
                        "front_axis": "+z",
                        "up_axis": "+y",
                        "bottom_support_plane": {
                            "shape": "circle",
                            "width_m": 0.1,
                            "depth_m": 0.1,
                            "local_center_m": {"x": 0.0, "y": 0.0, "z": 0.0},
                            "normal_axis": "+y"
                        },
                        "placement_class": "mug",
                        "review_status": "auto"
                    }
                ]
            }
        )
