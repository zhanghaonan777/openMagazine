"""Tests for prompt_builder_v2."""
import pytest

from lib.prompt_builder_v2 import (
    build_storyboard_prompt_v2,
    build_upscale_prompt,
    ROLE_TEMPLATES,
)


@pytest.fixture
def spec():
    return {"slug": "test", "issue_number": "01", "date": "MAY 2026", "overrides": {}}


@pytest.fixture
def layers():
    return {
        "subject": {"name": "luna", "display_name": {"en": "Luna"}, "traits": "tabby cat"},
        "theme": {"theme_world": "outer space", "default_cover_line": {"en": "L"},
                  "page_plan_hints": []},
        "layout": {"page_count": 16, "storyboard_grid": "6x4",
                   "image_slots": [
                       {"id": "cover_hero", "role": "cover_hero", "aspect": "3:4", "spread_idx": 1},
                       {"id": "back_coda", "role": "back_coda", "aspect": "2:3", "spread_idx": 9},
                   ]},
        "brand": {"masthead": "M"},
        "style": {"style_anchor": "Annie Leibovitz, Hasselblad H6D"},
    }


def test_role_templates_complete():
    for role in ("portrait", "scene", "environment", "detail", "cover_hero", "back_coda"):
        assert role in ROLE_TEMPLATES


def test_build_upscale_portrait(spec, layers):
    p = build_upscale_prompt(role="portrait", spec=spec, layers=layers,
                             slot_id="spread-03.feature_hero",
                             scene="character at boulder, hand on rock",
                             aspect="3:4")
    assert "tabby cat" in p
    assert "character at boulder" in p
    assert "Annie Leibovitz" in p
    assert "{{" not in p


def test_build_upscale_environment(spec, layers):
    p = build_upscale_prompt(role="environment", spec=spec, layers=layers,
                             slot_id="spread-05.pullquote_environment",
                             scene="wide lunar landscape, tiny figure on horizon",
                             aspect="16:10")
    assert "wide lunar landscape" in p
    assert "16:10" in p
    assert "{{" not in p


def test_unknown_role_raises(spec, layers):
    with pytest.raises(ValueError, match="unknown role"):
        build_upscale_prompt(role="banana", spec=spec, layers=layers,
                             slot_id="x", scene="y", aspect="1:1")


def test_build_storyboard_v2(spec, layers):
    plan = {
        "outer_aspect": "2:3",
        "outer_size_px": [1024, 1536],
        "grid": {"rows": 1, "cols": 2},
        "cells": [
            {"slot_id": "spread-01.cover_hero", "row": 0, "col": 0, "rowspan": 1, "colspan": 1,
             "aspect": "3:4", "bbox_px": [0, 0, 512, 1536], "page_label": "01"},
            {"slot_id": "spread-09.back_coda", "row": 0, "col": 1, "rowspan": 1, "colspan": 1,
             "aspect": "2:3", "bbox_px": [512, 0, 512, 1536], "page_label": "02"},
        ],
    }
    p = build_storyboard_prompt_v2(spec, layers,
                                   plan=plan,
                                   scenes_by_slot={
                                       "spread-01.cover_hero": "hero on lunar surface",
                                       "spread-09.back_coda": "tiny figure at horizon",
                                   })
    assert "spread-01.cover_hero" in p
    assert "01" in p
    assert "tabby cat" in p
    assert "hero on lunar surface" in p
    # Outer canvas declared
    assert "1024" in p and "1536" in p
    # No unfilled placeholders
    assert "{{" not in p
