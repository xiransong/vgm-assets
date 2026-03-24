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


def test_object_semantics_allows_review_scope_and_needs_fix_targets() -> None:
    payload = validate_object_semantics_annotation_set_data(
        {
            "annotation_set_id": "review_scope_example",
            "version": "object_semantics_annotation_set_v0",
            "assets": [
                {
                    "asset_id": "coffee_table_review_01",
                    "asset_role": "parent_object",
                    "category": "coffee_table",
                    "front_axis": "+z",
                    "up_axis": "+y",
                    "bottom_support_plane": {
                        "shape": "rectangle",
                        "width_m": 0.8,
                        "depth_m": 0.6,
                        "local_center_m": {"x": 0.0, "y": 0.0, "z": 0.0},
                        "normal_axis": "+y",
                        "review_status": "reviewed",
                    },
                    "placement_class": "coffee_table",
                    "review_status": "uncertain",
                    "review_scope_v0": [
                        "asset_role",
                        "category",
                        "front_axis",
                        "up_axis",
                        "bottom_support_surface",
                        "support_surfaces_v1",
                        "canonical_bounds",
                    ],
                    "needs_fix_targets_v0": ["front_axis", "canonical_bounds"],
                    "supports_objects": True,
                    "support_surfaces_v1": [
                        {
                            "surface_id": "top",
                            "surface_type": "coffee_table_top",
                            "surface_class": "table_top",
                            "shape": "rectangle",
                            "width_m": 0.75,
                            "depth_m": 0.55,
                            "height_m": 0.42,
                            "local_center_m": {"x": 0.0, "y": 0.42, "z": 0.0},
                            "normal_axis": "+y",
                            "front_axis": "+z",
                            "usable_margin_m": 0.03,
                            "review_status": "reviewed",
                        }
                    ],
                }
            ],
        }
    )
    asset = payload["assets"][0]
    assert asset["review_scope_v0"][0] == "asset_role"
    assert asset["needs_fix_targets_v0"] == ["front_axis", "canonical_bounds"]
