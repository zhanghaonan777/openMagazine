"""Integration test for the manifest-driven WeasyPrint render path.

Proves that slide_manifest.json is a sufficient input to produce a PDF
end-to-end, without going through the Jinja2 templates. Visual fidelity
is intentionally lower than the legacy Jinja path; the canonical
assertion here is "manifest → PDF works, has the expected page count,
and the HTML contains text resolved from the manifest".
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from PIL import Image

from lib.manifest_to_html import manifest_to_html
from lib.slide_manifest_builder import build_from_spec_path
from tools.output.weasyprint_compose import WeasyprintCompose

SKILL_ROOT = Path(__file__).resolve().parents[2]
COSMOS_SPEC = SKILL_ROOT / "library" / "issue-specs" / "cosmos-luna-may-2026.yaml"
EDITORIAL_LAYOUT = SKILL_ROOT / "library" / "layouts" / "editorial-16page.yaml"

WEASYPRINT_AVAILABLE, WEASYPRINT_REASON = WeasyprintCompose.dependency_status()
requires_weasyprint = pytest.mark.skipif(
    not WEASYPRINT_AVAILABLE, reason=WEASYPRINT_REASON
)


def _make_placeholder_pngs(images_dir: Path, layout: dict):
    for slot in layout["image_slots"]:
        spread_dir = images_dir / f"spread-{slot['spread_idx']:02d}"
        spread_dir.mkdir(parents=True, exist_ok=True)
        out = spread_dir / f"{slot['id']}.png"
        Image.new("RGB", (200, 200), color=(40, 40, 40)).save(out)


@pytest.fixture
def issue_dir(tmp_path):
    d = tmp_path / "issue"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# Pure manifest_to_html (no WeasyPrint dependency)
# ---------------------------------------------------------------------------


def test_manifest_to_html_contains_resolved_text():
    """HTML must render text fields resolved by the builder."""
    manifest = build_from_spec_path(COSMOS_SPEC, target_format="a4-magazine", locale="en")
    html = manifest_to_html(manifest)
    # Brand masthead (resolved through cover_kicker text_field fallback path)
    assert "FEATURE STORY" in html
    # Spread 3 DEPARTURE title
    assert "DEPARTURE" in html
    # Spread 6 EARTHRISE title
    assert "EARTHRISE" in html
    # Spread 7 portrait wall title
    assert "STILLS FROM A MISSION" in html


def test_manifest_to_html_emits_region_divs_with_claim_role():
    """data-claim-role attributes survive into the HTML for downstream QA / a11y."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    html = manifest_to_html(manifest)
    assert 'data-claim-role="kicker"' in html
    assert 'data-claim-role="claim_title"' in html
    assert 'data-claim-role="proof_object"' in html
    assert 'data-claim-role="support_note"' in html


def test_manifest_to_html_localises_to_zh():
    manifest = build_from_spec_path(COSMOS_SPEC, locale="zh")
    html = manifest_to_html(manifest)
    assert "启程" in html  # DEPARTURE zh
    assert "地升" in html  # EARTHRISE zh


def test_manifest_to_html_named_pages_match_pages_per_instance():
    """@page slide1 for 1-page (cover, back-cover) + slide2 for facing spreads."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    html = manifest_to_html(manifest)
    assert "@page slide1" in html  # cover + back-cover
    assert "@page slide2" in html  # everything else
    # 9 slides total
    assert html.count('class="slide ') == 9


# ---------------------------------------------------------------------------
# Full WeasyPrint render (requires native deps)
# ---------------------------------------------------------------------------


@requires_weasyprint
def test_manifest_renders_to_pdf_with_expected_page_count(issue_dir):
    layout = yaml.safe_load(EDITORIAL_LAYOUT.read_text())
    images_dir = issue_dir / "images"
    _make_placeholder_pngs(images_dir, layout)

    manifest = build_from_spec_path(COSMOS_SPEC, target_format="a4-magazine", locale="en")

    tool = WeasyprintCompose()
    meta = tool.render_from_manifest(
        manifest, issue_dir=issue_dir, out_path=issue_dir / "magazine.pdf"
    )

    assert (issue_dir / "magazine.pdf").is_file()
    # 9 slides → 9 PDF pages (manifest path renders one slide per PDF page,
    # with widths matching pages_per_instance).
    assert meta["page_count"] == 9, f"got {meta['page_count']}"
    assert meta["size_mb"] > 0.01  # at least 10 KB

    # HTML sidecar exists and includes the resolved text.
    html_path = (issue_dir / "magazine.pdf").with_suffix(".html")
    assert html_path.is_file()
    html_text = html_path.read_text(encoding="utf-8")
    assert "DEPARTURE" in html_text
    assert "FEATURE STORY" in html_text


@requires_weasyprint
def test_legacy_jinja_path_still_works_alongside_manifest(issue_dir):
    """Regression: render_from_manifest must NOT break the legacy run()."""
    layout = yaml.safe_load(EDITORIAL_LAYOUT.read_text())
    brand = yaml.safe_load((SKILL_ROOT / "library/brands/meow-life.yaml").read_text())
    article = yaml.safe_load((SKILL_ROOT / "library/articles/cosmos-luna-may-2026.yaml").read_text())

    images_dir = issue_dir / "images"
    _make_placeholder_pngs(images_dir, layout)

    tool = WeasyprintCompose()
    meta = tool.run(
        issue_dir=issue_dir, layout=layout, brand=brand, article=article,
        spec={"slug": "test"},
        # The next two kwargs simulate OutputSelector multi-realizer wiring;
        # absorbing them without crash is the v0.3.2 bug-fix.
        design_system={"output_targets": [{"format": "a4-magazine", "realizer": "weasyprint"}]},
        target={"format": "a4-magazine", "realizer": "weasyprint"},
    )
    assert meta["pdf_path"]
    assert meta["page_count"] >= 9
