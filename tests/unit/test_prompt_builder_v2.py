"""Tests for prompt_builder_v2."""
import pytest

from lib.prompt_builder_v2 import (
    _render_brand_authenticity_negatives,
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


def test_build_upscale_prompt_with_regions_context(spec, layers):
    regions_context = {
        "own_region": {
            "id": "hero_image",
            "rect_norm": [0.0, 0.0, 0.5, 1.0],
            "role": "image",
            "image_slot": "feature_hero",
            "image_prompt_hint": "subject lives here, sharp focus",
        },
        "sibling_regions": [
            {
                "id": "title",
                "rect_norm": [0.55, 0.15, 0.95, 0.30],
                "role": "text",
                "component": "Title",
                "image_prompt_hint": "uniform low-detail background",
            },
            {
                "id": "captioned_strip",
                "rect_norm": [0.55, 0.86, 0.95, 0.98],
                "role": "image_grid",
                "image_prompt_hint": "calm strip",
            },
        ],
    }
    p = build_upscale_prompt(
        role="portrait", spec=spec, layers=layers,
        slot_id="spread-03.feature_hero",
        scene="character at boulder, hand on rock",
        aspect="3:4",
        regions_context=regions_context,
    )
    # Own region declared
    assert "hero_image" in p
    assert "subject lives here" in p
    # Sibling regions declared and explicitly off-limits
    assert "title" in p
    assert "captioned_strip" in p
    assert "uniform low-detail background" in p
    # No unfilled placeholders
    assert "{{" not in p


def test_build_upscale_prompt_without_regions_context_unchanged(spec, layers):
    """Backward compatibility: omit regions_context → prompt body matches
    the existing shape (no regions section)."""
    p_old = build_upscale_prompt(
        role="portrait", spec=spec, layers=layers,
        slot_id="spread-03.feature_hero",
        scene="character at boulder",
        aspect="3:4",
    )
    p_new = build_upscale_prompt(
        role="portrait", spec=spec, layers=layers,
        slot_id="spread-03.feature_hero",
        scene="character at boulder",
        aspect="3:4",
        regions_context=None,
    )
    assert p_old == p_new
    assert "sibling regions" not in p_old.lower()


def test_build_storyboard_v2_with_regions_by_spread(spec, layers):
    plan = {
        "outer_aspect": "2:3",
        "outer_size_px": [1024, 1536],
        "grid": {"rows": 1, "cols": 2},
        "cells": [
            {"slot_id": "spread-03.feature_hero", "row": 0, "col": 0,
             "rowspan": 1, "colspan": 1, "aspect": "3:4",
             "bbox_px": [0, 0, 512, 1536], "page_label": "01"},
            {"slot_id": "spread-09.back_coda", "row": 0, "col": 1,
             "rowspan": 1, "colspan": 1, "aspect": "2:3",
             "bbox_px": [512, 0, 512, 1536], "page_label": "02"},
        ],
    }
    regions_by_spread_type = {
        "feature-spread": [
            {"id": "hero_image", "rect_norm": [0, 0, 0.5, 1], "role": "image",
             "image_slot": "feature_hero", "aspect": "3:4"},
            {"id": "title", "rect_norm": [0.55, 0.15, 0.95, 0.3], "role": "text",
             "component": "Title", "text_field": "title"},
        ],
    }
    spread_type_by_idx = {3: "feature-spread", 9: "back-cover"}
    p = build_storyboard_prompt_v2(
        spec, layers,
        plan=plan,
        scenes_by_slot={"spread-03.feature_hero": "hero", "spread-09.back_coda": "coda"},
        regions_by_spread_type=regions_by_spread_type,
        spread_type_by_idx=spread_type_by_idx,
    )
    assert "spread-03.feature_hero" in p
    # The block names the spread + type
    assert "spread 3" in p.lower() or "feature-spread" in p.lower()
    # back-cover has no regions yaml in this test → no layout block for spread 9
    assert "spread-09.back_coda" in p
    assert "{{" not in p


def test_build_upscale_prompt_embeds_brand_authenticity(spec, layers):
    """Upscale + storyboard prompts append brand_authenticity negatives when
    design_system is present in layers."""
    layers_with_ds = {
        **layers,
        "design_system": {
            "brand_authenticity": {
                "do_not_generate": ["logo", "mascot"],
                "do_not_approximate": ["MEOW LIFE wordmark"],
            }
        },
    }

    # --- upscale ---
    p = build_upscale_prompt(
        role="portrait", spec=spec, layers=layers_with_ds,
        slot_id="spread-03.feature_hero",
        scene="character at boulder",
        aspect="3:4",
    )
    assert "Brand authenticity (additional negative prompt):" in p
    assert "no logo" in p
    assert "no mascot" in p
    assert "no MEOW LIFE wordmark" in p

    # --- storyboard ---
    plan = {
        "outer_aspect": "2:3",
        "outer_size_px": [1024, 1536],
        "grid": {"rows": 1, "cols": 1},
        "cells": [
            {"slot_id": "spread-01.cover_hero", "row": 0, "col": 0,
             "rowspan": 1, "colspan": 1, "aspect": "3:4",
             "bbox_px": [0, 0, 1024, 1536], "page_label": "01"},
        ],
    }
    sb = build_storyboard_prompt_v2(
        spec, layers_with_ds,
        plan=plan,
        scenes_by_slot={"spread-01.cover_hero": "hero on lunar surface"},
    )
    assert "Brand authenticity (additional negative prompt):" in sb
    assert "no logo" in sb
    assert "no MEOW LIFE wordmark" in sb

    # --- no design_system → no negatives block ---
    p_plain = build_upscale_prompt(
        role="portrait", spec=spec, layers=layers,
        slot_id="spread-03.feature_hero",
        scene="character at boulder",
        aspect="3:4",
    )
    assert "Brand authenticity" not in p_plain


def test_render_brand_authenticity_negatives_empty_when_no_design_system(layers):
    """Helper returns empty string when layers has no design_system key."""
    assert _render_brand_authenticity_negatives(layers) == ""


def test_render_brand_authenticity_negatives_empty_when_no_entries():
    """Helper returns empty string when brand_authenticity lists are empty."""
    layers_empty = {
        "design_system": {
            "brand_authenticity": {
                "do_not_generate": [],
                "do_not_approximate": [],
            }
        }
    }
    assert _render_brand_authenticity_negatives(layers_empty) == ""
