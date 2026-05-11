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
WEASYPRINT_AVAILABLE, WEASYPRINT_REASON = WeasyprintCompose.dependency_status()
requires_weasyprint = pytest.mark.skipif(
    not WEASYPRINT_AVAILABLE, reason=WEASYPRINT_REASON
)


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


@requires_weasyprint
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
    assert meta["size_mb"] > 0.04  # rough plausibility (40 KB+)

    # Verify intermediate HTML written
    html_path = out_pdf.with_suffix(".html")
    assert html_path.is_file()
    html_text = html_path.read_text(encoding="utf-8")
    # Cosmos article copy should appear
    assert "DEPARTURE" in html_text or "EARTHRISE" in html_text
    # Brand masthead should appear
    assert "MEOW LIFE" in html_text


@requires_weasyprint
def test_feature_spread_renders_via_regions(issue_dir):
    """Regions-driven feature-spread emits region divs (not legacy
    .grid-2-7-5 markup)."""
    layout = yaml.safe_load((SKILL_ROOT / "library/layouts/editorial-16page.yaml").read_text())
    brand = yaml.safe_load((SKILL_ROOT / "library/brands/meow-life.yaml").read_text())
    article = yaml.safe_load((SKILL_ROOT / "library/articles/cosmos-luna-may-2026.yaml").read_text())

    images_dir = issue_dir / "images"
    _make_placeholder_pngs(images_dir, layout)

    tool = WeasyprintCompose()
    layout_j2 = SKILL_ROOT / "library/layouts/editorial-16page.html.j2"
    out_pdf = issue_dir / "magazine.pdf"
    tool.render_template(
        layout_j2=layout_j2,
        context={
            "layout": layout, "brand": brand, "article": article,
            "spec": {"slug": "test"},
            "language": brand.get("default_language", "en"),
            "issue_dir": str(issue_dir), "images_root": str(images_dir),
        },
        out_path=out_pdf,
        save_html=True,
    )
    html = out_pdf.with_suffix(".html").read_text(encoding="utf-8")
    # Region divs are present (region id=hero_image → class="region region-hero_image")
    assert 'class="region region-hero_image"' in html or 'region region-hero_image' in html
    # Sanity: data-role attribute is present (uniquely identifies regions-driven render)
    assert 'data-role="image"' in html
    assert 'data-role="image_grid"' in html  # 3 captioned strips
    # 3 feature-spread instances × 1 hero_image each = at least 3
    assert html.count('data-role="image"') >= 3
