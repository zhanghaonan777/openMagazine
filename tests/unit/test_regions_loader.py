"""Tests for regions_loader."""
from pathlib import Path

import pytest
import yaml

from lib.regions_loader import (
    load_regions,
    regions_for_image_prompt,
    RegionsNotFoundError,
)


SKILL_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sample_yaml(tmp_path, monkeypatch):
    """Write a minimal regions yaml under a temporary library/layouts/_components/.

    Patches SKILL_ROOT so load_regions finds it.
    """
    components_dir = tmp_path / "library" / "layouts" / "_components"
    components_dir.mkdir(parents=True)
    yaml_path = components_dir / "feature-spread.regions.yaml"
    yaml_path.write_text(yaml.safe_dump({
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "hero_image", "rect_norm": [0.0, 0.0, 0.5, 1.0],
             "role": "image", "image_slot": "feature_hero", "aspect": "3:4"},
            {"id": "title", "rect_norm": [0.55, 0.15, 0.95, 0.30],
             "role": "text", "component": "Title", "text_field": "title"},
            {"id": "body", "rect_norm": [0.55, 0.45, 0.95, 0.85],
             "role": "text", "component": "BodyWithDropCap", "text_field": "body"},
        ],
    }))
    monkeypatch.setattr("lib.regions_loader.SKILL_ROOT", tmp_path)
    return yaml_path


def test_load_regions_returns_dict(sample_yaml):
    regions = load_regions("feature-spread")
    assert regions["spread_type"] == "feature-spread"
    assert regions["schema_version"] == 1
    assert len(regions["regions"]) == 3


def test_load_regions_missing_raises(monkeypatch, tmp_path):
    monkeypatch.setattr("lib.regions_loader.SKILL_ROOT", tmp_path)
    with pytest.raises(RegionsNotFoundError):
        load_regions("does-not-exist")


def test_regions_for_image_prompt_own_and_siblings(sample_yaml):
    ctx = regions_for_image_prompt("feature-spread", "feature_hero")
    assert ctx["own_region"]["id"] == "hero_image"
    assert ctx["own_region"]["image_slot"] == "feature_hero"
    sibling_ids = {r["id"] for r in ctx["sibling_regions"]}
    assert sibling_ids == {"title", "body"}


def test_regions_for_image_prompt_unknown_slot_raises(sample_yaml):
    with pytest.raises(ValueError, match="image_slot"):
        regions_for_image_prompt("feature-spread", "nonexistent_slot")
