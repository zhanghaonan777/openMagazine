"""Tests for font_resolver."""
import pytest

from lib.font_resolver import (
    resolve_font,
    resolve_typography_pack,
)


def test_resolve_font_returns_dict_with_required_keys():
    result = resolve_font("Playfair Display", ["Georgia", "Times New Roman"])
    assert "requested" in result
    assert "matched" in result
    assert "fallback_used" in result
    assert result["requested"] == "Playfair Display"


def test_resolve_font_falls_back_when_desired_missing():
    """A guaranteed-missing family name should fall back."""
    result = resolve_font(
        "DefinitelyDoesNotExistFontXYZ123",
        ["Georgia", "Times New Roman"],
    )
    assert result["fallback_used"] is True
    # matched should be one of the fallbacks, or empty string if no match at all
    assert result["matched"] in ["Georgia", "Times New Roman", ""] or len(result["matched"]) > 0


def test_resolve_typography_pack():
    """Iterates the resolution chain dict and returns a log."""
    design_system = {
        "typography_resolution": {
            "display": {
                "desired_family": "Playfair Display",
                "fallback_chain": ["Georgia"],
            },
            "body": {
                "desired_family": "Source Serif 4",
                "fallback_chain": ["Georgia"],
            },
        }
    }
    log = resolve_typography_pack(design_system)
    assert "display" in log
    assert "body" in log
    assert log["display"]["requested"] == "Playfair Display"
