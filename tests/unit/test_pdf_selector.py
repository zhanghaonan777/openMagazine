"""Tests for pdf_selector."""
import pytest

from tools.pdf.pdf_selector import PdfSelector


def test_v1_layout_routes_to_reportlab():
    sel = PdfSelector()
    backend = sel.choose_backend(layout={"schema_version": 1, "name": "plain-4"})
    assert backend.provider == "reportlab"


def test_v2_layout_routes_to_weasyprint():
    sel = PdfSelector()
    backend = sel.choose_backend(layout={"schema_version": 2, "name": "editorial-16page"})
    assert backend.provider == "weasyprint"


def test_unknown_schema_raises():
    sel = PdfSelector()
    with pytest.raises(ValueError, match="schema_version"):
        sel.choose_backend(layout={"schema_version": 99})


def test_missing_schema_raises():
    sel = PdfSelector()
    with pytest.raises(ValueError, match="schema_version"):
        sel.choose_backend(layout={"name": "no-schema"})
