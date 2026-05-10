"""Tests for build_pdf._discover — simple-mode image discovery.

Simple mode writes to <issue>/images/page-NN.png (cover IS page-01).
The discover function reads that layout, sorted by NN ascending.
"""
from pathlib import Path

from tools.pdf.reportlab_compose import _discover


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"PNG_PLACEHOLDER")


def test_discover_simple_mode_images_dir(tmp_path):
    """When <issue>/images/ exists with page-*.png, return them in NN order.
    cover IS page-01; no separate cover_4k.png expected."""
    issue = tmp_path / "naigai-fauve-01"
    for nn in (1, 2, 3, 4):
        _touch(issue / "images" / f"page-{nn:02d}.png")

    result = _discover(issue)

    names = [p.name for p in result]
    assert names == ["page-01.png", "page-02.png", "page-03.png", "page-04.png"]
    # All from images/, sanity check
    assert all(p.parent.name == "images" for p in result)


def test_discover_simple_mode_sorted_by_NN_not_lexicographic(tmp_path):
    """page-2 comes before page-10 (numeric, not lex)."""
    issue = tmp_path / "x"
    for nn in (1, 2, 3, 10, 11):
        _touch(issue / "images" / f"page-{nn:02d}.png")

    result = _discover(issue)

    assert [p.name for p in result] == [
        "page-01.png", "page-02.png", "page-03.png", "page-10.png", "page-11.png"
    ]


def test_discover_no_images_dir_returns_empty(tmp_path):
    """If <issue>/images/ doesn't exist or is empty, return empty list."""
    issue = tmp_path / "empty"
    issue.mkdir()

    assert _discover(issue) == []

    # also true if images/ exists but has no page-*.png
    (issue / "images").mkdir()
    assert _discover(issue) == []
