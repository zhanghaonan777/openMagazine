"""Integration test: render full editorial-16page PDF with placeholder PNGs.

No Vertex / no Codex calls. Generates a 1x1 black PNG for each image slot,
fills in article + brand + layout, runs Weasyprint, asserts PDF has expected
page count and is plausibly sized (>50KB).
"""
from pathlib import Path

import pytest
import yaml
from PIL import Image

from tools.pdf.weasyprint_compose import WeasyprintCompose


SKILL_ROOT = Path(__file__).resolve().parents[2]


def _make_placeholder_pngs(images_dir: Path, layout: dict):
    """Create one tiny black PNG per image_slot."""
    for slot in layout["image_slots"]:
        spread_dir = images_dir / f"spread-{slot['spread_idx']:02d}"
        spread_dir.mkdir(parents=True, exist_ok=True)
        out = spread_dir / f"{slot['id']}.png"
        Image.new("RGB", (100, 100), color="black").save(out)


@pytest.fixture
def issue_dir(tmp_path):
    d = tmp_path / "issue"
    d.mkdir()
    return d


def test_renders_editorial_16page_with_placeholders(issue_dir):
    layout = yaml.safe_load((SKILL_ROOT / "library/layouts/editorial-16page.yaml").read_text())
    brand = yaml.safe_load((SKILL_ROOT / "library/brands/meow-life.yaml").read_text())
    article = yaml.safe_load((SKILL_ROOT / "library/articles/cosmos-luna-may-2026.yaml").read_text())

    images_dir = issue_dir / "images"
    _make_placeholder_pngs(images_dir, layout)

    tool = WeasyprintCompose()
    layout_j2 = SKILL_ROOT / "library/layouts/editorial-16page.html.j2"
    out_pdf = issue_dir / "magazine.pdf"
    meta = tool.render_template(
        layout_j2=layout_j2,
        context={
            "layout": layout,
            "brand": brand,
            "article": article,
            "spec": {"slug": "test"},
            "language": brand.get("default_language", "en"),
            "issue_dir": str(issue_dir),
            "images_root": str(images_dir),
        },
        out_path=out_pdf,
        save_html=True,
    )
    assert out_pdf.is_file()
    # 9 spreads (1 cover + 1 toc + 3 features + 1 pull-quote + 1 portrait-wall +
    # 1 colophon + 1 back-cover). Each spread can flow over multiple pages.
    # Expect at least 9 pages, but the spread:page mapping isn't exact —
    # accept >=9 and <=18.
    assert 9 <= meta["page_count"] <= 18, f"unexpected page count {meta['page_count']}"
    assert meta["size_mb"] > 0.05  # rough plausibility (50 KB+)

    # Verify intermediate HTML written
    html_path = out_pdf.with_suffix(".html")
    assert html_path.is_file()
    html_text = html_path.read_text(encoding="utf-8")
    # Cosmos article copy should appear
    assert "DEPARTURE" in html_text or "EARTHRISE" in html_text
    # Brand masthead should appear
    assert "MEOW LIFE" in html_text
