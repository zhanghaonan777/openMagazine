"""Tests for the editable HTML realizer + article-patch round-trip."""
from __future__ import annotations

import copy
import json
import pathlib

import pytest
import yaml

from lib.article_patch import PatchError, apply_patch
from lib.manifest_to_html import manifest_to_html
from lib.slide_manifest_builder import build_from_spec_path
from tools.output.html_interactive_compose import HtmlInteractiveCompose
from tools.output.output_selector import OutputSelector

SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]
COSMOS_SPEC = SKILL_ROOT / "library" / "issue-specs" / "cosmos-luna-may-2026.yaml"
COSMOS_ARTICLE = SKILL_ROOT / "library" / "articles" / "cosmos-luna-may-2026.yaml"


# ---------------------------------------------------------------------------
# manifest_to_html interactive mode
# ---------------------------------------------------------------------------


def test_interactive_html_has_contenteditable_on_text_regions():
    manifest = build_from_spec_path(COSMOS_SPEC)
    html = manifest_to_html(manifest, interactive=True)
    assert 'contenteditable="true"' in html
    # Exactly one contenteditable per text region with bind_field — there
    # are 21 such regions across cosmos-luna's 9 slides today.
    assert html.count('contenteditable="true"') == 21


def test_interactive_html_emits_toolbar_and_js():
    manifest = build_from_spec_path(COSMOS_SPEC)
    html = manifest_to_html(manifest, interactive=True)
    assert 'id="om-toolbar"' in html
    assert 'id="om-save-btn"' in html
    assert "Object.fromEntries(edits)" in html  # the save JS
    assert "article-patch.json" in html  # download filename


def test_non_interactive_html_has_no_contenteditable():
    manifest = build_from_spec_path(COSMOS_SPEC)
    html = manifest_to_html(manifest, interactive=False)
    assert "contenteditable" not in html
    assert "om-toolbar" not in html


def test_body_data_attrs_carry_locale_and_slug():
    manifest = build_from_spec_path(COSMOS_SPEC, locale="zh")
    html = manifest_to_html(manifest, interactive=True)
    assert 'data-spec-slug="cosmos-luna-may-2026"' in html
    assert 'data-locale="zh"' in html
    assert 'data-interactive="true"' in html


# ---------------------------------------------------------------------------
# HtmlInteractiveCompose tool
# ---------------------------------------------------------------------------


def test_html_interactive_compose_writes_html_and_sidecar(tmp_path):
    manifest = build_from_spec_path(COSMOS_SPEC)
    issue_dir = tmp_path / "issue"
    issue_dir.mkdir()
    tool = HtmlInteractiveCompose()
    meta = tool.run(manifest=manifest, issue_dir=issue_dir)

    html_path = pathlib.Path(meta["html_path"])
    assert html_path.is_file()
    assert html_path.parent == issue_dir / "magazine-interactive"
    assert html_path.name == "index.html"
    assert meta["editable_regions"] == 21
    assert meta["slide_count"] == 9

    sidecar = html_path.parent / "compose_result.json"
    assert sidecar.is_file()
    sidecar_data = json.loads(sidecar.read_text())
    assert sidecar_data["spec_slug"] == "cosmos-luna-may-2026"
    assert sidecar_data["locale"] == "en"


def test_output_selector_routes_html_interactive():
    """OutputSelector must pick HtmlInteractiveCompose for realizer='html-interactive'."""
    selector = OutputSelector()
    backend = selector.choose_backend(target={"realizer": "html-interactive"})
    assert isinstance(backend, HtmlInteractiveCompose)


# ---------------------------------------------------------------------------
# article_patch
# ---------------------------------------------------------------------------


@pytest.fixture
def cosmos_article():
    return yaml.safe_load(COSMOS_ARTICLE.read_text(encoding="utf-8"))


def test_patch_top_level_bilingual_field_preserves_other_locale(cosmos_article):
    """Patching cover_line.en must leave cover_line.zh intact."""
    original_zh = cosmos_article["cover_line"]["zh"]
    patch = {
        "locale": "en",
        "patches": {"cover_line": "An astronaut who never came back."},
    }
    out = apply_patch(cosmos_article, patch)
    assert out["cover_line"]["en"] == "An astronaut who never came back."
    assert out["cover_line"]["zh"] == original_zh
    # Original article must not be mutated.
    assert cosmos_article["cover_line"]["en"] != "An astronaut who never came back."


def test_patch_spread_field_by_idx(cosmos_article):
    """spread.3.title patches spread_copy[where idx=3].title at the patch locale."""
    patch = {
        "locale": "en",
        "patches": {"spread.3.title": "Four billion years of silence"},
    }
    out = apply_patch(cosmos_article, patch)
    spread3 = next(s for s in out["spread_copy"] if s["idx"] == 3)
    assert spread3["title"]["en"] == "Four billion years of silence"
    # Chinese title still there
    assert spread3["title"]["zh"] == "启程"


def test_patch_unknown_spread_idx_raises(cosmos_article):
    patch = {
        "locale": "en",
        "patches": {"spread.99.title": "nope"},
    }
    with pytest.raises(PatchError, match="no spread_copy entry with idx=99"):
        apply_patch(cosmos_article, patch)


def test_patch_lenient_skips_unknown(cosmos_article):
    patch = {
        "locale": "en",
        "patches": {
            "spread.99.title": "skipped",
            "cover_line": "kept",
        },
    }
    out = apply_patch(cosmos_article, patch, strict=False)
    assert out["cover_line"]["en"] == "kept"
    # spread 99 didn't sneak in.
    assert not any(s.get("idx") == 99 for s in out["spread_copy"])


def test_patch_zh_locale(cosmos_article):
    """Patching with locale=zh must touch .zh and leave .en intact."""
    original_en = cosmos_article["cover_line"]["en"]
    patch = {
        "locale": "zh",
        "patches": {"cover_line": "再见月亮"},
    }
    out = apply_patch(cosmos_article, patch)
    assert out["cover_line"]["zh"] == "再见月亮"
    assert out["cover_line"]["en"] == original_en


def test_patch_bad_value_raises_in_strict_mode(cosmos_article):
    patch = {"locale": "en", "patches": {"cover_line": 42}}
    with pytest.raises(PatchError, match="must be a string"):
        apply_patch(cosmos_article, patch)


def test_patch_empty_patches_returns_copy(cosmos_article):
    out = apply_patch(cosmos_article, {"locale": "en", "patches": {}})
    assert out == cosmos_article
    # And it's a deep copy, not the same object.
    assert out is not cosmos_article


# ---------------------------------------------------------------------------
# End-to-end: edit a manifest's text, simulate patch download, apply back
# ---------------------------------------------------------------------------


def test_end_to_end_round_trip(cosmos_article):
    """Simulate: builder -> HTML interactive -> user 'edits' -> patch -> applied article."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    html = manifest_to_html(manifest, interactive=True)
    # Confirm the bind_field we plan to patch is present in the HTML.
    assert 'data-bind-field="spread.3.title"' in html

    # The browser would produce this JSON; we hand-build the equivalent.
    patch = {
        "generated_at": "2026-05-15T16:00:00Z",
        "spec_slug": "cosmos-luna-may-2026",
        "locale": "en",
        "patches": {
            "spread.3.title": "Four billion years of silence",
            "cover_line": "An astronaut who never came back.",
        },
    }
    out = apply_patch(cosmos_article, patch)

    # The article round-trips: rebuild a manifest from the patched article and
    # confirm the new text appears in the HTML.
    import lib.slide_manifest_builder as smb
    from lib.spec_loader import load_spec, resolve_layers
    from lib.regions_loader import load_regions, RegionsNotFoundError

    spec, _ = load_spec(COSMOS_SPEC)
    layers = resolve_layers(spec)
    regions_by_type = {}
    for sp in layers["layout"]["spread_plan"]:
        try:
            regions_by_type[sp["type"]] = load_regions(sp["type"])
        except RegionsNotFoundError:
            pass
    design_system = layers.get("design_system") or {}
    target = design_system["output_targets"][0]
    rebuilt = smb.build_manifest(
        spec, layers, out, target,
        locale="en", regions_by_type=regions_by_type,
    )
    rebuilt_html = manifest_to_html(rebuilt, interactive=True)
    assert "Four billion years of silence" in rebuilt_html
    assert "An astronaut who never came back." in rebuilt_html
