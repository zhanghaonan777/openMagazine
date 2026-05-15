"""Tests for output_selector."""
import pytest

from tools.output.output_selector import OutputSelector


def test_a4_magazine_routes_to_weasyprint():
    sel = OutputSelector()
    backend = sel.choose_backend(target={"format": "a4-magazine", "realizer": "weasyprint"})
    assert backend.provider == "weasyprint"


def test_photobook_routes_to_reportlab():
    sel = OutputSelector()
    backend = sel.choose_backend(target={"format": "photobook-plain", "realizer": "reportlab"})
    assert backend.provider == "reportlab"


def test_magazine_pptx_routes_to_presentations():
    sel = OutputSelector()
    backend = sel.choose_backend(target={"format": "magazine-pptx", "realizer": "presentations"})
    assert backend.provider == "presentations"


def test_unknown_realizer_raises():
    sel = OutputSelector()
    with pytest.raises(ValueError, match="realizer"):
        sel.choose_backend(target={"format": "x", "realizer": "InventedRealizer"})


def test_default_target_when_none():
    """No target arg → default to a4-magazine."""
    sel = OutputSelector()
    backend = sel.choose_backend(target=None)
    assert backend.provider == "weasyprint"


def test_legacy_layout_dict_compatibility():
    """choose_backend(layout=...) — old pdf_selector API — still works."""
    sel = OutputSelector()
    backend = sel.choose_backend(layout={"schema_version": 2, "name": "editorial-16page"})
    assert backend.provider == "weasyprint"
