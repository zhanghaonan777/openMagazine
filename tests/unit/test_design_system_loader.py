"""Tests for design_system_loader."""
from pathlib import Path

import pytest
import yaml

from lib.design_system_loader import (
    load_profile,
    load_design_system,
    resolve_design_system,
    ProfileNotFoundError,
    DesignSystemNotFoundError,
)


SKILL_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def fake_profile_dir(tmp_path, monkeypatch):
    """Create a temporary library/profiles/ dir with one yaml."""
    profiles_dir = tmp_path / "library" / "profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "consumer-retail.yaml").write_text(yaml.safe_dump({
        "schema_version": 1,
        "name": "consumer-retail",
        "display_name": {"en": "Consumer Retail"},
        "presentations_profile": "consumer-retail",
        "hard_gates": [
            {"rule": "brand_authenticity_gate",
             "description": "no logo generation",
             "forbidden_generations": ["logo", "mascot"]}
        ],
        "required_proof_objects": ["image_hero_or_look_page"],
    }))
    monkeypatch.setattr("lib.design_system_loader.SKILL_ROOT", tmp_path)
    return profiles_dir


def test_load_profile_returns_dict(fake_profile_dir):
    profile = load_profile("consumer-retail")
    assert profile["name"] == "consumer-retail"
    assert profile["presentations_profile"] == "consumer-retail"
    assert len(profile["hard_gates"]) == 1


def test_load_profile_missing_raises(monkeypatch, tmp_path):
    monkeypatch.setattr("lib.design_system_loader.SKILL_ROOT", tmp_path)
    with pytest.raises(ProfileNotFoundError):
        load_profile("nonexistent-profile")


def test_load_design_system_returns_dict(tmp_path, monkeypatch):
    ds_dir = tmp_path / "library" / "design-systems"
    ds_dir.mkdir(parents=True)
    (ds_dir / "test-slug.yaml").write_text(yaml.safe_dump({
        "schema_version": 1,
        "slug": "test-slug",
        "profile": "consumer-retail",
        "brand": "meow-life",
        "typography_resolution": {},
        "brand_authenticity": {},
        "output_targets": [{"format": "a4-magazine", "realizer": "weasyprint"}],
    }))
    monkeypatch.setattr("lib.design_system_loader.SKILL_ROOT", tmp_path)
    ds = load_design_system("test-slug")
    assert ds["slug"] == "test-slug"
    assert ds["profile"] == "consumer-retail"


def test_load_design_system_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setattr("lib.design_system_loader.SKILL_ROOT", tmp_path)
    with pytest.raises(DesignSystemNotFoundError):
        load_design_system("nonexistent-slug")


def test_resolve_design_system_inherits_from_brand(fake_profile_dir, tmp_path, monkeypatch):
    """resolve_design_system composes from spec + brand + profile."""
    spec = {"slug": "test-slug"}
    layers = {
        "brand": {
            "schema_version": 2,
            "name": "meow-life",
            "typography": {
                "display": {"family": "Playfair Display"},
                "body": {"family": "Source Serif 4"},
            },
        },
    }
    monkeypatch.setattr("lib.design_system_loader.SKILL_ROOT", tmp_path)
    # Need both profile and brand setup; reuse fake_profile_dir
    ds = resolve_design_system(spec, layers, profile_name="consumer-retail")
    assert ds["slug"] == "test-slug"
    assert ds["profile"] == "consumer-retail"
    assert "display" in ds["typography_resolution"]
    assert ds["typography_resolution"]["display"]["desired_family"] == "Playfair Display"
    # Fallback chain auto-built with at least a system-safe option
    assert len(ds["typography_resolution"]["display"]["fallback_chain"]) >= 1
