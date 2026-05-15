"""Tests for article ↔ layout cross-validation."""
import pathlib

import pytest
import yaml

from tools.validation.article_validate import validate_article

SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture
def valid_article(tmp_path):
    p = tmp_path / "article.yaml"
    p.write_text(yaml.safe_dump({
        "schema_version": 1,
        "slug": "x",
        "display_title": {"en": "X"},
        "issue_label": {"en": "I 01"},
        "cover_line": {"en": "L"},
        "cover_kicker": {"en": "K"},
        "spread_copy": [
            {"idx": 1, "type": "cover"},
            {"idx": 2, "type": "toc", "table_of_contents": []},
            {"idx": 3, "type": "feature-spread", "title": {"en": "T"},
             "kicker": {"en": "K"}, "lead": {"en": "L"}, "body": {"en": "B"}},
            {"idx": 4, "type": "feature-spread", "title": {"en": "T"},
             "kicker": {"en": "K"}, "lead": {"en": "L"}, "body": {"en": "B"}},
            {"idx": 5, "type": "pull-quote", "quote": {"en": "Q"},
             "quote_attribution": {"en": ""}},
            {"idx": 6, "type": "feature-spread", "title": {"en": "T"},
             "kicker": {"en": "K"}, "lead": {"en": "L"}, "body": {"en": "B"}},
            {"idx": 7, "type": "portrait-wall", "title": {"en": "T"},
             "captions": [{"slot": "portrait_wall.1", "en": "C"}] * 6},
            {"idx": 8, "type": "colophon", "credits": {"en": {}}},
            {"idx": 9, "type": "back-cover", "quote": {"en": "Q"},
             "quote_attribution": {"en": ""}},
        ],
    }))
    return p


@pytest.fixture
def layout_editorial_16page(tmp_path):
    p = tmp_path / "layout.yaml"
    p.write_text(yaml.safe_dump({
        "schema_version": 2,
        "name": "editorial-16page",
        "format": {"page_count": 16},
        "spread_plan": [
            {"idx": 1, "type": "cover"},
            {"idx": 2, "type": "toc"},
            {"idx": 3, "type": "feature-spread"},
            {"idx": 4, "type": "feature-spread"},
            {"idx": 5, "type": "pull-quote"},
            {"idx": 6, "type": "feature-spread"},
            {"idx": 7, "type": "portrait-wall"},
            {"idx": 8, "type": "colophon"},
            {"idx": 9, "type": "back-cover"},
        ],
        "text_slots_required": {
            "cover": [], "toc": [], "feature-spread": ["title", "lead", "body"],
            "pull-quote": ["quote"], "portrait-wall": ["title", "captions"],
            "colophon": [], "back-cover": ["quote"],
        },
    }))
    return p


def test_valid_article_passes(valid_article, layout_editorial_16page):
    errors = validate_article(valid_article, layout_editorial_16page)
    assert errors == []


def test_mismatched_spread_count(valid_article, tmp_path):
    bad_layout = tmp_path / "layout.yaml"
    bad_layout.write_text(yaml.safe_dump({
        "schema_version": 2, "name": "x", "format": {"page_count": 4},
        "spread_plan": [{"idx": 1, "type": "cover"}],
        "text_slots_required": {"cover": []},
    }))
    errors = validate_article(valid_article, bad_layout)
    assert any("count mismatch" in e or "spread_plan" in e for e in errors)


def test_missing_required_field(layout_editorial_16page, tmp_path):
    bad_article = tmp_path / "article.yaml"
    bad_article.write_text(yaml.safe_dump({
        "schema_version": 1, "slug": "x",
        "display_title": {"en": "X"},
        "spread_copy": [
            {"idx": 1, "type": "cover"},
            {"idx": 2, "type": "toc"},
            # spread 3 missing 'body'
            {"idx": 3, "type": "feature-spread", "title": {"en": "T"},
             "kicker": {"en": "K"}, "lead": {"en": "L"}},
        ] + [{"idx": i, "type": "x"} for i in range(4, 10)],
    }))
    errors = validate_article(bad_article, layout_editorial_16page)
    assert any("body" in e for e in errors)


def test_type_mismatch(valid_article, layout_editorial_16page, tmp_path):
    """If article spread_copy[i].type doesn't match layout.spread_plan[i].type."""
    a = yaml.safe_load(valid_article.read_text())
    a["spread_copy"][0]["type"] = "wrong-type"
    valid_article.write_text(yaml.safe_dump(a))
    errors = validate_article(valid_article, layout_editorial_16page)
    assert any("type mismatch" in e or "wrong-type" in e for e in errors)


def test_missing_image_slot_override_is_flagged(valid_article, layout_editorial_16page):
    layout = yaml.safe_load(layout_editorial_16page.read_text())
    layout["image_slots"] = [
        {"id": "feature_hero", "spread_idx": 3, "role": "portrait"},
    ]
    layout_editorial_16page.write_text(yaml.safe_dump(layout))

    errors = validate_article(valid_article, layout_editorial_16page)
    assert any("feature_hero" in e for e in errors)


# ---------------------------------------------------------------------------
# claim_spine tests (v0.3.2)
# ---------------------------------------------------------------------------


COSMOS_ARTICLE = SKILL_ROOT / "library" / "articles" / "cosmos-luna-may-2026.yaml"
EDITORIAL_LAYOUT = SKILL_ROOT / "library" / "layouts" / "editorial-16page.yaml"


def _cosmos_article_dict() -> dict:
    return yaml.safe_load(COSMOS_ARTICLE.read_text(encoding="utf-8"))


def _write(tmp_path, article: dict, name: str = "article.yaml") -> pathlib.Path:
    p = tmp_path / name
    p.write_text(yaml.safe_dump(article, sort_keys=False), encoding="utf-8")
    return p


def test_cosmos_luna_article_validates_clean():
    """The real cosmos-luna article with claim_spine must pass."""
    errors = validate_article(COSMOS_ARTICLE, EDITORIAL_LAYOUT)
    assert errors == [], f"unexpected errors: {errors}"


def test_article_without_claim_spine_validates_clean(tmp_path):
    """Backward compat: removing claim_spine entirely must not error."""
    a = _cosmos_article_dict()
    a.pop("claim_spine", None)
    article_path = _write(tmp_path, a)
    errors = validate_article(article_path, EDITORIAL_LAYOUT)
    assert errors == [], f"unexpected errors: {errors}"


def test_claim_spine_idx_missing_from_spread_copy(tmp_path):
    """spread_claims pointing to an idx that does not exist in spread_copy."""
    a = _cosmos_article_dict()
    # Add a bogus extra claim pointing at idx 99.
    a["claim_spine"]["spread_claims"].append({
        "spread_idx": 99,
        "spread_type": "feature-spread",
        "kicker": "BOGUS",
        "claim_title": "This claim points to a spread that does not exist.",
        "proof_object": {"kind": "image_slot", "ref": "feature_hero"},
    })
    article_path = _write(tmp_path, a)
    errors = validate_article(article_path, EDITORIAL_LAYOUT)
    assert any("99" in e and "not found in article.spread_copy" in e
               for e in errors), errors


def test_claim_spine_type_mismatches_spread_copy(tmp_path):
    """spread_claims[i].spread_type must equal matching spread_copy.type."""
    a = _cosmos_article_dict()
    # Claim for idx 3 currently 'feature-spread'; flip to 'pull-quote'.
    for claim in a["claim_spine"]["spread_claims"]:
        if claim.get("spread_idx") == 3:
            claim["spread_type"] = "pull-quote"
            break
    article_path = _write(tmp_path, a)
    errors = validate_article(article_path, EDITORIAL_LAYOUT)
    assert any("idx 3" in e and "does not match" in e for e in errors), errors


def test_claim_spine_proof_ref_not_in_layout_image_slots(tmp_path):
    """proof_object.ref pointing to an image_slot id absent from layout."""
    a = _cosmos_article_dict()
    for claim in a["claim_spine"]["spread_claims"]:
        if claim.get("spread_idx") == 3:
            claim["proof_object"] = {
                "kind": "image_slot",
                "ref": "nonexistent_slot",
            }
            break
    article_path = _write(tmp_path, a)
    errors = validate_article(article_path, EDITORIAL_LAYOUT)
    assert any("nonexistent_slot" in e and "does not match" in e
               for e in errors), errors


def test_claim_spine_proof_ref_pattern_matches_prefix(tmp_path):
    """A pattern ref like 'portrait_wall.[1-6]' must not error when the
    base prefix matches at least one image_slot id-prefix."""
    a = _cosmos_article_dict()
    # Spread 7 already uses portrait_wall.[1-6]; assert it still passes after
    # rewriting it explicitly through this fixture path (defensive).
    for claim in a["claim_spine"]["spread_claims"]:
        if claim.get("spread_idx") == 7:
            claim["proof_object"] = {
                "kind": "image_slot",
                "ref": "portrait_wall.[1-6]",
                "why_carries_claim": "pattern test",
            }
            break
    article_path = _write(tmp_path, a)
    errors = validate_article(article_path, EDITORIAL_LAYOUT)
    # Specifically no claim_spine error on spread 7's proof_object.
    assert not any("portrait_wall.[1-6]" in e for e in errors), errors


def test_claim_spine_proof_ref_on_wrong_spread(tmp_path):
    """proof_object.ref points to an image_slot that exists in the layout
    but on a different spread than this claim. Should produce a clear
    'on spread(s) [M] but this claim is on spread N' error."""
    a = _cosmos_article_dict()
    # spread 7 (portrait-wall) claim — repoint its proof at 'cover_hero',
    # which lives on spread 1 in the editorial-16page layout.
    for claim in a["claim_spine"]["spread_claims"]:
        if claim.get("spread_idx") == 7:
            claim["proof_object"] = {
                "kind": "image_slot",
                "ref": "cover_hero",
            }
            break
    article_path = _write(tmp_path, a)
    errors = validate_article(article_path, EDITORIAL_LAYOUT)
    assert any(
        "cover_hero" in e
        and "spread(s) [1]" in e
        and "claim is on spread 7" in e
        for e in errors
    ), errors


def test_claim_spine_proof_ref_pattern_on_wrong_spread(tmp_path):
    """A pattern ref whose prefix matches slots only on another spread
    must also produce the wrong-spread error, not a not-found error."""
    a = _cosmos_article_dict()
    # spread 3 (feature-spread) claim — repoint at portrait_wall.[1-6]
    # whose prefix 'portrait_wall' lives only on spread 7.
    for claim in a["claim_spine"]["spread_claims"]:
        if claim.get("spread_idx") == 3 and claim.get("proof_object"):
            claim["proof_object"] = {
                "kind": "image_grid",
                "ref": "portrait_wall.[1-6]",
            }
            break
    article_path = _write(tmp_path, a)
    errors = validate_article(article_path, EDITORIAL_LAYOUT)
    assert any(
        "portrait_wall.[1-6]" in e
        and "spread(s) [7]" in e
        and "claim is on spread 3" in e
        for e in errors
    ), errors


def test_spread_copy_idx_without_matching_claim(tmp_path):
    """When claim_spine is present, every spread_copy idx must have a claim."""
    a = _cosmos_article_dict()
    # Drop the claim for spread 7 entirely.
    a["claim_spine"]["spread_claims"] = [
        c for c in a["claim_spine"]["spread_claims"]
        if c.get("spread_idx") != 7
    ]
    article_path = _write(tmp_path, a)
    errors = validate_article(article_path, EDITORIAL_LAYOUT)
    assert any("spread_copy idx 7" in e and "no matching entry" in e
               for e in errors), errors
