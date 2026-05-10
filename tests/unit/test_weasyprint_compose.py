"""Tests for WeasyprintCompose."""
from pathlib import Path

import pytest

from tools.pdf.weasyprint_compose import WeasyprintCompose


def test_renders_minimal_html(tmp_path):
    """Render a trivial HTML to PDF; verify file exists and >0 bytes."""
    tool = WeasyprintCompose()
    html = "<html><body><h1>Hello</h1></body></html>"
    out = tmp_path / "out.pdf"
    tool.render_html_string(html, out)
    assert out.is_file()
    assert out.stat().st_size > 100


def test_render_returns_metadata(tmp_path):
    tool = WeasyprintCompose()
    html = "<html><body><div style='page-break-after: always'>1</div><div>2</div></body></html>"
    out = tmp_path / "out.pdf"
    meta = tool.render_html_string(html, out)
    assert meta["pdf_path"] == str(out)
    assert meta["size_mb"] > 0
    assert meta["page_count"] >= 2


def test_descriptor():
    t = WeasyprintCompose()
    d = t.descriptor()
    assert d["capability"] == "pdf_compose"
    assert d["provider"] == "weasyprint"
