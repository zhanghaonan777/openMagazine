"""Tests for design_system_validate."""
import pytest
import yaml

from tools.validation.design_system_validate import validate_design_system


def _write_yaml(tmp_path, data):
    p = tmp_path / "test.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


def test_valid_design_system_returns_empty(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "slug": "test",
        "profile": "consumer-retail",
        "brand": "meow-life",
        "typography_resolution": {
            "display": {
                "desired_family": "Playfair Display",
                "fallback_chain": ["Georgia"],
            },
        },
        "brand_authenticity": {"do_not_generate": ["logo"]},
        "output_targets": [{"format": "a4-magazine", "realizer": "weasyprint"}],
    })
    assert validate_design_system(p) == []


def test_missing_required_top_level_field_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "slug": "test",
        # missing profile, brand, etc.
    })
    errors = validate_design_system(p)
    assert any("profile" in e or "brand" in e or "required" in e for e in errors)


def test_empty_fallback_chain_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "slug": "test",
        "profile": "consumer-retail",
        "brand": "meow-life",
        "typography_resolution": {
            "display": {"desired_family": "X", "fallback_chain": []},
        },
        "brand_authenticity": {},
        "output_targets": [{"format": "a4-magazine", "realizer": "weasyprint"}],
    })
    errors = validate_design_system(p)
    assert any("fallback_chain" in e for e in errors)


def test_unknown_realizer_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "slug": "test",
        "profile": "consumer-retail",
        "brand": "meow-life",
        "typography_resolution": {},
        "brand_authenticity": {},
        "output_targets": [{"format": "deck-pptx", "realizer": "InventedRealizer"}],
    })
    errors = validate_design_system(p)
    assert any("realizer" in e or "InventedRealizer" in e for e in errors)


def test_magazine_pptx_requires_portrait_two_to_three(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "slug": "test",
        "profile": "consumer-retail",
        "brand": "meow-life",
        "typography_resolution": {},
        "brand_authenticity": {},
        "output_targets": [{
            "format": "magazine-pptx",
            "realizer": "presentations",
            "slide_size": "1280x720",
            "page_count": 16,
        }],
    })
    errors = validate_design_system(p)
    assert any("portrait" in e or "2:3" in e for e in errors)


def test_magazine_pptx_portrait_target_validates(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "slug": "test",
        "profile": "consumer-retail",
        "brand": "meow-life",
        "typography_resolution": {},
        "brand_authenticity": {},
        "output_targets": [{
            "format": "magazine-pptx",
            "realizer": "presentations",
            "slide_size": "720x1080",
            "page_count": 16,
        }],
    })
    assert validate_design_system(p) == []


def test_validates_shipped_example():
    """The cosmos-luna-may-2026.yaml shipped in the repo must validate."""
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    example = repo_root / "library/design-systems/cosmos-luna-may-2026.yaml"
    if example.is_file():
        assert validate_design_system(example) == []
