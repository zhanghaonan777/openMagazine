"""Tests for regions_validate."""
from pathlib import Path

import pytest
import yaml

from tools.validation.regions_validate import validate_regions


def _write_yaml(tmp_path, data):
    p = tmp_path / "x.regions.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


def test_valid_regions_yaml_returns_empty_errors(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "hero", "rect_norm": [0.0, 0.0, 0.5, 1.0],
             "role": "image", "image_slot": "feature_hero", "aspect": "3:4"},
        ],
    })
    assert validate_regions(p) == []


def test_rect_norm_out_of_range_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "bad", "rect_norm": [0.0, 0.0, 1.5, 1.0],  # x2 > 1
             "role": "negative_space"},
        ],
    })
    errors = validate_regions(p)
    assert any("rect_norm" in e for e in errors)


def test_text_region_missing_text_field_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "title", "rect_norm": [0.55, 0.1, 0.95, 0.3],
             "role": "text", "component": "Title"},  # missing text_field
        ],
    })
    errors = validate_regions(p)
    assert any("text_field" in e for e in errors)


def test_unknown_component_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "title", "rect_norm": [0.55, 0.1, 0.95, 0.3],
             "role": "text", "component": "InventedComponent",
             "text_field": "title"},
        ],
    })
    errors = validate_regions(p)
    assert any("InventedComponent" in e for e in errors)


def test_overlapping_regions_above_threshold_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "a", "rect_norm": [0.0, 0.0, 0.5, 0.5], "role": "negative_space"},
            {"id": "b", "rect_norm": [0.1, 0.1, 0.6, 0.6], "role": "negative_space"},
        ],
    })
    errors = validate_regions(p)
    assert any("overlap" in e for e in errors)


def test_duplicate_region_id_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "x", "rect_norm": [0.0, 0.0, 0.4, 0.4], "role": "negative_space"},
            {"id": "x", "rect_norm": [0.5, 0.5, 0.9, 0.9], "role": "negative_space"},
        ],
    })
    errors = validate_regions(p)
    assert any("duplicate" in e.lower() for e in errors)
