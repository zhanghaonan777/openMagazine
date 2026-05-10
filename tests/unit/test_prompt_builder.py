"""Tests for prompt_builder + placeholder_resolver layout/theme placeholders."""
import pytest

from lib.placeholder_resolver import build_placeholder_map
from lib.prompt_builder import (
    build_storyboard_prompt,
    build_cover_prompt,
    build_inner_prompt,
    build_back_prompt,
    page_plan_scene_for,
)


@pytest.fixture
def spec():
    return {
        "issue_number": "01",
        "date": "MAY 2026",
        "overrides": {},
        "slug": "test-01",
    }


@pytest.fixture
def layers_4page():
    return {
        "subject": {
            "name": "naipi",
            "display_name": {"en": "Naipi"},
            "traits": "tabby cat with charcoal markings",
        },
        "theme": {
            "theme_world": "outer space, lunar regolith",
            "default_cover_line": {"en": "THE COSMOS ISSUE / {{PROTAGONIST_NAME}} walks the Moon"},
            "page_plan_hints": [
                "01: cover hero — character at module windowsill",
                "02: action — chasing toy across moonlit floor",
                "03: quiet — curled by viewport",
                "04: back coda — distant silhouette under crescent",
            ],
        },
        "layout": {
            "page_count": 4,
            "storyboard_grid": "2x2",
        },
        "brand": {"masthead": "MEOW LIFE"},
        "style": {"style_anchor": "Annie Leibovitz, Hasselblad H6D-100c"},
    }


@pytest.fixture
def layers_9page(layers_4page):
    layers_4page["layout"] = {"page_count": 9, "storyboard_grid": "3x3"}
    layers_4page["theme"]["page_plan_hints"] = [
        f"{i:02d}: scene {i}" for i in range(1, 10)
    ]
    return layers_4page


def test_placeholder_map_includes_grid_keys(spec, layers_4page):
    pmap = build_placeholder_map(spec, layers_4page)
    assert pmap["{{GRID_ROWS}}"] == "2"
    assert pmap["{{GRID_COLS}}"] == "2"
    assert pmap["{{PAGE_COUNT}}"] == "4"
    assert pmap["{{PAGE_NUMBER_RANGE}}"] == "01-04"


def test_placeholder_map_3x3(spec, layers_9page):
    pmap = build_placeholder_map(spec, layers_9page)
    assert pmap["{{GRID_ROWS}}"] == "3"
    assert pmap["{{GRID_COLS}}"] == "3"
    assert pmap["{{PAGE_COUNT}}"] == "9"
    assert pmap["{{PAGE_NUMBER_RANGE}}"] == "01-09"


def test_page_plan_block_renders_all_hints(spec, layers_4page):
    pmap = build_placeholder_map(spec, layers_4page)
    block = pmap["{{PAGE_PLAN_BLOCK}}"]
    for i in range(1, 5):
        assert f"{i:02d}:" in block


def test_storyboard_prompt_substitutes_grid(spec, layers_4page):
    prompt = build_storyboard_prompt(spec, layers_4page)
    assert "2×2 grid" in prompt
    assert "4 cells" in prompt
    assert "01-04" in prompt
    assert "tabby cat" in prompt
    assert "outer space" in prompt
    assert "{{" not in prompt, f"unsubstituted placeholders in:\n{prompt}"


def test_storyboard_prompt_3x3(spec, layers_9page):
    prompt = build_storyboard_prompt(spec, layers_9page)
    assert "3×3 grid" in prompt
    assert "9 cells" in prompt
    assert "01-09" in prompt
    assert "{{" not in prompt


def test_cover_prompt_substitutes(spec, layers_4page):
    prompt = build_cover_prompt(spec, layers_4page)
    assert "MEOW LIFE" in prompt
    assert "Naipi" in prompt
    assert "Annie Leibovitz" in prompt
    assert "{{" not in prompt


def test_inner_prompt_uses_scene(spec, layers_4page):
    prompt = build_inner_prompt(spec, layers_4page, scene="chasing toy across lunar floor")
    assert "chasing toy across lunar floor" in prompt
    assert "tabby cat" in prompt
    assert "{{" not in prompt


def test_back_prompt_with_scene(spec, layers_4page):
    prompt = build_back_prompt(spec, layers_4page, scene="distant silhouette")
    assert "distant silhouette" in prompt
    assert "tabby cat" in prompt
    assert "{{" not in prompt


def test_back_prompt_empty_scene_collapses(spec, layers_4page):
    prompt = build_back_prompt(spec, layers_4page)
    # SCENE collapses to empty; the template's surrounding language stays
    assert "{{" not in prompt
    assert "quiet coda" in prompt or "negative space" in prompt


def test_page_plan_scene_for_strips_prefix(layers_4page):
    s = page_plan_scene_for(layers_4page, 2)
    assert s == "action — chasing toy across moonlit floor"


def test_page_plan_scene_for_out_of_range(layers_4page):
    assert page_plan_scene_for(layers_4page, 99) == ""
    assert page_plan_scene_for(layers_4page, 0) == ""


def test_layout_default_when_missing():
    """If spec has no layout (edge case), default to 2x2."""
    spec = {"issue_number": "01", "date": "MAY 2026", "overrides": {}}
    layers = {
        "subject": {"name": "x", "display_name": {"en": "X"}, "traits": "t"},
        "theme": {"theme_world": "tw", "default_cover_line": {"en": "L"},
                  "page_plan_hints": ["01: x"]},
        "layout": {},  # missing keys
        "brand": {"masthead": "M"},
        "style": {"style_anchor": "S"},
    }
    pmap = build_placeholder_map(spec, layers)
    assert pmap["{{GRID_ROWS}}"] == "2"
    assert pmap["{{GRID_COLS}}"] == "2"
