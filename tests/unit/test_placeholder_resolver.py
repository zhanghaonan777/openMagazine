"""Tests for placeholder_resolver."""
import pytest

from lib.placeholder_resolver import build_placeholder_map


def test_overrides_take_priority_over_layers():
    spec = {
        "issue_number": "01",
        "date": "MAY 2026",
        "overrides": {"masthead": "OVERRIDE"},
    }
    layers = {
        "subject": {"name": "luna", "display_name": {"en": "Luna"}, "traits": "..."},
        "theme": {"theme_world": "...", "default_cover_line": {"en": "..."}},
        "layout": {"page_count": 16},
        "brand": {"masthead": "MEOW LIFE"},
        "style": {"style_anchor": "..."},
    }
    pmap = build_placeholder_map(spec, layers)
    assert pmap["{{MAGAZINE_NAME}}"] == "OVERRIDE"


def test_layer_fallback():
    spec = {"issue_number": "01", "date": "MAY 2026", "overrides": {}}
    layers = {
        "subject": {"name": "luna", "display_name": {"en": "Luna"}, "traits": "T"},
        "theme": {"theme_world": "TW", "default_cover_line": {"en": "L for {{PROTAGONIST_NAME}}"}},
        "layout": {"page_count": 16},
        "brand": {"masthead": "MEOW LIFE"},
        "style": {"style_anchor": "SA"},
    }
    pmap = build_placeholder_map(spec, layers)
    assert pmap["{{TRAITS}}"] == "T"
    assert pmap["{{STYLE_ANCHOR}}"] == "SA"
    assert pmap["{{PROTAGONIST_NAME}}"] == "Luna"
    assert pmap["{{COVER_LINE}}"] == "L for Luna"
    assert pmap["{{MAGAZINE_NAME}}"] == "MEOW LIFE"
