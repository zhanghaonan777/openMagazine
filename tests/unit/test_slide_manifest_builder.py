"""Tests for slide_manifest_builder."""
from __future__ import annotations

import json
import pathlib

import pytest
from jsonschema import Draft7Validator

from lib.slide_manifest_builder import (
    _compute_rect_px,
    _expand_image_grid,
    _image_claim_role,
    _localize,
    augment_target,
    build_from_spec_path,
    build_manifest,
    compute_design_tokens,
)


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_PATH = SKILL_ROOT / "schemas" / "artifacts" / "slide_manifest.schema.json"
COSMOS_SPEC = SKILL_ROOT / "library" / "issue-specs" / "cosmos-luna-may-2026.yaml"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# End-to-end against the real cosmos-luna spec
# ---------------------------------------------------------------------------


def test_cosmos_luna_manifest_validates_against_schema(schema):
    """The flagship test: a real spec must produce a schema-clean manifest."""
    manifest = build_from_spec_path(COSMOS_SPEC, target_format="a4-magazine", locale="en")
    errors = list(Draft7Validator(schema).iter_errors(manifest))
    assert errors == [], "\n".join(
        f"{list(e.absolute_path)}: {e.message}" for e in errors[:10]
    )


def test_cosmos_luna_has_9_slides():
    manifest = build_from_spec_path(COSMOS_SPEC)
    assert len(manifest["slides"]) == 9
    types = [s["spread_type"] for s in manifest["slides"]]
    assert types == [
        "cover", "toc", "feature-spread", "feature-spread", "pull-quote",
        "feature-spread", "portrait-wall", "colophon", "back-cover",
    ]


def test_cosmos_luna_zh_resolves_chinese_text():
    """Locale=zh must pull the Chinese variant of bilingual fields."""
    manifest = build_from_spec_path(COSMOS_SPEC, locale="zh")
    # Spread 3 DEPARTURE title in Chinese is '启程'
    slide3 = manifest["slides"][2]
    title_region = next(r for r in slide3["regions"] if r["id"] == "title")
    assert title_region["text"] == "启程"


def test_cosmos_luna_claim_role_on_feature_spread_text_fields():
    """Spread 3 text regions must carry the right claim_role hints derived
    from text_field name (kicker / lead / body)."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    slide3 = manifest["slides"][2]
    by_id = {r["id"]: r for r in slide3["regions"]}
    assert by_id["kicker"].get("claim_role") == "kicker"
    assert by_id["lead"].get("claim_role") == "claim_title"
    assert by_id["body"].get("claim_role") == "support_note"


def test_cosmos_luna_claim_role_on_proof_image_slot_spread3():
    """Spread 3 claim's proof_object.ref is 'feature_hero' (the image_slot id),
    but the regions.yaml region id is 'hero_image'. The matcher should resolve
    against the image_slot, so hero_image must still get tagged proof_object."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    slide3 = manifest["slides"][2]
    hero = next(r for r in slide3["regions"] if r["id"] == "hero_image")
    assert hero.get("claim_role") == "proof_object"


def test_cosmos_luna_claim_role_on_image_grid_spread4():
    """Spread 4 claim.proof_object.ref='feature_captioned.[1-3]' → the 3
    expanded captioned images are all proof_object."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    slide4 = manifest["slides"][3]
    cap_regions = [
        r for r in slide4["regions"] if r["id"].startswith("feature_captioned.")
    ]
    assert len(cap_regions) == 3
    assert all(r.get("claim_role") == "proof_object" for r in cap_regions)


def test_cosmos_luna_image_grid_expansion_portrait_wall():
    """portrait-wall.portrait_grid (6 slots, grid_cols=3) expands to 6 image regions."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    slide7 = manifest["slides"][6]
    image_regions = [r for r in slide7["regions"] if r["role"] == "image"]
    assert len(image_regions) == 6
    ids = [r["id"] for r in image_regions]
    assert ids == [f"portrait_wall.{i}" for i in range(1, 7)]
    # All 6 should be proof_object (claim spread 7 ref='portrait_wall.[1-6]').
    assert all(r.get("claim_role") == "proof_object" for r in image_regions)


def test_cosmos_luna_image_grid_expansion_captioned_strip():
    """feature-spread.captioned_strip (3 slots in 1 row) expands to 3 regions."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    slide3 = manifest["slides"][2]
    cap_regions = [r for r in slide3["regions"] if r["id"].startswith("feature_captioned.")]
    assert len(cap_regions) == 3
    # Sub-rects should partition the source strip [0.55, 0.86, 0.95, 0.98]
    # into 3 equal-width cells.
    strip_w = (0.95 - 0.55)
    cell_w = strip_w / 3
    for i, r in enumerate(cap_regions):
        rn = r["rect_norm"]
        assert abs(rn[0] - (0.55 + i * cell_w)) < 1e-9
        assert abs(rn[2] - (0.55 + (i + 1) * cell_w)) < 1e-9
        assert rn[1] == 0.86
        assert rn[3] == 0.98


def test_cosmos_luna_canvas_doubles_for_two_page_spread():
    """A feature-spread (2 pages) canvas is 2x cover canvas (1 page)."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    cover_hero = manifest["slides"][0]["regions"][0]  # cover_hero rect_norm = [0,0,1,1]
    feature_hero = manifest["slides"][2]["regions"][0]  # hero_image rect_norm = [0,0,0.5,1]
    # cover_hero spans full 1-page canvas; feature hero spans left half of 2-page.
    # Both should resolve to the same rect_px width (= 1 page width).
    assert cover_hero["rect_px"][2] == feature_hero["rect_px"][2]


def test_cosmos_luna_vertical_gradient_becomes_decorative():
    """The pull-quote and back-cover gradient_overlay (role: accent but
    component: VerticalGradient) becomes role=decorative in the manifest."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    slide5 = manifest["slides"][4]
    grad = next(r for r in slide5["regions"] if r["id"] == "gradient_overlay")
    assert grad["role"] == "decorative"
    assert grad["component"] == "VerticalGradient"


# ---------------------------------------------------------------------------
# Pure-function unit tests
# ---------------------------------------------------------------------------


def test_localize_picks_requested_locale():
    assert _localize({"en": "Hello", "zh": "你好"}, "zh") == "你好"
    assert _localize({"en": "Hello", "zh": "你好"}, "en") == "Hello"


def test_localize_falls_back_when_locale_missing():
    """When the requested locale isn't present, fall back to ANY non-empty value."""
    assert _localize({"en": "Hello"}, "zh") == "Hello"


def test_localize_returns_string_unchanged():
    assert _localize("plain", "en") == "plain"


def test_compute_rect_px_rounds_to_int():
    px = _compute_rect_px([0.0, 0.0, 0.5, 1.0], 2480.0, 3508.0)
    assert px == [0, 0, 1240, 3508]


def test_image_claim_role_exact_match():
    claim = {"proof_object": {"kind": "image_slot", "ref": "feature_hero"}}
    assert _image_claim_role("feature_hero", claim) == "proof_object"
    assert _image_claim_role("cover_hero", claim) is None


def test_image_claim_role_pattern_match():
    claim = {"proof_object": {"kind": "image_grid", "ref": "feature_captioned.[1-3]"}}
    assert _image_claim_role("feature_captioned.1", claim) == "proof_object"
    assert _image_claim_role("feature_captioned.2", claim) == "proof_object"
    assert _image_claim_role("portrait_wall.1", claim) is None


def test_image_claim_role_no_claim():
    assert _image_claim_role("any", None) is None
    assert _image_claim_role("any", {}) is None


def test_expand_image_grid_3x2():
    region = {
        "rect_norm": [0.0, 0.0, 1.0, 1.0],
        "image_slots": [f"p.{i}" for i in range(1, 7)],
        "grid_cols": 3,
    }
    cells = _expand_image_grid(
        region,
        rect_norm=region["rect_norm"],
        spread_idx=7,
        image_slots_layout=[],
        canvas_w_px=300.0, canvas_h_px=200.0,
        claim_entry=None,
    )
    assert len(cells) == 6
    # Row 0 cells have y0=0; row 1 cells have y0=0.5
    assert cells[0]["rect_norm"] == [0.0, 0.0, 1 / 3, 0.5]
    assert cells[3]["rect_norm"] == [0.0, 0.5, 1 / 3, 1.0]
    # rect_px for cell [0]
    assert cells[0]["rect_px"] == [0, 0, 100, 100]


def test_augment_target_a4_string_to_mm():
    """page_size='A4' (legacy string) augments to the structured form."""
    out = augment_target({"format": "a4-magazine", "page_size": "A4", "bleed_mm": 3}, brand={})
    assert out["page_size"] == {"width": 210, "height": 297, "unit": "mm"}
    assert out["bleed"] == {"value": 3.0, "unit": "mm"}
    assert "bleed_mm" not in out
    assert out["dpi"] == 300


def test_augment_target_pptx_slide_size_to_px():
    """slide_size='720x1080' augments to a px page_size."""
    out = augment_target(
        {"format": "magazine-pptx", "realizer": "presentations", "slide_size": "720x1080"},
        brand={},
    )
    assert out["page_size"] == {"width": 720.0, "height": 1080.0, "unit": "px"}
    assert "slide_size" not in out
    assert out["dpi"] == 96


def test_augment_target_pulls_from_brand_print_specs():
    """When target has no page_size, pull from brand.print_specs."""
    brand = {"print_specs": {"page_size": "A4", "bleed_mm": 5}}
    out = augment_target({"format": "x", "realizer": "weasyprint"}, brand=brand)
    assert out["page_size"] == {"width": 210, "height": 297, "unit": "mm"}
    assert out["bleed"]["value"] == 5.0


def test_compute_design_tokens_typography_chain_from_design_system():
    """design_system.typography_resolution.display.fallback_chain wins over brand."""
    brand = {
        "typography": {"display": {"family": "Playfair Display", "weights": [700]}},
        "visual_tokens": {"color_ink_primary": "#1a1a1a"},
    }
    ds = {
        "typography_resolution": {
            "display": {
                "desired_family": "Playfair Display",
                "fallback_chain": ["Source Serif 4", "Georgia"],
            }
        }
    }
    tokens = compute_design_tokens(brand, ds)
    chain = tokens["typography"]["display"]["family_chain"]
    assert chain[0] == "Playfair Display"
    assert "Source Serif 4" in chain
    assert "Georgia" in chain
    # An ultimate generic fallback gets appended.
    assert chain[-1] in ("serif", "monospace")
    assert tokens["typography"]["display"]["weight"] == 700


def test_compute_design_tokens_color_palette_from_brand_visual_tokens():
    brand = {
        "visual_tokens": {
            "color_bg_paper": "#f5efe6",
            "color_ink_primary": "#1a1a1a",
            "color_accent": "#c2272d",
            "color_ink_secondary": "#6b6b6b",
        }
    }
    tokens = compute_design_tokens(brand, {})
    assert tokens["color_palette"] == {
        "paper": "#F5EFE6",
        "ink": "#1A1A1A",
        "accent": "#C2272D",
        "muted": "#6B6B6B",
    }


def test_text_safe_required_set_when_z_index_positive():
    """A text region with z_index>0 (overlays an image) is marked text_safe_required."""
    manifest = build_from_spec_path(COSMOS_SPEC)
    cover_line = next(r for r in manifest["slides"][0]["regions"] if r["id"] == "cover_line")
    assert cover_line.get("text_safe_required") is True
