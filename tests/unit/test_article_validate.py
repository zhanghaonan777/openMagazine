"""Tests for article ↔ layout cross-validation."""
import pytest
import yaml

from tools.validation.article_validate import validate_article


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
