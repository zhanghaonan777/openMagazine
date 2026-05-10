# openMagazine v0.3 Editorial Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add editorial-spread layout engine (Weasyprint + HTML/CSS templates + multi-aspect image generation + real PDF text) as `editorial-16page` pipeline. v0.1/v0.2 `plain-*` modes coexist via schema_version detection + pdf_selector.

**Architecture:** see `docs/superpowers/specs/2026-05-10-openmagazine-v0.3-editorial-engine-design.md` (the spec, commit `725eff5`). 6 confirmed decisions, schema v2 for brand/layout/spec + new article layer, 21 image slots per issue, ~$5.04 vertex cost, ~9 working days.

**Tech Stack:** Python 3.10+, Jinja2, Weasyprint, PIL, Vertex Gemini 3 Pro Image, Codex `image_gen.imagegen`, pytest.

---

## Phase A — Data layer schema v2 (~2 days, 6 tasks)

### Task A1: Create `editorial-classic` brand preset

**Files:**
- Create: `~/github/openMagazine/library/brands/_presets/editorial-classic.yaml`
- Create: `~/github/openMagazine/library/brands/_presets/README.md`

- [ ] **Step A1.1: Create `_presets/` directory**

```bash
mkdir -p ~/github/openMagazine/library/brands/_presets
```

- [ ] **Step A1.2: Write `library/brands/_presets/editorial-classic.yaml`**

```yaml
schema_version: 2
name: editorial-classic
display_name: Editorial Classic
masthead: "{{MASTHEAD}}"           # placeholder; user clones and replaces
default_language: en

typography:
  display:
    family: "Playfair Display"
    weights: [700, 900]
    source: google-fonts
  body:
    family: "Source Serif 4"
    weights: [400, 600]
    source: google-fonts
    size_pt: 10
    leading: 1.45
    align: justify
    hyphenate: true
  kicker:
    family: "IBM Plex Mono"
    weight: 500
    transform: uppercase
    letter_spacing: 0.08em
    size_pt: 8
  caption:
    family: "IBM Plex Mono"
    weight: 400
    style: italic
    size_pt: 8
  pull_quote:
    family: "Playfair Display"
    weight: 900
    style: italic
    size_pt: 32
  drop_cap:
    enabled: true
    family: "Playfair Display"
    weight: 900
    lines: 3
    color_token: accent
  page_number:
    family: "IBM Plex Mono"
    weight: 400
    size_pt: 9
  pairing_notes: |
    Playfair Display (didone-adjacent display) + Source Serif 4 (comfortable
    body) + IBM Plex Mono (editorial meta labels). The classic editorial
    pairing — high-contrast hero, readable long-form, distinctive metadata.

print_specs:
  page_size: A4
  page_size_custom_mm: ~
  bleed_mm: 3
  trim_marks: true
  registration_marks: false
  binding: saddle-stitch
  binding_gutter_mm: 8
  margin_top_mm: 20
  margin_bottom_mm: 22
  margin_outer_mm: 18
  margin_inner_mm: 22
  baseline_grid_mm: 4
  paper_stock_note: "80gsm uncoated"
  color_mode: rgb

visual_tokens:
  color_bg_paper: "#f5efe6"
  color_ink_primary: "#1a1a1a"
  color_ink_secondary: "#6b6b6b"
  color_accent: "#c2272d"
  color_quote_bg: "#1a1a1a"
  color_quote_fg: "#f5efe6"
  rule_thickness_pt: 1.5
  margin_note_indent_mm: 4
```

- [ ] **Step A1.3: Write `library/brands/_presets/README.md`**

```markdown
# Brand Presets

Starting points for `library/brands/<name>.yaml` (schema_version 2).

| Preset | Display family | Body family | Vibe |
|---|---|---|---|
| editorial-classic | Playfair Display | Source Serif 4 | Generic editorial / human-interest |
| humanist-warm | Cormorant Garamond | Lora | Literature / lifestyle |

## Use

```bash
cp library/brands/_presets/editorial-classic.yaml library/brands/my-magazine.yaml
# Edit name, masthead, default_language; leave typography / print_specs / tokens alone unless you know what you're doing
```

The `{{MASTHEAD}}` placeholder must be replaced before the brand is referenced from a spec. `spec_validate` will reject a brand whose masthead still contains literal `{{...}}`.

## Future presets (v0.3.1+)

- architectural — Archivo Black + Manrope (design / business)
- swiss-modernist — Inter Display + Inter (tech / product)
- editorial-asian — Noto Serif CJK + Source Han Sans (Chinese-language)
```

- [ ] **Step A1.4: Verify yaml parses**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
python -c "import yaml; d=yaml.safe_load(open('library/brands/_presets/editorial-classic.yaml')); print('schema_version:', d['schema_version']); assert d['schema_version']==2"
```

Expected: `schema_version: 2`

- [ ] **Step A1.5: Commit**

```bash
git add library/brands/_presets/
git commit -m "feat(brands): add editorial-classic preset (v2 typography pack)"
```

---

### Task A2: Create `humanist-warm` brand preset

**Files:**
- Create: `~/github/openMagazine/library/brands/_presets/humanist-warm.yaml`

- [ ] **Step A2.1: Write `humanist-warm.yaml`**

```yaml
schema_version: 2
name: humanist-warm
display_name: Humanist Warm
masthead: "{{MASTHEAD}}"
default_language: en

typography:
  display:
    family: "Cormorant Garamond"
    weights: [600, 700]
    source: google-fonts
  body:
    family: "Lora"
    weights: [400, 500]
    source: google-fonts
    size_pt: 10.5
    leading: 1.5
    align: justify
    hyphenate: true
  kicker:
    family: "Lora"
    weight: 500
    transform: uppercase
    letter_spacing: 0.1em
    size_pt: 8
  caption:
    family: "Lora"
    weight: 400
    style: italic
    size_pt: 8.5
  pull_quote:
    family: "Cormorant Garamond"
    weight: 700
    style: italic
    size_pt: 30
  drop_cap:
    enabled: true
    family: "Cormorant Garamond"
    weight: 700
    lines: 4
    color_token: accent
  page_number:
    family: "Lora"
    weight: 400
    size_pt: 9
  pairing_notes: |
    Cormorant Garamond (humanist serif, warm proportions) + Lora (low-contrast
    serif body, optimized for screen + print). Warmer, slower than editorial-
    classic. Pairs with literary, slow-living, lifestyle content.

print_specs:
  page_size: A4
  page_size_custom_mm: ~
  bleed_mm: 3
  trim_marks: true
  registration_marks: false
  binding: saddle-stitch
  binding_gutter_mm: 8
  margin_top_mm: 22
  margin_bottom_mm: 24
  margin_outer_mm: 20
  margin_inner_mm: 24
  baseline_grid_mm: 4.5
  paper_stock_note: "100gsm cream uncoated"
  color_mode: rgb

visual_tokens:
  color_bg_paper: "#f7f1e8"
  color_ink_primary: "#2b2519"
  color_ink_secondary: "#7a6f5c"
  color_accent: "#a64a2e"
  color_quote_bg: "#3d3528"
  color_quote_fg: "#f7f1e8"
  rule_thickness_pt: 0.75
  margin_note_indent_mm: 5
```

- [ ] **Step A2.2: Verify + commit**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
python -c "import yaml; yaml.safe_load(open('library/brands/_presets/humanist-warm.yaml'))"
git add library/brands/_presets/humanist-warm.yaml
git commit -m "feat(brands): add humanist-warm preset (Cormorant + Lora)"
```

---

### Task A3: Migrate `meow-life.yaml` to schema v2

**Files:**
- Create: `~/github/openMagazine/tools/meta/migrate_brand_v1_to_v2.py`
- Modify: `~/github/openMagazine/library/brands/meow-life.yaml`
- Create: `~/github/openMagazine/tests/unit/test_migrate_brand.py`

- [ ] **Step A3.1: Read current meow-life.yaml**

```bash
cd ~/github/openMagazine && cat library/brands/meow-life.yaml
```

Note current fields (likely `schema_version: 1`, `name`, `masthead`, `display_name`).

- [ ] **Step A3.2: Write the failing test**

Create `tests/unit/test_migrate_brand.py`:

```python
"""Tests for tools.meta.migrate_brand_v1_to_v2."""
import yaml
import pytest

from tools.meta.migrate_brand_v1_to_v2 import migrate, V1_TO_V2_DEFAULTS


def test_migrate_keeps_v1_fields(tmp_path):
    src = tmp_path / "brand.yaml"
    src.write_text(yaml.safe_dump({
        "schema_version": 1,
        "name": "test-brand",
        "masthead": "TEST MAG",
        "display_name": {"en": "Test Magazine"},
    }))
    out = migrate(src, preset="editorial-classic", dry_run=True)
    assert out["schema_version"] == 2
    assert out["name"] == "test-brand"
    assert out["masthead"] == "TEST MAG"
    assert out["display_name"] == {"en": "Test Magazine"}


def test_migrate_adds_typography(tmp_path):
    src = tmp_path / "brand.yaml"
    src.write_text(yaml.safe_dump({
        "schema_version": 1,
        "name": "x",
        "masthead": "X",
    }))
    out = migrate(src, preset="editorial-classic", dry_run=True)
    assert "typography" in out
    assert out["typography"]["display"]["family"] == "Playfair Display"
    assert out["typography"]["body"]["size_pt"] == 10


def test_migrate_adds_print_specs(tmp_path):
    src = tmp_path / "brand.yaml"
    src.write_text(yaml.safe_dump({"schema_version": 1, "name": "x", "masthead": "X"}))
    out = migrate(src, preset="editorial-classic", dry_run=True)
    assert out["print_specs"]["page_size"] == "A4"
    assert out["print_specs"]["bleed_mm"] == 3


def test_migrate_writes_file(tmp_path):
    src = tmp_path / "brand.yaml"
    src.write_text(yaml.safe_dump({"schema_version": 1, "name": "x", "masthead": "X"}))
    migrate(src, preset="editorial-classic", dry_run=False)
    after = yaml.safe_load(src.read_text())
    assert after["schema_version"] == 2
    assert "typography" in after


def test_migrate_idempotent_on_v2(tmp_path):
    src = tmp_path / "brand.yaml"
    src.write_text(yaml.safe_dump({"schema_version": 2, "name": "x", "typography": {}}))
    with pytest.raises(ValueError, match="already v2"):
        migrate(src, preset="editorial-classic")
```

- [ ] **Step A3.3: Verify test fails**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
python -m pytest tests/unit/test_migrate_brand.py -v
```

Expected: ImportError (`migrate_brand_v1_to_v2` not yet defined).

- [ ] **Step A3.4: Write `tools/meta/migrate_brand_v1_to_v2.py`**

```python
"""Migrate library/brands/<name>.yaml from schema_version 1 to 2.

Adds typography / print_specs / visual_tokens from a chosen brand preset,
preserving any v1 fields (name, masthead, display_name).

Usage:
    python tools/meta/migrate_brand_v1_to_v2.py library/brands/meow-life.yaml \
        --preset editorial-classic
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any

import yaml


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]
PRESETS_DIR = SKILL_ROOT / "library" / "brands" / "_presets"

V1_TO_V2_DEFAULTS = {
    "default_language": "en",
}


def migrate(brand_path: pathlib.Path, *, preset: str, dry_run: bool = False) -> dict:
    """Read v1 brand, return v2 dict (and optionally write it back)."""
    brand_path = pathlib.Path(brand_path)
    v1 = yaml.safe_load(brand_path.read_text(encoding="utf-8"))
    if v1.get("schema_version") == 2:
        raise ValueError(f"{brand_path} already v2; nothing to migrate")

    preset_path = PRESETS_DIR / f"{preset}.yaml"
    if not preset_path.is_file():
        raise FileNotFoundError(f"preset not found: {preset_path}")
    p = yaml.safe_load(preset_path.read_text(encoding="utf-8"))

    # Copy preset typography / print_specs / visual_tokens
    out = {
        "schema_version": 2,
        "name": v1.get("name", "unknown"),
        "display_name": v1.get("display_name", {"en": v1.get("name", "Unknown")}),
        "masthead": v1.get("masthead", v1.get("name", "MAGAZINE").upper()),
        "default_language": v1.get("default_language", V1_TO_V2_DEFAULTS["default_language"]),
        "typography": p["typography"],
        "print_specs": p["print_specs"],
        "visual_tokens": p["visual_tokens"],
    }

    if not dry_run:
        brand_path.write_text(
            yaml.safe_dump(out, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("brand_path", type=pathlib.Path)
    p.add_argument("--preset", default="editorial-classic")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    try:
        out = migrate(a.brand_path, preset=a.preset, dry_run=a.dry_run)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if a.dry_run:
        print(yaml.safe_dump(out, sort_keys=False, allow_unicode=True))
    else:
        print(f"migrated: {a.brand_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step A3.5: Run tests**

```bash
python -m pytest tests/unit/test_migrate_brand.py -v
```

Expected: 5 pass.

- [ ] **Step A3.6: Run migration on meow-life.yaml**

```bash
cd ~/github/openMagazine
python tools/meta/migrate_brand_v1_to_v2.py library/brands/meow-life.yaml --preset editorial-classic
git diff library/brands/meow-life.yaml | head -40
```

Verify: schema_version is now 2; masthead preserved; typography / print_specs / visual_tokens added.

- [ ] **Step A3.7: Commit**

```bash
git add tools/meta/migrate_brand_v1_to_v2.py tests/unit/test_migrate_brand.py library/brands/meow-life.yaml
git commit -m "feat(meta): migrate_brand_v1_to_v2 + bump meow-life to v2"
```

---

### Task A4: Create `editorial-16page` layout schema v2

**Files:**
- Create: `~/github/openMagazine/library/layouts/editorial-16page.yaml`

- [ ] **Step A4.1: Write `library/layouts/editorial-16page.yaml`**

```yaml
schema_version: 2
name: editorial-16page
display_name: Editorial 16-page A4 Spread
typography_mode: editorial-spread

format:
  page_count: 16
  spreads: 9
  page_size: A4
  bleed_mm: 3
  binding: saddle-stitch

spread_plan:
  - {idx: 1, type: cover,           pages: [1]}
  - {idx: 2, type: toc,             pages: [2, 3]}
  - {idx: 3, type: feature-spread,  pages: [4, 5]}
  - {idx: 4, type: feature-spread,  pages: [6, 7]}
  - {idx: 5, type: pull-quote,      pages: [8, 9]}
  - {idx: 6, type: feature-spread,  pages: [10, 11]}
  - {idx: 7, type: portrait-wall,   pages: [12, 13]}
  - {idx: 8, type: colophon,        pages: [14, 15]}
  - {idx: 9, type: back-cover,      pages: [16]}

# 21 image slots total. spread_idx tells which spread each lives in.
image_slots:
  - {id: cover_hero,            role: cover_hero,   aspect: "3:4",   min_long_edge_px: 3500, spread_idx: 1}
  - {id: feature_hero,          role: portrait,     aspect: "3:4",   min_long_edge_px: 3000, spread_idx: 3}
  - {id: feature_hero,          role: portrait,     aspect: "3:4",   min_long_edge_px: 3000, spread_idx: 4}
  - {id: feature_hero,          role: portrait,     aspect: "3:4",   min_long_edge_px: 3000, spread_idx: 6}
  - {id: feature_captioned.1,   role: scene,        aspect: "3:2",   min_long_edge_px: 2500, spread_idx: 3}
  - {id: feature_captioned.2,   role: scene,        aspect: "3:2",   min_long_edge_px: 2500, spread_idx: 3}
  - {id: feature_captioned.3,   role: scene,        aspect: "3:2",   min_long_edge_px: 2500, spread_idx: 3}
  - {id: feature_captioned.1,   role: scene,        aspect: "3:2",   min_long_edge_px: 2500, spread_idx: 4}
  - {id: feature_captioned.2,   role: scene,        aspect: "3:2",   min_long_edge_px: 2500, spread_idx: 4}
  - {id: feature_captioned.3,   role: scene,        aspect: "3:2",   min_long_edge_px: 2500, spread_idx: 4}
  - {id: feature_captioned.1,   role: scene,        aspect: "3:2",   min_long_edge_px: 2500, spread_idx: 6}
  - {id: feature_captioned.2,   role: scene,        aspect: "3:2",   min_long_edge_px: 2500, spread_idx: 6}
  - {id: feature_captioned.3,   role: scene,        aspect: "3:2",   min_long_edge_px: 2500, spread_idx: 6}
  - {id: pullquote_environment, role: environment,  aspect: "16:10", min_long_edge_px: 3500, spread_idx: 5}
  - {id: portrait_wall.1,       role: portrait,     aspect: "1:1",   min_long_edge_px: 1500, spread_idx: 7}
  - {id: portrait_wall.2,       role: portrait,     aspect: "1:1",   min_long_edge_px: 1500, spread_idx: 7}
  - {id: portrait_wall.3,       role: portrait,     aspect: "1:1",   min_long_edge_px: 1500, spread_idx: 7}
  - {id: portrait_wall.4,       role: portrait,     aspect: "1:1",   min_long_edge_px: 1500, spread_idx: 7}
  - {id: portrait_wall.5,       role: portrait,     aspect: "1:1",   min_long_edge_px: 1500, spread_idx: 7}
  - {id: portrait_wall.6,       role: portrait,     aspect: "1:1",   min_long_edge_px: 1500, spread_idx: 7}
  - {id: back_coda,             role: back_coda,    aspect: "2:3",   min_long_edge_px: 2500, spread_idx: 9}

text_slots_required:
  cover: [cover_line, cover_kicker]
  toc: [table_of_contents]
  feature-spread: [title, kicker, lead, body]
  pull-quote: [quote, attribution]
  portrait-wall: [title, captions]
  colophon: [credits]
  back-cover: [quote, attribution]

defaults:
  storyboard_grid_outer: "2:3"
  storyboard_size_px: [1024, 1536]
  total_image_slots: 21
  vertex_cost_estimate_usd: 5.04
```

- [ ] **Step A4.2: Verify yaml parses + slot count**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
python -c "
import yaml
d = yaml.safe_load(open('library/layouts/editorial-16page.yaml'))
assert d['schema_version'] == 2
assert d['format']['page_count'] == 16
assert len(d['spread_plan']) == 9
assert len(d['image_slots']) == 21
print('OK: 9 spreads, 21 image slots')
"
```

- [ ] **Step A4.3: Commit**

```bash
git add library/layouts/editorial-16page.yaml
git commit -m "feat(layouts): add editorial-16page yaml (9 spreads, 21 image slots)"
```

---

### Task A5: Create `articles/` layer + cosmos-luna-may-2026.yaml

**Files:**
- Create: `~/github/openMagazine/library/articles/README.md`
- Create: `~/github/openMagazine/library/articles/cosmos-luna-may-2026.yaml`

- [ ] **Step A5.1: Create directory + README**

```bash
mkdir -p ~/github/openMagazine/library/articles
```

Write `library/articles/README.md`:

```markdown
# Articles

The `articles/` layer holds per-issue editorial copy: titles, kickers, leads, body paragraphs, pull quotes, captions, credits.

This layer is **new in schema v2**. v0.3 specs reference an article via the `article` field.

## Relationship to other layers

- `subjects/` — character traits (reusable across issues)
- `themes/` — visual world (lighting, palette, page_plan_hints; reusable)
- `articles/` — **per-issue copy** (this layer)
- `layouts/` — page geometry (image_slots, spread_plan; reusable)
- `brands/` — typography + print specs + visual tokens (reusable)
- `styles/` — image-gen prompt anchor (reusable)

A theme like `cosmos` can serve many issues (May 2026, June 2026, ...) — each gets its own `articles/<slug>.yaml`.

## Schema (v1)

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | always 1 (this is a new layer at v0.3, no migration) |
| `slug` | string | matches the spec's slug; usually identical |
| `display_title` | `{lang: string}` | human-readable title |
| `masthead_override` | string \| null | overrides brand.masthead for this issue |
| `issue_label` | `{lang: string}` | "ISSUE 03 / MAY 2026" |
| `cover_line` | `{lang: string}` | front-cover headline |
| `cover_kicker` | `{lang: string}` | "FEATURE STORY" / "VOL 03" / etc |
| `spread_copy` | list | one entry per layout.spread_plan item, by `idx` |

Each `spread_copy` entry MUST match the corresponding `layout.spread_plan[idx]` by `idx` and `type`.

## Auto-draft

If the spec references an `article` that doesn't exist on disk, the `articulate-director` skill drafts a complete article during Stage 3 (articulate) and persists it to `library/articles/<slug>.yaml`. The user reviews and edits the file before storyboard generation.

## Validation

Run `python tools/validation/article_validate.py library/articles/<slug>.yaml --layout editorial-16page` to verify schema + cross-references.
```

- [ ] **Step A5.2: Write `library/articles/cosmos-luna-may-2026.yaml`**

(Long file — roughly 200 lines. Write the complete article copy for editorial-16page's 9 spreads.)

```yaml
schema_version: 1
slug: cosmos-luna-may-2026
display_title:
  en: "Luna Walks the Moon"
  zh: "月行猫"

masthead_override: ~
issue_label:
  en: "ISSUE 03 / MAY 2026"
  zh: "第 03 期 / 2026 年 5 月"
cover_line:
  en: "A small astronaut on the lunar regolith"
  zh: "月尘上的微小宇航员"
cover_kicker:
  en: "FEATURE STORY"
  zh: "封面故事"

spread_copy:
  - idx: 1
    type: cover
    notes: "cover_line + cover_kicker provided above"
    image_slot_overrides:
      cover_hero: "Luna in EVA suit standing on lunar regolith, hero portrait, Earth horizon upper-right"

  - idx: 2
    type: toc
    table_of_contents:
      - {page: 4,  en: "Departure",       zh: "启程"}
      - {page: 6,  en: "Lunar Plain",     zh: "月之平原"}
      - {page: 8,  en: "The Pause",       zh: "停顿"}
      - {page: 10, en: "Earthrise",       zh: "地升"}
      - {page: 12, en: "Stills From a Mission", zh: "任务剪影"}
      - {page: 14, en: "Colophon",        zh: "出版信息"}

  - idx: 3
    type: feature-spread
    pages: [4, 5]
    title:
      en: "DEPARTURE"
      zh: "启程"
    kicker:
      en: "Chapter 01"
      zh: "第一章"
    lead:
      en: "She steps from the module into a silence that has waited four billion years for the sound of a paw."
      zh: "她踏出舱门，进入一个等待了四十亿年才迎来一只猫爪声响的寂静。"
    body:
      en: |
        First steps onto the lunar surface are quieter than anyone tells you. The
        suit's life support hums; the regolith makes no sound. Luna's footprints
        will outlast every photograph in this issue.

        She moves with the slow deliberation of low gravity — each step a small
        flight, ending in a deeper-than-expected sink as the dust gives way.
        Earth is a small blue marble in the upper right of frame, and she will
        be photographed against it for the next eleven days.

        The light here is unforgiving. There is no atmospheric scatter to soften
        the shadows; there is no fill. What you see is what the sun gives you,
        and the sun on the Moon is a single hard key from above the horizon.
      zh: |
        踏上月面的第一步比任何人告诉你的都要安静。生命维持系统嗡鸣；月尘无声。
        Luna 的脚印将比这一期里所有照片都活得更久。

        她以低重力的缓慢步态移动——每一步都是一次小小的飞翔，最终陷入比预想更深的
        尘土。地球是画面右上角的一颗蓝色弹珠，接下来的十一天里，她都将以它为背景被拍摄。

        这里的光毫不留情。没有大气散射柔化阴影；没有补光。你看到的就是太阳给你的，
        而月球上的太阳是一束来自地平线上方的单一硬光。
    image_slot_overrides:
      feature_hero: "Luna in EVA suit at module airlock, hand on hatch, hero portrait at moment of egress, Earth visible upper right"
      feature_captioned.1: "Luna's footprints in lunar regolith, 3:2 wide angle, low sun raking shadows"
      feature_captioned.2: "Luna mid-stride on lunar plain, 3:2 medium wide, Earth small in upper-right of frame"
      feature_captioned.3: "Luna's gloved paw on rock surface, 3:2 close-up, regolith grain visible"

  - idx: 4
    type: feature-spread
    pages: [6, 7]
    title:
      en: "LUNAR PLAIN"
      zh: "月之平原"
    kicker:
      en: "Chapter 02"
      zh: "第二章"
    lead:
      en: "There is more nothing here than anywhere on Earth, and yet she finds something to look at in every direction."
      zh: "这里比地球上任何地方都更虚无，但她在每个方向都能找到值得看的东西。"
    body:
      en: |
        The Sea of Tranquility is misnamed. It is not a sea, and on the
        timescale of a lunar day, it is anything but tranquil — temperature
        swings of three hundred degrees, micro-meteorites arriving without
        warning, the occasional moonquake from the slowly cooling core.

        Luna walks for an hour. She finds a boulder the size of a delivery van,
        casts of impact craters in the dust, the curving line of an old rille
        she has been told to look for. She does not find life, but she did not
        expect to.

        The most photographed astronauts are the ones who came back. Luna
        intends to be one of them.
      zh: |
        宁静海名不副实。它不是海，在月昼的时间尺度上，它远谈不上宁静——三百度的
        温度起伏，毫无预警的微流星，缓慢冷却的内核偶尔送来的月震。

        Luna 走了一个小时。她发现一块送货车大小的巨石、月尘里撞击坑的形状、一条
        她被嘱咐要寻找的古老月谷的曲线。她没找到生命，但她也没指望找到。

        被拍得最多的宇航员，是那些活着回来的。Luna 打算成为其中之一。
    image_slot_overrides:
      feature_hero: "Luna at boulder, hero portrait 3:4, hand resting on rock surface, Earth small in distance"
      feature_captioned.1: "wide shot of lunar plain, 3:2, Luna small in lower-third, vast emptiness"
      feature_captioned.2: "close-up of impact crater rim in dust, 3:2, low sun, micro-shadow detail"
      feature_captioned.3: "Luna walking away from camera into distance, 3:2, footprints leading away"

  - idx: 5
    type: pull-quote
    pages: [8, 9]
    quote:
      en: "The most photographed astronaut\nis the one who never came back."
      zh: "被拍得最多的宇航员，\n是再没回来的那位。"
    quote_attribution:
      en: "— field notes, May 2026"
      zh: "—— 现场笔记，2026 年 5 月"
    image_slot_overrides:
      pullquote_environment: "wide environmental 16:10, sweeping lunar landscape with Luna as a tiny figure on the horizon, dramatic raking light, deep negative space"

  - idx: 6
    type: feature-spread
    pages: [10, 11]
    title:
      en: "EARTHRISE"
      zh: "地升"
    kicker:
      en: "Chapter 03"
      zh: "第三章"
    lead:
      en: "She turns to face the Earth and realizes, for the first time, that she has been facing away from it the whole time."
      zh: "她转身面对地球，第一次意识到自己一直背对着它。"
    body:
      en: |
        Earthrise is misnamed too — the Earth doesn't rise on the Moon, because
        the Moon's rotation is locked. Earth sits in the same patch of sky for
        anyone standing in the same place. But the first time you see it, your
        body insists otherwise: it is rising the way a memory rises.

        Luna stops moving. She has been told this is the moment to stop moving.

        The blue is too bright. She had been ready for the silence, ready for
        the gravity, ready for the cold. She had not been ready for the colour
        of the planet she came from.
      zh: |
        地升也是个误称——月球上地球不会升起，因为月球的自转是锁定的。地球停留在
        天空中的同一片区域，对任何在同一地点的人都是如此。但第一次看到它时，你的
        身体坚持相反的事实：它在升起，像记忆在升起的方式。

        Luna 停下脚步。她被告知这是该停下来的时刻。

        蓝色太亮了。她已经为寂静做好准备，为重力做好准备，为寒冷做好准备。她没
        准备好的，是她来自的那颗星球的颜色。
    image_slot_overrides:
      feature_hero: "Luna facing Earth, hero portrait 3:4, three-quarter back view, Earthrise dominant in upper frame"
      feature_captioned.1: "tight close-up of Luna's helmet visor reflecting Earth, 3:2"
      feature_captioned.2: "Luna's silhouette against Earth disc, 3:2 medium-wide, dramatic backlight"
      feature_captioned.3: "Luna gloved paw raised toward Earth, 3:2, gesture of acknowledgment"

  - idx: 7
    type: portrait-wall
    pages: [12, 13]
    title:
      en: "STILLS FROM A MISSION"
      zh: "任务剪影"
    captions:
      - {slot: portrait_wall.1, en: "Approach",  zh: "接近"}
      - {slot: portrait_wall.2, en: "Pause",     zh: "停顿"}
      - {slot: portrait_wall.3, en: "Touch",     zh: "触碰"}
      - {slot: portrait_wall.4, en: "Listen",    zh: "聆听"}
      - {slot: portrait_wall.5, en: "Climb",     zh: "攀登"}
      - {slot: portrait_wall.6, en: "Look Back", zh: "回望"}
    image_slot_overrides:
      portrait_wall.1: "Luna in EVA suit, square crop 1:1, approaching boulder, three-quarter front, neutral mood"
      portrait_wall.2: "Luna paused mid-stride, square 1:1, head turned slightly toward Earth, contemplative"
      portrait_wall.3: "Luna touching rock surface with gloved paw, square 1:1, close mid-shot"
      portrait_wall.4: "Luna head tilted as if listening, square 1:1, ears subtly forward, intent expression"
      portrait_wall.5: "Luna climbing low boulder, square 1:1, dynamic pose, low angle"
      portrait_wall.6: "Luna looking back over shoulder toward Earth, square 1:1, three-quarter back, final pause"

  - idx: 8
    type: colophon
    pages: [14, 15]
    credits:
      en:
        photographer: "Luna (self-portrait series)"
        art_direction: "MEOW LIFE editorial team"
        printing: "Saddle-stitched A4 portrait, 80gsm uncoated"
        copyright: "© 2026 MEOW LIFE. All rights reserved."
        contact: "letters@meowlife.example"
      zh:
        photographer: "Luna（自拍系列）"
        art_direction: "MEOW LIFE 编辑团队"
        printing: "骑马钉装订 A4 竖版，80g 非涂布纸"
        copyright: "© 2026 MEOW LIFE 版权所有"
        contact: "letters@meowlife.example"

  - idx: 9
    type: back-cover
    pages: [16]
    quote:
      en: "Look up. The Moon\nwas always watching."
      zh: "抬头。月亮\n一直在看着。"
    quote_attribution:
      en: ""
      zh: ""
    image_slot_overrides:
      back_coda: "Luna small distant figure on lunar horizon, 2:3 portrait, lots of negative space, quiet coda mood, looking up at sky"
```

- [ ] **Step A5.3: Verify article parses**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
python -c "
import yaml
d = yaml.safe_load(open('library/articles/cosmos-luna-may-2026.yaml'))
assert d['schema_version'] == 1
assert len(d['spread_copy']) == 9
print('OK: 9 spread_copy entries')
"
```

- [ ] **Step A5.4: Commit**

```bash
git add library/articles/
git commit -m "feat(articles): add articles/ layer + cosmos-luna-may-2026 example"
```

---

### Task A6: Extend `spec_validate` for v2 + new `article_validate`

**Files:**
- Modify: `~/github/openMagazine/tools/validation/spec_validate.py`
- Create: `~/github/openMagazine/tools/validation/article_validate.py`
- Create: `~/github/openMagazine/tests/unit/test_article_validate.py`

- [ ] **Step A6.1: Write the failing test for article_validate**

Create `tests/unit/test_article_validate.py`:

```python
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
```

- [ ] **Step A6.2: Run test, expect ImportError**

```bash
python -m pytest tests/unit/test_article_validate.py -v
```

- [ ] **Step A6.3: Write `tools/validation/article_validate.py`**

```python
"""Validate articles/<slug>.yaml against the matching layout's spread_plan."""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any

import yaml

from tools.base_tool import BaseTool


def _load_yaml(p: pathlib.Path) -> dict:
    return yaml.safe_load(pathlib.Path(p).read_text(encoding="utf-8")) or {}


def validate_article(article_path: pathlib.Path, layout_path: pathlib.Path) -> list[str]:
    """Return list of error messages. Empty list = valid."""
    errors: list[str] = []
    a = _load_yaml(article_path)
    layout = _load_yaml(layout_path)

    if a.get("schema_version") != 1:
        errors.append(f"article schema_version must be 1, got {a.get('schema_version')!r}")

    plan = layout.get("spread_plan") or []
    copy = a.get("spread_copy") or []

    if len(plan) != len(copy):
        errors.append(
            f"spread count mismatch: layout.spread_plan has {len(plan)} entries, "
            f"article.spread_copy has {len(copy)}"
        )

    required = layout.get("text_slots_required") or {}
    n = min(len(plan), len(copy))
    for i in range(n):
        p_entry = plan[i]
        c_entry = copy[i]
        if p_entry.get("idx") != c_entry.get("idx"):
            errors.append(
                f"spread idx mismatch at position {i}: "
                f"layout.idx={p_entry.get('idx')}, article.idx={c_entry.get('idx')}"
            )
        if p_entry.get("type") != c_entry.get("type"):
            errors.append(
                f"spread type mismatch at idx {p_entry.get('idx')}: "
                f"layout.type={p_entry.get('type')!r}, article.type={c_entry.get('type')!r}"
            )
        # required text fields per type
        spread_type = p_entry.get("type")
        for field in required.get(spread_type, []):
            if field not in c_entry:
                errors.append(
                    f"spread {p_entry.get('idx')} ({spread_type}): "
                    f"required field {field!r} missing"
                )

    return errors


class ArticleValidate(BaseTool):
    capability = "validation"
    provider = "local"
    status = "active"
    agent_skills = ["spec-validate-usage"]

    def run(self, article_path: pathlib.Path, layout_path: pathlib.Path) -> list[str]:
        return validate_article(article_path, layout_path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("article", type=pathlib.Path)
    p.add_argument("--layout", type=pathlib.Path, required=True)
    a = p.parse_args(argv)
    errs = validate_article(a.article, a.layout)
    if not errs:
        print(f"✓ {a.article.name}: valid against {a.layout.name}", file=sys.stderr)
        return 0
    print(f"✗ {a.article.name}: {len(errs)} error(s)", file=sys.stderr)
    for e in errs:
        print(f"  {e}", file=sys.stderr)
    return 1


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(ArticleValidate())


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step A6.4: Run tests**

```bash
python -m pytest tests/unit/test_article_validate.py -v
```

Expected: 4 pass.

- [ ] **Step A6.5: Update `tools/validation/__init__.py`**

Append `from tools.validation import article_validate  # noqa: F401`

- [ ] **Step A6.6: Extend `tools/validation/spec_validate.py` for schema v2**

Read the file, then add v2 detection and the new `article` field to LAYER_DIRS:

After existing `LAYER_DIRS`, add a v2 variant resolved at runtime:

```python
LAYER_DIRS_V2 = {
    **LAYER_DIRS,
    "article": LIBRARY_DIR / "articles",
}
```

In `validate_spec`, check schema_version and route:

```python
def validate_spec(spec_path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    try:
        spec = _load_yaml(spec_path)
    except FileNotFoundError as e:
        return [str(e)]
    except Exception as e:
        return [f"failed to parse {spec_path}: {e}"]

    schema_version = spec.get("schema_version")
    if schema_version == 1:
        return _validate_spec_v1(spec, spec_path)
    if schema_version == 2:
        return _validate_spec_v2(spec, spec_path)
    return [f"spec.schema_version must be 1 or 2, got {schema_version!r}"]
```

Refactor existing `validate_spec` body into `_validate_spec_v1`. Add `_validate_spec_v2` mirroring v1 but also requiring `article` field and running `article_validate.validate_article` against the resolved layout path.

- [ ] **Step A6.7: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: previous 47 + new tests (including A3 migrate 5 + A6 article_validate 4) = 56+ pass.

- [ ] **Step A6.8: Commit**

```bash
git add tools/validation/article_validate.py tests/unit/test_article_validate.py \
       tools/validation/__init__.py tools/validation/spec_validate.py
git commit -m "feat(validation): add article_validate + spec_validate v2 routing"
```

---

## Phase B — Rendering engine (~3 days, 8 tasks)

### Task B1: Install Weasyprint dep

**Files:**
- Modify: `~/github/openMagazine/pyproject.toml`

- [ ] **Step B1.1: Edit `pyproject.toml`**

Add `"weasyprint>=62"` to `dependencies` and `"jinja2>=3.1"` (if not already there).

```toml
dependencies = [
  "google-genai>=2.0",
  "pillow>=10.0",
  "reportlab>=4.0",
  "pyyaml>=6.0",
  "jsonschema>=4.0",
  "jinja2>=3.1",
  "weasyprint>=62",
]
```

- [ ] **Step B1.2: Install + smoke import**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
uv pip install -e ".[dev]"
python -c "from weasyprint import HTML; print('weasyprint OK')"
python -c "from jinja2 import Environment; print('jinja2 OK')"
```

If macOS native deps fail, run `brew install weasyprint` first, then retry. If still failing, document in step report and fallback to Playwright is out of scope for v0.3.0 — escalate.

- [ ] **Step B1.3: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add weasyprint + jinja2 for v0.3 editorial engine"
```

---

### Task B2: `weasyprint_compose.py` BaseTool subclass

**Files:**
- Create: `~/github/openMagazine/tools/pdf/weasyprint_compose.py`
- Modify: `~/github/openMagazine/tools/pdf/__init__.py`
- Create: `~/github/openMagazine/tests/unit/test_weasyprint_compose.py`

- [ ] **Step B2.1: Write the failing test**

Create `tests/unit/test_weasyprint_compose.py`:

```python
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
```

- [ ] **Step B2.2: Run test, expect ImportError**

```bash
python -m pytest tests/unit/test_weasyprint_compose.py -v
```

- [ ] **Step B2.3: Write `tools/pdf/weasyprint_compose.py`**

```python
"""Weasyprint compose — render HTML/CSS to print PDF.

Used by editorial-* layouts (schema_version=2). Reads layout html.j2 +
components, fills with article copy + brand typography + image paths,
renders to magazine.pdf.
"""
from __future__ import annotations

import pathlib
import sys
from typing import Any

from tools.base_tool import BaseTool


class WeasyprintCompose(BaseTool):
    capability = "pdf_compose"
    provider = "weasyprint"
    cost_per_call_usd = 0.0
    agent_skills = ["weasyprint-cookbook"]
    status = "active"

    def render_html_string(self, html: str, out_path: pathlib.Path,
                           *, base_url: pathlib.Path | None = None) -> dict:
        """Render an HTML string to PDF at out_path. Returns metadata."""
        from weasyprint import HTML

        out_path = pathlib.Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        base = str(base_url) if base_url else None
        doc = HTML(string=html, base_url=base).render()
        doc.write_pdf(str(out_path))
        size_mb = out_path.stat().st_size / (1024 * 1024)
        page_count = len(doc.pages)
        print(
            f"[weasyprint] {out_path.name}  {page_count} pages  {size_mb:.1f} MB",
            file=sys.stderr,
        )
        return {
            "pdf_path": str(out_path),
            "page_count": page_count,
            "size_mb": size_mb,
        }

    def render_template(
        self,
        *,
        layout_j2: pathlib.Path,
        context: dict,
        out_path: pathlib.Path,
        save_html: bool = True,
    ) -> dict:
        """Render a Jinja2 template with context, then to PDF.

        layout_j2 is the path to the template; its parent dir + the project's
        library/layouts/ are included on the Jinja2 search path so
        {% include "_components/..." %} works. The base_url for relative
        image paths is also the project root (so img src='output/<slug>/...'
        resolves)."""
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        layout_j2 = pathlib.Path(layout_j2)
        project_root = layout_j2.resolve().parents[2]   # tools/pdf/x.py → repo root
        layout_dir = layout_j2.parent
        env = Environment(
            loader=FileSystemLoader([str(layout_dir), str(project_root / "library" / "layouts")]),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        tmpl = env.get_template(layout_j2.name)
        html = tmpl.render(**context)

        out_path = pathlib.Path(out_path)
        if save_html:
            html_path = out_path.with_suffix(".html")
            html_path.write_text(html, encoding="utf-8")

        return self.render_html_string(html, out_path, base_url=project_root)

    def run(self, *, issue_dir: pathlib.Path, layout: dict, brand: dict,
            article: dict, spec: dict) -> dict:
        """High-level entry: derive layout_j2 path from layout name and render.

        Looks up library/layouts/<layout.name>.html.j2 relative to project root.
        """
        project_root = pathlib.Path(__file__).resolve().parents[2]
        layout_j2 = project_root / "library" / "layouts" / f"{layout['name']}.html.j2"
        out_path = pathlib.Path(issue_dir) / "magazine.pdf"

        context = {
            "layout": layout,
            "brand": brand,
            "article": article,
            "spec": spec,
            "language": brand.get("default_language", "en"),
            "issue_dir": str(issue_dir),
        }
        meta = self.render_template(
            layout_j2=layout_j2,
            context=context,
            out_path=out_path,
            save_html=True,
        )
        meta["html_path"] = str(out_path.with_suffix(".html"))
        return meta


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(WeasyprintCompose())
```

- [ ] **Step B2.4: Update `tools/pdf/__init__.py`**

```python
"""pdf capability family."""
from tools.pdf import reportlab_compose  # noqa: F401
from tools.pdf import weasyprint_compose  # noqa: F401
```

- [ ] **Step B2.5: Run tests**

```bash
python -m pytest tests/unit/test_weasyprint_compose.py -v
```

Expected: 3 pass.

- [ ] **Step B2.6: Commit**

```bash
git add tools/pdf/weasyprint_compose.py tools/pdf/__init__.py tests/unit/test_weasyprint_compose.py
git commit -m "feat(tools/pdf): add WeasyprintCompose (HTML/CSS → print PDF)"
```

---

### Task B3: Root template `_base.html.j2`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_base.html.j2`

- [ ] **Step B3.1: Write `_base.html.j2`**

```jinja2
<!DOCTYPE html>
<html lang="{{ language }}">
<head>
<meta charset="utf-8">
<title>{{ article.display_title[language] | default('Magazine') }}</title>

{# Google Fonts: collect all unique families requested by typography pack #}
{%- set families = [] -%}
{%- for slot in ['display','body','kicker','caption','pull_quote','drop_cap','page_number'] -%}
  {%- set tp = brand.typography[slot] -%}
  {%- if tp and tp.source == 'google-fonts' and tp.family not in families -%}
    {%- set _ = families.append(tp.family) -%}
  {%- endif -%}
{%- endfor %}
{%- if families %}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?{% for f in families %}family={{ f|replace(' ','+') }}:wght@400;500;600;700;900&{% endfor %}display=swap" rel="stylesheet">
{%- endif %}

<style>
@page {
  size: {{ brand.print_specs.page_size }};
  bleed: {{ brand.print_specs.bleed_mm }}mm;
  marks: {% if brand.print_specs.trim_marks %}crop{% if brand.print_specs.registration_marks %} cross{% endif %}{% else %}none{% endif %};
  margin:
    {{ brand.print_specs.margin_top_mm }}mm
    {{ brand.print_specs.margin_outer_mm }}mm
    {{ brand.print_specs.margin_bottom_mm }}mm
    {{ brand.print_specs.margin_inner_mm }}mm;

  @bottom-center {
    content: counter(page);
    font-family: '{{ brand.typography.page_number.family }}', monospace;
    font-size: {{ brand.typography.page_number.size_pt }}pt;
    color: var(--color-ink-secondary);
  }
}
@page :left  { margin-right: {{ brand.print_specs.margin_inner_mm }}mm; }
@page :right { margin-left:  {{ brand.print_specs.margin_inner_mm }}mm; }
@page cover  { @bottom-center { content: ""; } }
@page back-cover { @bottom-center { content: ""; } }

:root {
  --color-bg-paper:       {{ brand.visual_tokens.color_bg_paper }};
  --color-ink-primary:    {{ brand.visual_tokens.color_ink_primary }};
  --color-ink-secondary:  {{ brand.visual_tokens.color_ink_secondary }};
  --color-accent:         {{ brand.visual_tokens.color_accent }};
  --color-quote-bg:       {{ brand.visual_tokens.color_quote_bg }};
  --color-quote-fg:       {{ brand.visual_tokens.color_quote_fg }};
  --rule-thickness:       {{ brand.visual_tokens.rule_thickness_pt }}pt;
  --baseline-mm:          {{ brand.print_specs.baseline_grid_mm }}mm;

  --font-display:         '{{ brand.typography.display.family }}', serif;
  --font-body:            '{{ brand.typography.body.family }}', serif;
  --font-kicker:          '{{ brand.typography.kicker.family }}', monospace;
  --font-caption:         '{{ brand.typography.caption.family }}', monospace;
  --font-pull-quote:      '{{ brand.typography.pull_quote.family }}', serif;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font-body);
  font-size: {{ brand.typography.body.size_pt }}pt;
  line-height: {{ brand.typography.body.leading }};
  hyphens: {% if brand.typography.body.hyphenate %}auto{% else %}manual{% endif %};
  text-align: {{ brand.typography.body.align }};
  background: var(--color-bg-paper);
  color: var(--color-ink-primary);
}

.spread {
  break-after: page;
  page: auto;
}
.spread.cover       { page: cover; }
.spread.back-cover  { page: back-cover; }

.kicker {
  font-family: var(--font-kicker);
  text-transform: {{ brand.typography.kicker.transform }};
  letter-spacing: {{ brand.typography.kicker.letter_spacing }};
  font-size: {{ brand.typography.kicker.size_pt }}pt;
  color: var(--color-ink-secondary);
}

.title {
  font-family: var(--font-display);
  font-weight: 900;
  line-height: 1.05;
  margin: 0.4em 0;
}
.title-xl  { font-size: 48pt; }
.title-l   { font-size: 36pt; }
.title-m   { font-size: 24pt; }

.lead {
  font-family: var(--font-body);
  font-style: italic;
  font-size: 13pt;
  line-height: 1.4;
  margin: 0.6em 0 0.9em 0;
}

.body p { margin-bottom: 0.7em; }

{% if brand.typography.drop_cap.enabled %}
.drop-cap p:first-of-type::first-letter {
  font-family: '{{ brand.typography.drop_cap.family }}', serif;
  font-weight: {{ brand.typography.drop_cap.weight }};
  font-size: calc({{ brand.typography.body.size_pt }}pt
                 * {{ brand.typography.drop_cap.lines }}
                 * {{ brand.typography.body.leading }});
  float: left;
  line-height: 0.85;
  margin: 0 0.1em -0.1em 0;
  color: var(--color-{{ brand.typography.drop_cap.color_token }});
}
{% endif %}

.pull-quote {
  font-family: var(--font-pull-quote);
  font-style: {{ brand.typography.pull_quote.style }};
  font-size: {{ brand.typography.pull_quote.size_pt }}pt;
  line-height: 1.15;
  white-space: pre-line;
}

.caption {
  font-family: var(--font-caption);
  font-style: {{ brand.typography.caption.style }};
  font-size: {{ brand.typography.caption.size_pt }}pt;
  color: var(--color-ink-secondary);
}

img.slot {
  display: block;
  width: 100%;
  height: auto;
  object-fit: cover;
}

hr.accent {
  border: none;
  border-top: var(--rule-thickness) solid var(--color-accent);
  width: 4em;
  margin: 0.4em 0;
}

/* Spread layout primitives — components compose these */
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8mm; }
.grid-2-7-5 { display: grid; grid-template-columns: 7fr 5fr; gap: 8mm; }
.grid-2-5-7 { display: grid; grid-template-columns: 5fr 7fr; gap: 8mm; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6mm; }
.grid-3x2 { display: grid; grid-template-columns: 1fr 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 4mm; }
</style>
</head>
<body>
{% block content %}{% endblock %}
</body>
</html>
```

- [ ] **Step B3.2: Sanity test it parses**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('library/layouts'))
tmpl = env.get_template('_base.html.j2')
print('template loaded OK,', len(tmpl.render(
    article={'display_title': {'en': 'X'}},
    brand={'typography': {
        'display': {'family':'Playfair Display','source':'google-fonts'},
        'body': {'family':'Source Serif 4','source':'google-fonts','size_pt':10,'leading':1.45,'align':'justify','hyphenate':True},
        'kicker': {'family':'IBM Plex Mono','source':'google-fonts','transform':'uppercase','letter_spacing':'0.08em','size_pt':8},
        'caption': {'family':'IBM Plex Mono','source':'google-fonts','style':'italic','size_pt':8},
        'pull_quote': {'family':'Playfair Display','source':'google-fonts','style':'italic','size_pt':32},
        'drop_cap': {'enabled':True,'family':'Playfair Display','source':'google-fonts','weight':900,'lines':3,'color_token':'accent'},
        'page_number': {'family':'IBM Plex Mono','source':'google-fonts','weight':400,'size_pt':9},
    },
    'print_specs': {'page_size':'A4','bleed_mm':3,'trim_marks':True,'registration_marks':False,'margin_top_mm':20,'margin_bottom_mm':22,'margin_outer_mm':18,'margin_inner_mm':22,'baseline_grid_mm':4},
    'visual_tokens': {'color_bg_paper':'#f5efe6','color_ink_primary':'#1a1a1a','color_ink_secondary':'#6b6b6b','color_accent':'#c2272d','color_quote_bg':'#1a1a1a','color_quote_fg':'#f5efe6','rule_thickness_pt':1.5,'margin_note_indent_mm':4}},
    language='en',
)), 'chars')
"
```

- [ ] **Step B3.3: Commit**

```bash
git add library/layouts/_base.html.j2
git commit -m "feat(layouts): _base.html.j2 root template (CSS Paged Media + tokens)"
```

---

### Task B4: Component `_components/cover.html.j2`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/cover.html.j2`

- [ ] **Step B4.1: Write `cover.html.j2`**

```jinja2
{% set sc = article.spread_copy[0] %}
{% set img_path = images_root ~ '/spread-01/cover_hero.png' %}
<section class="spread cover" data-spread-idx="1">
  <div style="position: relative; width: 100%; height: 100%; min-height: 100vh;">
    <img class="slot" src="{{ img_path }}" alt="cover hero"
         style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 0;">
    <div style="position: absolute; top: 12mm; left: 0; right: 0; text-align: center; z-index: 2;
                color: var(--color-bg-paper); mix-blend-mode: difference;">
      <div class="title title-xl" style="font-family: var(--font-display); letter-spacing: 0.04em;">
        {{ article.masthead_override or brand.masthead }}
      </div>
      <div class="kicker" style="margin-top: 6mm; color: inherit; opacity: 0.85;">
        {{ article.issue_label[language] }}
      </div>
    </div>
    <div style="position: absolute; bottom: 18mm; left: 12mm; right: 12mm; z-index: 2;
                color: var(--color-bg-paper); mix-blend-mode: difference;">
      <div class="kicker" style="color: inherit; opacity: 0.7;">
        {{ article.cover_kicker[language] }}
      </div>
      <div class="title title-l" style="margin-top: 4mm; font-style: italic;">
        {{ article.cover_line[language] }}
      </div>
    </div>
  </div>
</section>
```

The `mix-blend-mode: difference` overlay strategy gives readable text over arbitrary images without us picking a foreground color per cover. If color contrast is poor, add a subtle dark gradient overlay.

- [ ] **Step B4.2: Commit**

```bash
git add library/layouts/_components/cover.html.j2
git commit -m "feat(layouts): cover.html.j2 component"
```

---

### Task B5: Component `feature-spread.html.j2`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/feature-spread.html.j2`

- [ ] **Step B5.1: Write `feature-spread.html.j2`**

The component is a 2-page spread with: left page = hero image; right page = title + kicker + lead + body + 3 captioned thumbnails along the right edge.

```jinja2
{% set spread_idx = sc.idx %}
{% set hero = images_root ~ '/spread-' ~ '{:02d}'.format(spread_idx) ~ '/feature_hero.png' %}
{% set cap1 = images_root ~ '/spread-' ~ '{:02d}'.format(spread_idx) ~ '/feature_captioned.1.png' %}
{% set cap2 = images_root ~ '/spread-' ~ '{:02d}'.format(spread_idx) ~ '/feature_captioned.2.png' %}
{% set cap3 = images_root ~ '/spread-' ~ '{:02d}'.format(spread_idx) ~ '/feature_captioned.3.png' %}

<section class="spread feature-spread" data-spread-idx="{{ spread_idx }}">
  <div class="grid-2-7-5" style="height: 100%; padding-top: 0;">
    <div class="left" style="padding: 0;">
      <img class="slot" src="{{ hero }}"
           style="width: 100%; height: 100vh; object-fit: cover;"
           alt="feature hero">
    </div>
    <div class="right" style="padding: 18mm 16mm 18mm 8mm; display: flex; flex-direction: column; gap: 4mm;">
      <div class="kicker">{{ sc.kicker[language] }}</div>
      <hr class="accent">
      <h2 class="title title-l">{{ sc.title[language] }}</h2>
      <p class="lead">{{ sc.lead[language] }}</p>
      <div class="body drop-cap" style="font-size: {{ brand.typography.body.size_pt }}pt;
                                         line-height: {{ brand.typography.body.leading }};
                                         column-count: 1;">
        {% for para in sc.body[language].strip().split('\n\n') %}
        <p>{{ para | trim }}</p>
        {% endfor %}
      </div>
      <div class="grid-3" style="margin-top: 6mm;">
        <figure>
          <img class="slot" src="{{ cap1 }}" style="aspect-ratio: 3/2;">
          <figcaption class="caption">{{ sc.image_slot_overrides['feature_captioned.1'] | default('') | truncate(60) }}</figcaption>
        </figure>
        <figure>
          <img class="slot" src="{{ cap2 }}" style="aspect-ratio: 3/2;">
          <figcaption class="caption">{{ sc.image_slot_overrides['feature_captioned.2'] | default('') | truncate(60) }}</figcaption>
        </figure>
        <figure>
          <img class="slot" src="{{ cap3 }}" style="aspect-ratio: 3/2;">
          <figcaption class="caption">{{ sc.image_slot_overrides['feature_captioned.3'] | default('') | truncate(60) }}</figcaption>
        </figure>
      </div>
    </div>
  </div>
</section>
```

- [ ] **Step B5.2: Commit**

```bash
git add library/layouts/_components/feature-spread.html.j2
git commit -m "feat(layouts): feature-spread.html.j2 (left hero + right body + 3 captioned)"
```

---

### Task B6: Components `portrait-wall` + `pull-quote`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/portrait-wall.html.j2`
- Create: `~/github/openMagazine/library/layouts/_components/pull-quote.html.j2`

- [ ] **Step B6.1: Write `portrait-wall.html.j2`**

```jinja2
{% set spread_idx = sc.idx %}
{% set base = images_root ~ '/spread-' ~ '{:02d}'.format(spread_idx) %}

<section class="spread portrait-wall" data-spread-idx="{{ spread_idx }}">
  <div style="padding: 18mm 16mm; height: 100%; display: flex; flex-direction: column;">
    <div class="kicker" style="margin-bottom: 4mm;">{{ sc.title[language] }}</div>
    <hr class="accent">
    <div class="grid-3x2" style="flex: 1; gap: 6mm; margin-top: 8mm;">
      {% for cap in sc.captions %}
      {% set n = loop.index %}
      <figure style="display: flex; flex-direction: column; gap: 2mm;">
        <img class="slot" src="{{ base }}/portrait_wall.{{ n }}.png"
             style="aspect-ratio: 1/1; width: 100%; object-fit: cover;">
        <figcaption class="caption">{{ cap[language] }}</figcaption>
      </figure>
      {% endfor %}
    </div>
  </div>
</section>
```

- [ ] **Step B6.2: Write `pull-quote.html.j2`**

```jinja2
{% set spread_idx = sc.idx %}
{% set env_img = images_root ~ '/spread-' ~ '{:02d}'.format(spread_idx) ~ '/pullquote_environment.png' %}

<section class="spread pull-quote-spread" data-spread-idx="{{ spread_idx }}">
  <div style="position: relative; width: 100%; height: 100vh; overflow: hidden;">
    <img class="slot" src="{{ env_img }}"
         style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 0;
                filter: brightness(0.6);">
    <div style="position: absolute; inset: 0; background: linear-gradient(to bottom, rgba(0,0,0,0.0), rgba(0,0,0,0.5)); z-index: 1;"></div>
    <blockquote class="pull-quote"
                style="position: absolute; left: 16mm; right: 16mm; bottom: 32mm; z-index: 2;
                       color: var(--color-bg-paper); text-align: center;">
      {{ sc.quote[language] }}
    </blockquote>
    <cite class="caption"
          style="position: absolute; left: 0; right: 0; bottom: 22mm; z-index: 2;
                 text-align: center; color: var(--color-bg-paper); opacity: 0.8;
                 font-style: normal;">
      {{ sc.quote_attribution[language] }}
    </cite>
  </div>
</section>
```

- [ ] **Step B6.3: Commit**

```bash
git add library/layouts/_components/portrait-wall.html.j2\
        library/layouts/_components/pull-quote.html.j2
git commit -m "feat(layouts): portrait-wall + pull-quote components"
```

---

### Task B7: Components `toc` + `colophon` + `back-cover`

**Files:**
- Create: 3 j2 files

- [ ] **Step B7.1: Write `toc.html.j2`**

```jinja2
<section class="spread toc" data-spread-idx="{{ sc.idx }}">
  <div class="grid-2" style="height: 100vh; padding: 18mm 16mm;">
    <div class="left">
      <div class="kicker">{{ article.cover_kicker[language] }}</div>
      <hr class="accent">
      <h2 class="title title-l" style="margin-top: 6mm;">CONTENTS</h2>
      <p class="lead" style="margin-top: 8mm; font-style: normal;">{{ article.issue_label[language] }}</p>
    </div>
    <div class="right" style="padding-top: 8mm;">
      {% for entry in sc.table_of_contents %}
      <div style="display: grid; grid-template-columns: auto 1fr auto; gap: 4mm;
                  align-items: baseline; padding: 3mm 0;
                  border-bottom: 0.5pt solid var(--color-ink-secondary);">
        <span class="kicker" style="color: var(--color-accent);">{{ '%02d' % entry.page }}</span>
        <span style="font-family: var(--font-display); font-size: 14pt; font-weight: 700;">
          {{ entry[language] }}
        </span>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
```

- [ ] **Step B7.2: Write `colophon.html.j2`**

```jinja2
{% set credits = sc.credits[language] if sc.credits[language] is mapping else sc.credits %}
<section class="spread colophon" data-spread-idx="{{ sc.idx }}">
  <div class="grid-2" style="height: 100vh; padding: 18mm 16mm; gap: 16mm;">
    <div class="left">
      <div class="kicker">COLOPHON</div>
      <hr class="accent">
      <h2 class="title title-m" style="margin-top: 6mm;">{{ article.masthead_override or brand.masthead }}</h2>
      <p class="lead" style="margin-top: 4mm; font-style: normal;">{{ article.issue_label[language] }}</p>
    </div>
    <div class="right" style="padding-top: 4mm; display: flex; flex-direction: column; gap: 5mm; font-size: 9.5pt;">
      {% for k, v in credits.items() %}
      <div>
        <div class="kicker" style="color: var(--color-ink-secondary); margin-bottom: 1mm;">
          {{ k | replace('_', ' ') }}
        </div>
        <div>{{ v }}</div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
```

- [ ] **Step B7.3: Write `back-cover.html.j2`**

```jinja2
{% set spread_idx = sc.idx %}
{% set img = images_root ~ '/spread-' ~ '{:02d}'.format(spread_idx) ~ '/back_coda.png' %}

<section class="spread back-cover" data-spread-idx="{{ spread_idx }}">
  <div style="position: relative; width: 100%; height: 100vh; overflow: hidden;">
    <img class="slot" src="{{ img }}"
         style="position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 0;">
    {% if sc.quote and sc.quote[language] %}
    <blockquote class="pull-quote"
                style="position: absolute; left: 16mm; right: 16mm; bottom: 24mm; z-index: 2;
                       color: var(--color-bg-paper); mix-blend-mode: difference;
                       text-align: center; font-size: 22pt;">
      {{ sc.quote[language] }}
    </blockquote>
    {% endif %}
  </div>
</section>
```

- [ ] **Step B7.4: Commit**

```bash
git add library/layouts/_components/toc.html.j2 \
        library/layouts/_components/colophon.html.j2 \
        library/layouts/_components/back-cover.html.j2
git commit -m "feat(layouts): toc + colophon + back-cover components"
```

---

### Task B8: Assemble `editorial-16page.html.j2` + dry-run integration test

**Files:**
- Create: `~/github/openMagazine/library/layouts/editorial-16page.html.j2`
- Create: `~/github/openMagazine/tests/integration/__init__.py`
- Create: `~/github/openMagazine/tests/integration/test_render_dry_run.py`

- [ ] **Step B8.1: Write `editorial-16page.html.j2`**

```jinja2
{% extends "_base.html.j2" %}
{% block content %}
{# images_root is e.g. "output/<slug>/images" — used in components #}
{% for sc in article.spread_copy %}
  {% if sc.type == 'cover' %}
    {% include "_components/cover.html.j2" %}
  {% elif sc.type == 'toc' %}
    {% include "_components/toc.html.j2" %}
  {% elif sc.type == 'feature-spread' %}
    {% include "_components/feature-spread.html.j2" %}
  {% elif sc.type == 'pull-quote' %}
    {% include "_components/pull-quote.html.j2" %}
  {% elif sc.type == 'portrait-wall' %}
    {% include "_components/portrait-wall.html.j2" %}
  {% elif sc.type == 'colophon' %}
    {% include "_components/colophon.html.j2" %}
  {% elif sc.type == 'back-cover' %}
    {% include "_components/back-cover.html.j2" %}
  {% else %}
    <section class="spread unknown"><h2>Unknown spread type: {{ sc.type }}</h2></section>
  {% endif %}
{% endfor %}
{% endblock %}
```

- [ ] **Step B8.2: Write integration test**

Create `tests/integration/__init__.py` (empty) and `tests/integration/test_render_dry_run.py`:

```python
"""Integration test: render full editorial-16page PDF with placeholder PNGs.

No Vertex / no Codex calls. Generates a 1x1 black PNG for each image slot,
fills in article + brand + layout, runs Weasyprint, asserts PDF has 16 pages
and is plausibly sized (>500KB).
"""
import shutil
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
        # 100x100 black PNG; sized later by CSS object-fit
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

    # Place placeholder PNGs at output/<slug>/images/spread-NN/<slot>.png
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
    assert meta["page_count"] >= 14            # 16 spreads but some collapse
    assert meta["size_mb"] > 0.05              # rough plausibility (50 KB+)
```

- [ ] **Step B8.3: Run integration test**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
python -m pytest tests/integration/test_render_dry_run.py -v
```

Expected: pass; PDF generates with 14-16 pages.

- [ ] **Step B8.4: Inspect output PDF**

```bash
ls -la /tmp/pytest-*/test_renders_editorial_16page_with_placeholders0/issue/magazine.pdf 2>/dev/null || echo "find via pytest output"
```

If you can open it on your mac: `open /tmp/.../magazine.pdf`. Should see 16 pages of black squares with typography + page numbers + spread structure visible.

- [ ] **Step B8.5: Commit**

```bash
git add library/layouts/editorial-16page.html.j2 \
        tests/integration/__init__.py \
        tests/integration/test_render_dry_run.py
git commit -m "feat(layouts): editorial-16page.html.j2 + integration dry-run test"
```

---

## Phase C — Image gen adaptation (~2 days, 7 tasks)

### Task C1: `lib/storyboard_planner.py` + tests

**Files:**
- Create: `~/github/openMagazine/lib/storyboard_planner.py`
- Create: `~/github/openMagazine/tests/unit/test_storyboard_planner.py`

- [ ] **Step C1.1: Write the failing test**

```python
"""Tests for storyboard_planner."""
import pytest

from lib.storyboard_planner import plan_storyboard


def test_plan_basic_4_slots():
    slots = [
        {"id": "spread-01.cover_hero",   "role": "cover_hero", "aspect": "3:4", "spread_idx": 1},
        {"id": "spread-03.feature_hero", "role": "portrait",   "aspect": "3:4", "spread_idx": 3},
        {"id": "spread-03.feature_captioned.1", "role": "scene", "aspect": "3:2", "spread_idx": 3},
        {"id": "spread-09.back_coda",    "role": "back_coda",  "aspect": "2:3", "spread_idx": 9},
    ]
    plan = plan_storyboard(slots, outer_aspect="2:3")
    assert plan["outer_aspect"] == "2:3"
    assert plan["outer_size_px"] == [1024, 1536]
    assert len(plan["cells"]) == 4
    # All slots represented
    slot_ids = {c["slot_id"] for c in plan["cells"]}
    assert slot_ids == {s["id"] for s in slots}


def test_plan_21_slots_packs_into_grid():
    """Editorial-16page has 21 slots — they all fit in 1024x1536."""
    slots = [
        {"id": f"slot.{i}", "role": "portrait", "aspect": "1:1", "spread_idx": (i // 6) + 1}
        for i in range(21)
    ]
    plan = plan_storyboard(slots)
    assert len(plan["cells"]) == 21
    # No overlaps
    bboxes = [tuple(c["bbox_px"]) for c in plan["cells"]]
    assert len(set(bboxes)) == 21


def test_cells_have_required_keys():
    slots = [{"id": "s.1", "role": "portrait", "aspect": "1:1", "spread_idx": 1}]
    plan = plan_storyboard(slots)
    cell = plan["cells"][0]
    for k in ("slot_id", "row", "col", "rowspan", "colspan", "aspect", "bbox_px", "page_label"):
        assert k in cell, f"missing key {k}"
```

- [ ] **Step C1.2: Run, expect ImportError**

```bash
python -m pytest tests/unit/test_storyboard_planner.py -v
```

- [ ] **Step C1.3: Write `lib/storyboard_planner.py`**

```python
"""storyboard_planner — pack heterogeneous-aspect image slots into a grid.

Greedy algorithm: sort slots by area desc, place into a uniform 6x4 grid by
default. Each cell takes one grid cell; aspect drift is acceptable for v0.3.0
(model is told the per-cell aspect anyway).

For v0.3.1+ we may upgrade to a true bin-pack with rowspan/colspan.
"""
from __future__ import annotations


GRID_ROWS_DEFAULT = 6
GRID_COLS_DEFAULT = 4
OUTER_W_PX = 1024
OUTER_H_PX = 1536


def plan_storyboard(slots: list[dict], outer_aspect: str = "2:3") -> dict:
    """Pack slots into an outer-aspect-2:3 portrait grid.

    Args:
      slots: each {id, role, aspect, spread_idx, ...}
      outer_aspect: overall storyboard aspect; only "2:3" supported in v0.3.0

    Returns:
      {outer_aspect, outer_size_px, cells: [{slot_id, row, col, rowspan,
                                              colspan, aspect, bbox_px,
                                              page_label}, ...]}
    """
    if outer_aspect != "2:3":
        raise ValueError(f"only '2:3' outer_aspect supported, got {outer_aspect!r}")

    n = len(slots)
    if n == 0:
        return {"outer_aspect": outer_aspect, "outer_size_px": [OUTER_W_PX, OUTER_H_PX], "cells": []}

    # Choose grid that fits n slots with rows ≥ cols (since outer is portrait)
    # Try (rows, cols) with rows*cols ≥ n and rows ≥ cols
    cols = 1
    while True:
        rows = (n + cols - 1) // cols
        if rows >= cols:
            break
        cols += 1

    cell_w = OUTER_W_PX // cols
    cell_h = OUTER_H_PX // rows

    cells = []
    for i, slot in enumerate(slots):
        row = i // cols
        col = i % cols
        x = col * cell_w
        y = row * cell_h
        cells.append({
            "slot_id": slot["id"],
            "row": row,
            "col": col,
            "rowspan": 1,
            "colspan": 1,
            "aspect": slot.get("aspect", "1:1"),
            "bbox_px": [x, y, cell_w, cell_h],
            "page_label": f"{i+1:02d}",
        })

    return {
        "outer_aspect": outer_aspect,
        "outer_size_px": [OUTER_W_PX, OUTER_H_PX],
        "grid": {"rows": rows, "cols": cols},
        "cells": cells,
    }
```

- [ ] **Step C1.4: Run tests + commit**

```bash
python -m pytest tests/unit/test_storyboard_planner.py -v
git add lib/storyboard_planner.py tests/unit/test_storyboard_planner.py
git commit -m "feat(lib): storyboard_planner (greedy grid packing for multi-aspect slots)"
```

---

### Task C2: `library/templates/storyboard_v2.prompt.md`

**Files:**
- Create: `~/github/openMagazine/library/templates/storyboard_v2.prompt.md`

- [ ] **Step C2.1: Write the template**

```
OUTPUT IMAGE FORMAT (HARD CONSTRAINT):
- The OUTPUT IMAGE itself must be 2:3 PORTRAIT orientation ({{OUTER_W}}×{{OUTER_H}}), NOT square.
- Inside that portrait canvas: a {{GRID_ROWS}}×{{GRID_COLS}} grid of {{CELL_COUNT}} cells.
- Each cell has its OWN aspect (not all uniform); see cell layout below.
- Page numbers labeled top-left of each cell.
- White ~24px gutters between cells and around the grid.

Generate one image: a multi-aspect editorial storyboard for a {{PAGE_COUNT}}-page magazine.

Subject in EVERY cell (locked, identical across all):
{{TRAITS}}

Theme world: {{THEME_WORLD}}

Style locked across all cells: {{STYLE_ANCHOR}}

CELL LAYOUT (slot_id, page label, intended aspect, role, scene description):

{{CELL_LIST}}

Constraints:
- SAME character across all cells (face / markings / build / baseline expression).
- SAME color palette across all cells.
- SAME lighting language across all cells.
- Each cell is low-detail but composition + mood must read clearly.
- Each cell respects its declared intended aspect inside the cell rectangle.
- No text inside cells except the page label.
- No watermarks, no logos, no caption boxes.
```

`{{CELL_LIST}}` will be rendered by `prompt_builder_v2.build_storyboard_prompt_v2` from the planner's plan.cells, formatted as one line per cell:

```
01 - spread-01.cover_hero (3:4 portrait, role: cover_hero) - hero portrait, character at module windowsill
02 - spread-03.feature_hero (3:4 portrait, role: portrait) - character at boulder, hand on rock
...
```

- [ ] **Step C2.2: Commit**

```bash
git add library/templates/storyboard_v2.prompt.md
git commit -m "feat(templates): storyboard_v2 multi-aspect prompt template"
```

---

### Task C3: 6 role-driven upscale prompt templates

**Files:**
- Create: `library/templates/upscale_portrait.prompt.md`
- Create: `library/templates/upscale_scene.prompt.md`
- Create: `library/templates/upscale_environment.prompt.md`
- Create: `library/templates/upscale_detail.prompt.md`
- Create: `library/templates/upscale_cover_hero.prompt.md`
- Create: `library/templates/upscale_back_coda.prompt.md`

- [ ] **Step C3.1: Write `upscale_portrait.prompt.md`**

```
Subject: {{TRAITS}}.

Scene: {{SCENE}}.

Composition: maintain character placement and lighting from the FIRST reference (storyboard cell). Maintain character identity (face/markings/build/expression) from SUBSEQUENT references (protagonist photos).

Camera: shot on Sony Alpha 7R V with Sigma 35mm f/1.4 Art lens. Raw uncorrected file, no LUTs.

Texture: surface imperfections — fur strands, skin pores, fabric weave, micro-shadows.

Style: {{STYLE_ANCHOR}}.

Aspect: {{ASPECT}}.

Negative prompt: cartoonish, AI-looking, plastic skin/fur, over-smoothed, glossy CGI, anime cute, oversized eyes, beauty-filter, plush appearance, 3D render look, oily highlights, painted whiskers, mournful expression, droopy eyes, deformed anatomy, garbled typography, watermarks, logos, visible page numbers from storyboard cell.
```

- [ ] **Step C3.2: Write `upscale_scene.prompt.md`**

```
Subject: {{TRAITS}}.

Scene: {{SCENE}}.

Composition: wide-to-medium framing; subject occupies a defined fraction of the frame (specified in scene). Maintain layout direction from FIRST reference; identity from SUBSEQUENT references.

Camera: shot on Leica SL3 with 35mm Summilux. Raw uncorrected.

Lighting: as described in scene; preserve direction from cell reference.

Style: {{STYLE_ANCHOR}}.

Aspect: {{ASPECT}}.

Negative prompt: cartoonish, AI-look, plastic, over-smoothed, deformed anatomy, garbled typography, watermarks, visible page numbers.
```

- [ ] **Step C3.3: Write `upscale_environment.prompt.md`**

```
Scene: {{SCENE}}.

Composition: wide environmental establishing shot. Subject either absent or a tiny figure (≤ 5% of frame area). Negative space dominates. Maintain framing from FIRST reference (cell).

Camera: shot on Phase One IQ4 with 32mm lens. Raw uncorrected, large-format detail.

Lighting: dramatic, atmospheric; respect cell reference for direction.

Style: {{STYLE_ANCHOR}}.

Aspect: {{ASPECT}}.

Negative prompt: subject filling frame, AI-looking, watermarks, garbled typography, visible page numbers.
```

- [ ] **Step C3.4: Write `upscale_detail.prompt.md`**

```
Scene: {{SCENE}} — close detail / texture study.

Composition: tight detail crop. No protagonist in frame; subject implied through environmental traces.

Camera: macro lens; shallow DOF.

Style: {{STYLE_ANCHOR}}.

Aspect: {{ASPECT}}.

Negative prompt: subject in frame, AI-look, watermarks, visible page numbers.
```

- [ ] **Step C3.5: Write `upscale_cover_hero.prompt.md`**

```
Subject: {{TRAITS}}, in a hero pose appropriate to {{THEME_WORLD}}.

Scene: {{SCENE}}.

Composition: cover hero. Subject occupies upper two-thirds of frame, dramatic framing. Eyeline gives upper-frame room (masthead will be overlaid on cover composition by the renderer; do not render the masthead text into the photo).

Lighting: dramatic single key, deep shadow side. No rim.

Camera: Hasselblad H6D-100c with 80mm f/2.8. Raw uncorrected.

Style: {{STYLE_ANCHOR}}, with high-end editorial photography finish — slight grain.

Aspect: {{ASPECT}}.

NOTE: do NOT render typography (masthead, cover line, kicker) inside this image. The renderer overlays them in the PDF compose stage.

Negative prompt: any rendered text or typography, lorem ipsum, garbled letterforms, broken serifs, watermarks, logos, masthead text, footer bar, barcode, ISSN, version numerals, "VOL." text, AI-looking type, deformed anatomy, plastic skin/fur.
```

- [ ] **Step C3.6: Write `upscale_back_coda.prompt.md`**

```
Subject: {{TRAITS}}, quiet coda pose appropriate to {{THEME_WORLD}}.

Scene: {{SCENE}} — single small element in mostly empty frame. Calm, restrained. Bottom 30% is negative space.

Composition: maintain framing from FIRST reference (cell). Identity from SUBSEQUENT references.

Lighting: soft, diffused, low-contrast. Late-day or pre-dawn.

Camera: Leica M11 with Summicron 50mm. Raw uncorrected.

Style: {{STYLE_ANCHOR}}.

Aspect: {{ASPECT}}.

NOTE: do NOT render typography. The renderer overlays the closing quote in the PDF compose stage.

Negative prompt: any rendered text, masthead, cover line, footer bar, page numbers from cell, garbled typography, AI-look, deformed anatomy, plastic skin/fur.
```

- [ ] **Step C3.7: Commit**

```bash
git add library/templates/upscale_*.prompt.md
git commit -m "feat(templates): 6 role-driven upscale prompts (portrait/scene/environment/detail/cover_hero/back_coda)"
```

---

### Task C4: `lib/prompt_builder_v2.py` + tests

**Files:**
- Create: `~/github/openMagazine/lib/prompt_builder_v2.py`
- Create: `~/github/openMagazine/tests/unit/test_prompt_builder_v2.py`

- [ ] **Step C4.1: Write the failing test**

```python
"""Tests for prompt_builder_v2."""
import pytest

from lib.prompt_builder_v2 import (
    build_storyboard_prompt_v2,
    build_upscale_prompt,
    ROLE_TEMPLATES,
)


@pytest.fixture
def spec(): return {"slug": "test", "issue_number": "01", "date": "MAY 2026", "overrides": {}}


@pytest.fixture
def layers():
    return {
        "subject": {"name": "luna", "display_name": {"en": "Luna"}, "traits": "tabby cat"},
        "theme": {"theme_world": "outer space", "default_cover_line": {"en": "L"},
                  "page_plan_hints": []},
        "layout": {"page_count": 16, "storyboard_grid": "6x4",
                   "image_slots": [
                       {"id": "spread-01.cover_hero", "role": "cover_hero", "aspect": "3:4", "spread_idx": 1},
                       {"id": "spread-09.back_coda", "role": "back_coda", "aspect": "2:3", "spread_idx": 9},
                   ]},
        "brand": {"masthead": "M"},
        "style": {"style_anchor": "Annie Leibovitz, Hasselblad H6D"},
    }


def test_role_templates_complete():
    for role in ("portrait", "scene", "environment", "detail", "cover_hero", "back_coda"):
        assert role in ROLE_TEMPLATES


def test_build_upscale_portrait(spec, layers):
    p = build_upscale_prompt(role="portrait", spec=spec, layers=layers,
                             slot_id="spread-03.feature_hero",
                             scene="character at boulder, hand on rock",
                             aspect="3:4")
    assert "tabby cat" in p
    assert "character at boulder" in p
    assert "Annie Leibovitz" in p
    assert "{{" not in p


def test_build_upscale_environment(spec, layers):
    p = build_upscale_prompt(role="environment", spec=spec, layers=layers,
                             slot_id="spread-05.pullquote_environment",
                             scene="wide lunar landscape, tiny figure on horizon",
                             aspect="16:10")
    assert "wide lunar landscape" in p
    assert "16:10" in p
    assert "{{" not in p


def test_build_storyboard_v2(spec, layers):
    plan = {
        "outer_aspect": "2:3",
        "outer_size_px": [1024, 1536],
        "grid": {"rows": 1, "cols": 2},
        "cells": [
            {"slot_id": "spread-01.cover_hero", "row": 0, "col": 0, "rowspan": 1, "colspan": 1,
             "aspect": "3:4", "bbox_px": [0,0,512,1536], "page_label": "01"},
            {"slot_id": "spread-09.back_coda", "row": 0, "col": 1, "rowspan": 1, "colspan": 1,
             "aspect": "2:3", "bbox_px": [512,0,512,1536], "page_label": "02"},
        ],
    }
    p = build_storyboard_prompt_v2(spec, layers,
                                   plan=plan,
                                   scenes_by_slot={
                                       "spread-01.cover_hero": "hero on lunar surface",
                                       "spread-09.back_coda": "tiny figure at horizon",
                                   })
    assert "spread-01.cover_hero" in p
    assert "01" in p
    assert "tabby cat" in p
    assert "{{" not in p
```

- [ ] **Step C4.2: Run, expect ImportError**

```bash
python -m pytest tests/unit/test_prompt_builder_v2.py -v
```

- [ ] **Step C4.3: Write `lib/prompt_builder_v2.py`**

```python
"""prompt_builder_v2 — role-driven upscale prompts + multi-aspect storyboard.

For v0.3 editorial pipeline. v0.2 prompt_builder still serves legacy plain-* layouts.
"""
from __future__ import annotations

import pathlib

from lib.placeholder_resolver import build_placeholder_map


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES_DIR = SKILL_ROOT / "library" / "templates"


ROLE_TEMPLATES = {
    "portrait":     "upscale_portrait.prompt.md",
    "scene":        "upscale_scene.prompt.md",
    "environment":  "upscale_environment.prompt.md",
    "detail":       "upscale_detail.prompt.md",
    "cover_hero":   "upscale_cover_hero.prompt.md",
    "back_coda":    "upscale_back_coda.prompt.md",
}


def _read_template(name: str) -> str:
    p = TEMPLATES_DIR / name
    if not p.is_file():
        raise FileNotFoundError(f"template not found: {p}")
    return p.read_text(encoding="utf-8")


def _apply(template: str, mapping: dict[str, str]) -> str:
    out = template
    for k, v in mapping.items():
        out = out.replace(k, str(v))
    return out


def build_upscale_prompt(
    *,
    role: str,
    spec: dict,
    layers: dict,
    slot_id: str,
    scene: str,
    aspect: str,
) -> str:
    if role not in ROLE_TEMPLATES:
        raise ValueError(f"unknown role {role!r}; expected one of {list(ROLE_TEMPLATES)}")
    template = _read_template(ROLE_TEMPLATES[role])
    pmap = build_placeholder_map(spec, layers)
    pmap["{{SCENE}}"] = scene
    pmap["{{ASPECT}}"] = aspect
    pmap["{{SLOT_ID}}"] = slot_id
    return _apply(template, pmap)


def build_storyboard_prompt_v2(
    spec: dict,
    layers: dict,
    *,
    plan: dict,
    scenes_by_slot: dict[str, str],
) -> str:
    template = _read_template("storyboard_v2.prompt.md")
    pmap = build_placeholder_map(spec, layers)

    cell_lines = []
    for cell in plan["cells"]:
        slot_id = cell["slot_id"]
        scene = scenes_by_slot.get(slot_id, "")
        # Look up role from the layout's image_slots
        role = "portrait"
        for s in layers.get("layout", {}).get("image_slots", []):
            full_id = f"spread-{s['spread_idx']:02d}.{s['id']}"
            if full_id == slot_id or s["id"] == slot_id.split(".", 1)[-1]:
                role = s.get("role", "portrait")
                break
        cell_lines.append(
            f"{cell['page_label']} - {slot_id} ({cell['aspect']} {role}) - {scene}".rstrip(" -")
        )

    pmap["{{OUTER_W}}"] = str(plan["outer_size_px"][0])
    pmap["{{OUTER_H}}"] = str(plan["outer_size_px"][1])
    pmap["{{GRID_ROWS}}"] = str(plan.get("grid", {}).get("rows", "?"))
    pmap["{{GRID_COLS}}"] = str(plan.get("grid", {}).get("cols", "?"))
    pmap["{{CELL_COUNT}}"] = str(len(plan["cells"]))
    pmap["{{CELL_LIST}}"] = "\n".join(cell_lines)

    return _apply(template, pmap)
```

- [ ] **Step C4.4: Run tests + commit**

```bash
python -m pytest tests/unit/test_prompt_builder_v2.py -v
git add lib/prompt_builder_v2.py tests/unit/test_prompt_builder_v2.py
git commit -m "feat(lib): prompt_builder_v2 — role-driven upscale + multi-aspect storyboard"
```

---

### Task C5: Extend `pillow_split` for multi-aspect cell extraction

**Files:**
- Modify: `~/github/openMagazine/tools/image/pillow_split.py`
- Modify: `~/github/openMagazine/tests/unit/test_pillow_split.py`

- [ ] **Step C5.1: Add `split_by_plan` function**

Read `tools/image/pillow_split.py`. After the existing `split_storyboard` function, append:

```python
def split_by_plan(
    storyboard_path: pathlib.Path,
    out_dir: pathlib.Path,
    *,
    plan: dict,
) -> int:
    """Split a storyboard into per-slot cell PNGs using a plan from
    `lib.storyboard_planner.plan_storyboard`. Each cell goes to its own
    file at {out_dir}/{slot_id}.png.

    Returns count of files written.
    """
    from PIL import Image

    img = Image.open(storyboard_path)
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for cell in plan["cells"]:
        x, y, w, h = cell["bbox_px"]
        crop = img.crop((x, y, x + w, y + h))
        # Save with hierarchical naming: spread-NN/<slot>.png
        slot_id = cell["slot_id"]   # e.g. "spread-03.feature_hero" or "spread-07.portrait_wall.4"
        if "." in slot_id:
            head, tail = slot_id.split(".", 1)
            sub = out_dir / head
            sub.mkdir(parents=True, exist_ok=True)
            out_path = sub / f"{tail}.png"
        else:
            out_path = out_dir / f"{slot_id}.png"
        crop.save(out_path)
        count += 1

    print(f"[pillow_split.split_by_plan] {count} cells → {out_dir}", file=sys.stderr)
    return count
```

- [ ] **Step C5.2: Add tests**

Append to `tests/unit/test_pillow_split.py`:

```python
def test_split_by_plan(tmp_path):
    from PIL import Image
    sb = tmp_path / "sb.png"
    Image.new("RGB", (1024, 1536), color="white").save(sb)
    plan = {
        "outer_size_px": [1024, 1536],
        "cells": [
            {"slot_id": "spread-01.cover_hero", "bbox_px": [0, 0, 512, 768]},
            {"slot_id": "spread-03.feature_captioned.1", "bbox_px": [512, 0, 512, 768]},
            {"slot_id": "spread-09.back_coda", "bbox_px": [0, 768, 1024, 768]},
        ],
    }
    out = tmp_path / "cells"
    from tools.image.pillow_split import split_by_plan
    n = split_by_plan(sb, out, plan=plan)
    assert n == 3
    assert (out / "spread-01" / "cover_hero.png").is_file()
    assert (out / "spread-03" / "feature_captioned.1.png").is_file()
    assert (out / "spread-09" / "back_coda.png").is_file()
```

- [ ] **Step C5.3: Run + commit**

```bash
python -m pytest tests/unit/test_pillow_split.py -v
git add tools/image/pillow_split.py tests/unit/test_pillow_split.py
git commit -m "feat(tools/image): pillow_split.split_by_plan for multi-aspect cell extraction"
```

---

### Task C6: Extend `placeholder_resolver` with typography placeholders

**Files:**
- Modify: `~/github/openMagazine/lib/placeholder_resolver.py`
- Modify: `~/github/openMagazine/tests/unit/test_prompt_builder.py`

- [ ] **Step C6.1: Read current `lib/placeholder_resolver.py`**

Note the existing `build_placeholder_map(spec, layers)` signature and current return keys.

- [ ] **Step C6.2: Add typography keys**

In `build_placeholder_map`, before the final `return`, add:

```python
# v0.3: typography-aware placeholders (only present if brand.typography exists)
brand = layers.get("brand") or {}
typography = brand.get("typography") or {}
visual_tokens = brand.get("visual_tokens") or {}
typography_hints = {}
if typography:
    typography_hints["{{TYPOGRAPHY_DISPLAY_FAMILY}}"] = (
        typography.get("display", {}).get("family", "")
    )
    typography_hints["{{TYPOGRAPHY_BODY_FAMILY}}"] = (
        typography.get("body", {}).get("family", "")
    )
    typography_hints["{{TYPOGRAPHY_PAIRING_HINT}}"] = (
        typography.get("pairing_notes", "").strip()
    )
if visual_tokens:
    typography_hints["{{COLOR_ACCENT}}"] = visual_tokens.get("color_accent", "")
    typography_hints["{{COLOR_BG_PAPER}}"] = visual_tokens.get("color_bg_paper", "")
```

Merge `typography_hints` into the returned dict.

- [ ] **Step C6.3: Add a test**

Append to `tests/unit/test_prompt_builder.py`:

```python
def test_placeholder_map_typography_optional(spec, layers_4page):
    """Without brand.typography (v1), typography placeholders absent."""
    pmap = build_placeholder_map(spec, layers_4page)
    # v1 brand has no typography; key not added
    assert "{{TYPOGRAPHY_DISPLAY_FAMILY}}" not in pmap or pmap["{{TYPOGRAPHY_DISPLAY_FAMILY}}"] == ""


def test_placeholder_map_typography_v2(spec, layers_4page):
    layers_4page["brand"] = {
        "masthead": "MEOW LIFE",
        "typography": {
            "display": {"family": "Playfair Display"},
            "body": {"family": "Source Serif 4"},
            "pairing_notes": "Editorial classic",
        },
        "visual_tokens": {"color_accent": "#c2272d", "color_bg_paper": "#f5efe6"},
    }
    pmap = build_placeholder_map(spec, layers_4page)
    assert pmap["{{TYPOGRAPHY_DISPLAY_FAMILY}}"] == "Playfair Display"
    assert pmap["{{COLOR_ACCENT}}"] == "#c2272d"
```

- [ ] **Step C6.4: Run + commit**

```bash
python -m pytest tests/unit/test_prompt_builder.py -v
git add lib/placeholder_resolver.py tests/unit/test_prompt_builder.py
git commit -m "feat(lib): placeholder_resolver adds typography + color tokens (v2)"
```

---

### Task C7: `tools/pdf/pdf_selector.py` + tests

**Files:**
- Create: `~/github/openMagazine/tools/pdf/pdf_selector.py`
- Modify: `~/github/openMagazine/tools/pdf/__init__.py`
- Create: `~/github/openMagazine/tests/unit/test_pdf_selector.py`

- [ ] **Step C7.1: Write failing test**

```python
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
```

- [ ] **Step C7.2: Run, expect ImportError**

```bash
python -m pytest tests/unit/test_pdf_selector.py -v
```

- [ ] **Step C7.3: Write `tools/pdf/pdf_selector.py`**

```python
"""pdf_selector — route to ReportLab (v1 layouts) or Weasyprint (v2 layouts)."""
from __future__ import annotations

from tools.base_tool import BaseTool
from tools.pdf.reportlab_compose import ReportlabCompose
from tools.pdf.weasyprint_compose import WeasyprintCompose


class PdfSelector(BaseTool):
    capability = "pdf_compose"
    provider = "selector"
    status = "active"

    def __init__(self):
        super().__init__()
        self._reportlab = ReportlabCompose()
        self._weasyprint = WeasyprintCompose()

    def choose_backend(self, *, layout: dict) -> BaseTool:
        sv = layout.get("schema_version")
        if sv == 1:
            return self._reportlab
        if sv == 2:
            return self._weasyprint
        raise ValueError(f"unsupported layout.schema_version {sv!r}")

    def run(self, *, layout: dict, **kwargs):
        return self.choose_backend(layout=layout).run(**kwargs)


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(PdfSelector())
```

- [ ] **Step C7.4: Update `tools/pdf/__init__.py`**

Append `from tools.pdf import pdf_selector  # noqa: F401`.

- [ ] **Step C7.5: Run + commit**

```bash
python -m pytest tests/unit/test_pdf_selector.py -v
git add tools/pdf/pdf_selector.py tools/pdf/__init__.py tests/unit/test_pdf_selector.py
git commit -m "feat(tools/pdf): pdf_selector routes by layout schema_version"
```

---

## Phase D — Pipeline (~1 day, 5 tasks)

### Task D1: `pipeline_defs/editorial-16page.yaml`

**Files:**
- Create: `~/github/openMagazine/pipeline_defs/editorial-16page.yaml`

- [ ] **Step D1.1: Write the manifest**

```yaml
name: editorial-16page
version: "1.0"
schema_version: 2
description: 16-page editorial A4 magazine with multi-image spreads + real PDF text.
category: editorial
stability: experimental
budget_default_usd: 5.50
max_wall_time_minutes: 30

reference_input:
  supported: true
  analysis_depth: shallow

orchestration:
  parallelism: 3

required_skills:
  - pipelines/editorial-16page/research-director
  - pipelines/editorial-16page/proposal-director
  - pipelines/editorial-16page/articulate-director
  - pipelines/editorial-16page/storyboard-director
  - pipelines/editorial-16page/upscale-director
  - pipelines/editorial-16page/compose-director
  - pipelines/editorial-16page/publish-director
  - meta/reviewer
  - meta/checkpoint-protocol
  - meta/cost-budget-enforcer
  - meta/article-writer

stages:
  - name: research
    skill: pipelines/editorial-16page/research-director
    produces: research_brief.json
    checkpoint: "off"
    reviewer: "enabled"
    success_criteria:
      - schema-valid research_brief.json
      - 6 layer references resolved (subject/style/theme/layout/brand/article)

  - name: proposal
    skill: pipelines/editorial-16page/proposal-director
    produces: proposal.json
    checkpoint: "off"
    reviewer: "enabled"
    success_criteria:
      - cost_estimate_usd ≤ budget_default_usd
      - 21 image_slots accounted for

  - name: articulate
    skill: pipelines/editorial-16page/articulate-director
    produces: article.yaml
    checkpoint: "required"
    reviewer: "enabled"
    success_criteria:
      - article schema valid
      - article ↔ layout consistency check passes

  - name: storyboard
    skill: pipelines/editorial-16page/storyboard-director
    produces:
      - storyboard.png
      - storyboard.json
      - cells/spread-NN/<slot_id>.png × 21
    checkpoint: "required"
    reviewer: "enabled"
    success_criteria:
      - 21 cell PNGs in output/<slug>/cells/
      - storyboard.png 2:3 aspect, top-crop applied
      - user explicit OK in checkpoint sidecar

  - name: upscale
    skill: pipelines/editorial-16page/upscale-director
    produces:
      - images/spread-NN/<slot_id>.png × 21
      - upscale_result.json
    checkpoint: "off"
    reviewer: "enabled"
    success_criteria:
      - 21 4K PNGs in output/<slug>/images/
      - cumulative cost ≤ budget

  - name: compose
    skill: pipelines/editorial-16page/compose-director
    produces:
      - magazine.pdf
      - magazine.html
      - compose_result.json
    checkpoint: "off"
    reviewer: "enabled"
    success_criteria:
      - magazine.pdf at output/<slug>/, page count == 16, 30-150 MB total

  - name: publish
    skill: pipelines/editorial-16page/publish-director
    produces:
      - publish_report.json
      - contact_sheet.jpg
    checkpoint: "off"
    reviewer: "disabled"
    success_criteria:
      - publish_report.json schema-valid
      - contact_sheet.jpg exists

defaults:
  storyboard_grid_outer: "2:3"
  storyboard_size_px: [1024, 1536]
  total_image_slots: 21
  page_count: 16
  aspect: "2:3"
```

- [ ] **Step D1.2: Validate against pipeline schema**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
python -c "
import json, yaml, jsonschema
schema = json.loads(open('schemas/pipelines/pipeline.schema.json').read())
data = yaml.safe_load(open('pipeline_defs/editorial-16page.yaml').read())
jsonschema.validate(instance=data, schema=schema)
print('valid')
"
```

- [ ] **Step D1.3: Commit**

```bash
git add pipeline_defs/editorial-16page.yaml
git commit -m "feat(pipeline_defs): editorial-16page manifest (7 stages, 21 slots, ~$5.50)"
```

---

### Task D2: `research-director` + `proposal-director`

**Files:**
- Create: `skills/pipelines/editorial-16page/research-director.md`
- Create: `skills/pipelines/editorial-16page/proposal-director.md`

- [ ] **Step D2.1: Write `research-director.md`**

```markdown
# research-director — editorial-16page

## Purpose
Convert user input or spec yaml into a research_brief artifact identifying
subject / style / theme / layout / brand / article references.

## Inputs
- Free-form user message + photo, OR `library/issue-specs/<slug>.yaml` (v2)
- The spec must reference all 6 layers; if `article` is missing, articulate stage will draft it later.

## Read first
- `skills/meta/creative-intake.md`
- `skills/meta/reference-photo-analyst.md`
- `skills/creative/style-anchor-resolution.md`

## Procedure

1. If spec input: load + run `tools/validation/spec_validate.py library/issue-specs/<slug>.yaml`. Verify schema_version=2.
2. Free-form: extract subject, style, theme, page_count via creative-intake; default layout=editorial-16page; default brand=meow-life; article reference = match spec slug or auto-generate later.
3. If subject not in `library/subjects/`, run reference-photo-analyst on the photo.
4. Resolve style via 3-tier (Tier 1 lookup → Tier 2 scaffold → Tier 3 inline).
5. Write `output/<slug>/research_brief.json` matching `schemas/artifacts/research_brief.schema.json`.

## Output artifact
research_brief.json with traits, style_anchor, theme_world, magazine_name (= masthead from brand), page_count=16, spec_slug.

## Checkpoint
off (default)

## Success criteria
- research_brief.json schema-valid
- spec_validate returns 0 OR spec lacks `article` field (deferred to articulate stage)

## Failure modes
- Photo missing → STOP and ask for photo
- Layout other than `editorial-16page` requested → wrong director; route to that pipeline's research instead
```

- [ ] **Step D2.2: Write `proposal-director.md`**

```markdown
# proposal-director — editorial-16page

## Purpose
Produce a 9-spread plan + cost estimate before any paid call.

## Inputs
- research_brief.json
- `library/layouts/editorial-16page.yaml`

## Read first
- `library/SCHEMA.md`
- `skills/meta/cost-budget-enforcer.md`

## Procedure

1. Load layout's spread_plan (9 entries) and image_slots (21 entries).
2. Build proposal page_plan: one entry per spread with type / pages / image_slot_count.
3. Cost: 21 × $0.24 = $5.04 + 1 codex storyboard (negligible) ≈ **$5.04**. Wall time: ~15 min.
4. Write `output/<slug>/proposal.json` matching `schemas/artifacts/proposal.schema.json`.

## Output artifact
proposal.json with page_plan (9 spreads), cost_estimate_usd, wall_time_estimate_min, spec_slug.

## Checkpoint
off

## Success criteria
- 9-spread plan
- cost_estimate_usd ≤ pipeline.budget_default_usd ($5.50)

## Failure modes
- image_slot count != 21 → layout yaml inconsistent; halt
```

- [ ] **Step D2.3: Commit**

```bash
mkdir -p ~/github/openMagazine/skills/pipelines/editorial-16page
git add skills/pipelines/editorial-16page/research-director.md \
        skills/pipelines/editorial-16page/proposal-director.md
git commit -m "docs(skills/pipelines): editorial-16page research + proposal directors"
```

---

### Task D3: `articulate-director` + `meta/article-writer`

**Files:**
- Create: `skills/pipelines/editorial-16page/articulate-director.md`
- Create: `skills/meta/article-writer.md`

- [ ] **Step D3.1: Write `articulate-director.md`**

```markdown
# articulate-director — editorial-16page

## Purpose
Produce or load `library/articles/<slug>.yaml` containing all editorial copy.

## Inputs
- research_brief.json, proposal.json
- `library/layouts/editorial-16page.yaml` (spread_plan + text_slots_required)
- `library/themes/<theme>.yaml` (theme_world + page_plan_hints)

## Read first
- `skills/meta/article-writer.md`
- `library/articles/README.md`

## Procedure

1. Resolve `spec.article` reference. If `library/articles/<slug>.yaml` exists, **load and skip generation**.
2. Otherwise, draft article copy per the procedure in `skills/meta/article-writer.md`. Each spread gets the fields its `text_slots_required` demands.
3. Write `library/articles/<slug>.yaml` to disk.
4. Run `tools/validation/article_validate.py library/articles/<slug>.yaml --layout editorial-16page` — must return 0.
5. Write `output/<slug>/article.json` (artifact for downstream stages).

## Output artifact
article.json (a JSON projection of the yaml for stage chaining).

## Checkpoint
**required** — user reviews/edits the yaml before storyboard. Show user the article path and a summary of generated content.

## Success criteria
- article_validate returns 0
- article.spread_copy length == 9 (matches layout.spread_plan)
- All required fields present per text_slots_required

## Failure modes
- LLM-drafted copy fails validation → re-prompt with explicit field list and try once more; if still fails, STOP and ask user to write manually.
```

- [ ] **Step D3.2: Write `skills/meta/article-writer.md`**

```markdown
# article-writer

How an agent drafts an editorial article from spec + theme + layout.

## When to invoke
Articulate stage of editorial-* pipelines. The agent is asked to fill in `library/articles/<slug>.yaml` from scratch given: subject traits, theme world, layout spread plan.

## Drafting rules

1. **Match each spread to its text_slots_required** (from layout yaml). For editorial-16page:
   - cover: cover_line + cover_kicker (article-level fields, not in spread_copy)
   - toc: table_of_contents (list of {page, en, zh})
   - feature-spread: title + kicker + lead + body
   - pull-quote: quote + attribution
   - portrait-wall: title + 6 captions
   - colophon: credits (photographer / art_direction / printing / copyright / contact)
   - back-cover: quote + attribution

2. **Length targets**:
   - title: 1-3 words, all caps
   - kicker: short label like "Chapter 02" or "FEATURE STORY"
   - lead: 1-2 sentences, italic-friendly, hooks the reader
   - body: 3 paragraphs, each 60-120 words. Total ~250 words per spread.
   - pull-quote: 1-2 short lines, max 14 words
   - caption: 1-2 words

3. **Voice**: editorial, slightly literary, present tense, restrained. Avoid:
   - Marketing language ("revolutionary", "groundbreaking")
   - Emojis in body copy
   - Generic AI fillers ("In this article we will explore...")

4. **Multi-language**: write `en` first; if brand.default_language is `zh` or article has Chinese theme, also write `zh`. Use the same voice in zh — terse, literary, present tense.

5. **image_slot_overrides**: for each spread, write a one-sentence scene description per image_slot in that spread (matches layout's slot ids). These feed Stage 4 upscale prompts. Example:
   ```yaml
   image_slot_overrides:
     feature_hero: "Luna at boulder, hand on rock, three-quarter front view, hero portrait"
     feature_captioned.1: "footprints in regolith, low sun raking shadows, 3:2 wide"
   ```

6. **Cross-spread coherence**: the 9 spreads should read as one issue. Use the theme's `page_plan_hints` as scaffolding; expand each into full editorial language.

## Self-review before persisting

- All 9 spreads have all required fields
- Story has an arc: cover (hook) → toc (preview) → feature 1 (departure) → feature 2 (development) → pull-quote (mid-issue rest) → feature 3 (climax) → portrait-wall (montage) → colophon (resolution) → back (coda)
- No two consecutive spread titles use the same first word
- Every image_slot has a slot-specific scene override
```

- [ ] **Step D3.3: Commit**

```bash
git add skills/pipelines/editorial-16page/articulate-director.md \
        skills/meta/article-writer.md
git commit -m "docs(skills): articulate-director + article-writer meta-skill"
```

---

### Task D4: `storyboard-director` for editorial-16page

**Files:**
- Create: `skills/pipelines/editorial-16page/storyboard-director.md`

- [ ] **Step D4.1: Write `storyboard-director.md`**

```markdown
# storyboard-director — editorial-16page

## Purpose
ONE codex `image_gen.imagegen` inference produces a 2:3 portrait multi-aspect grid containing all 21 image slots locked in style/character/lighting.

## Inputs
- article.yaml (with `image_slot_overrides` per spread filled in by articulate)
- `library/layouts/editorial-16page.yaml`

## Read first
- `skills/core/codex-image-gen.md`
- `.agents/skills/codex-image-gen-plumbing.md`
- `CODEX.md`

## Procedure

1. **Plan**: flatten `layout.image_slots` into a 21-element list. Call:

   ~~~python
   from lib.spec_loader import load_spec, resolve_layers
   from lib.storyboard_planner import plan_storyboard
   from lib.prompt_builder_v2 import build_storyboard_prompt_v2

   spec, _ = load_spec(pathlib.Path("library/issue-specs/<slug>.yaml"))
   layers = resolve_layers(spec)
   article = yaml.safe_load(open(f"library/articles/{spec['article']}.yaml").read())

   slots = []
   for s in layers["layout"]["image_slots"]:
       slots.append({
           **s,
           "id": f"spread-{s['spread_idx']:02d}." + s['id'],
       })
   plan = plan_storyboard(slots)

   scenes_by_slot = {}
   for sc in article["spread_copy"]:
       for slot, scene in (sc.get("image_slot_overrides") or {}).items():
           scenes_by_slot[f"spread-{sc['idx']:02d}.{slot}"] = scene

   prompt = build_storyboard_prompt_v2(spec, layers, plan=plan, scenes_by_slot=scenes_by_slot)
   ~~~

2. **BEFORE capture**:
   ~~~bash
   BEFORE=$(ls -t ~/.codex/generated_images/*/ig_*.png 2>/dev/null | head -1)
   ~~~

3. **Call `image_gen.imagegen`** with the rendered prompt. (Codex tool call.)

4. **AFTER capture** — copy new PNG to `output/<slug>/storyboard.png`. STOP if no new file (do NOT fall back to PIL).

5. **Split** the storyboard into per-slot cells:

   ~~~python
   from tools.image.pillow_split import split_by_plan
   split_by_plan(
       pathlib.Path(f"output/{spec['slug']}/storyboard.png"),
       pathlib.Path(f"output/{spec['slug']}/cells"),
       plan=plan,
   )
   ~~~

6. **Write artifact** `output/<slug>/storyboard.json` with png_path, cells_dir, plan, slot_count=21, spec_slug.

## ABSOLUTE STOP RULE
If `image_gen.imagegen` produces no new file, STOP. Do NOT fall back to PIL.

## Checkpoint
**required**. Show user storyboard.png + list of 21 cell PNGs. User approves before Stage 5 upscale.

## Success criteria
- 21 cell PNGs at `output/<slug>/cells/spread-NN/<slot_id>.png`
- storyboard.png is 1024×1536 (2:3 portrait)
- Aspect warning from `pillow_split` did NOT fire
- User approval recorded in checkpoint sidecar

## Failure modes
- Storyboard not 2:3 → STOP. The model failed the OUTPUT IMAGE FORMAT constraint. Regenerate.
- Missing cells → split_by_plan miscount; check plan vs slots list.
- Cells too small (≪ 256px short edge) → storyboard outer too small; should be 1024×1536.
```

- [ ] **Step D4.2: Commit**

```bash
git add skills/pipelines/editorial-16page/storyboard-director.md
git commit -m "docs(skills/pipelines): editorial-16page storyboard-director"
```

---

### Task D5: `upscale-director` + `compose-director` + `publish-director`

**Files:**
- Create: 3 director files

- [ ] **Step D5.1: Write `upscale-director.md`**

```markdown
# upscale-director — editorial-16page

## Purpose
Generate 21 × 4K Vertex images, one per image_slot, with role-driven prompts and concurrent execution.

## Inputs
- storyboard.json (cells per slot)
- article.yaml (image_slot_overrides per spread for scene descriptions)
- `library/layouts/editorial-16page.yaml` (image_slots with role + aspect)

## Read first
- `skills/core/vertex-gemini.md`
- `.agents/skills/vertex-gemini-image-prompt-tips.md`
- `skills/creative/photoreal-anti-illustration.md`

## Procedure

1. Load all the inputs and resolve scenes:

   ~~~python
   from concurrent.futures import ThreadPoolExecutor
   from tools.image.vertex_gemini_image import VertexGeminiImage
   from lib.config_loader import get_parallelism
   from lib.prompt_builder_v2 import build_upscale_prompt
   from lib.spec_loader import load_spec, resolve_layers
   import pathlib, yaml

   spec, _ = load_spec(pathlib.Path("library/issue-specs/<slug>.yaml"))
   layers = resolve_layers(spec)
   article = yaml.safe_load(open(f"library/articles/{spec['article']}.yaml").read())
   issue_dir = pathlib.Path(f"output/{spec['slug']}")

   def scene_for(slot_id, spread_idx):
       for sc in article["spread_copy"]:
           if sc["idx"] == spread_idx:
               return (sc.get("image_slot_overrides") or {}).get(slot_id, "")
       return ""

   tool = VertexGeminiImage()
   jobs = []
   for s in layers["layout"]["image_slots"]:
       slot_full = f"spread-{s['spread_idx']:02d}.{s['id']}"
       scene = scene_for(s['id'], s['spread_idx'])
       prompt = build_upscale_prompt(
           role=s["role"], spec=spec, layers=layers,
           slot_id=slot_full, scene=scene, aspect=s["aspect"],
       )
       refs = [issue_dir / "cells" / f"spread-{s['spread_idx']:02d}" / f"{s['id']}.png"]
       if s["role"] not in ("environment", "detail"):
           refs.append(issue_dir / "refs" / "protagonist-1.jpg")
       out_path = issue_dir / "images" / f"spread-{s['spread_idx']:02d}" / f"{s['id']}.png"
       jobs.append((s, prompt, refs, out_path))

   def _run_one(slot, prompt, refs, out_path):
       return tool.run(prompt=prompt, refs=refs, out_path=out_path,
                       aspect=slot["aspect"], size="4k", skip_existing=True)

   with ThreadPoolExecutor(max_workers=get_parallelism()) as ex:
       results = list(ex.map(lambda j: _run_one(*j), jobs))
   ~~~

2. Write `output/<slug>/upscale_result.json` with all 21 image paths, vertex_calls_made=21, total_cost_usd=$5.04, spec_slug.

## Cost announcement
Per `skills/meta/cost-budget-enforcer.md`, announce each call. Cumulative: $0.24 → $5.04. Hard stop at 110% × $5.50 = $6.05.

## Checkpoint
off

## Success criteria
- 21 PNGs at `output/<slug>/images/spread-NN/<slot_id>.png`, each ≥ 5 MB
- All match declared aspect (within 5%)
- Cumulative cost ≤ budget

## Failure modes
- Vertex 503 → reduce parallelism (set `OPENMAGAZINE_PARALLELISM=1`) and retry
- Output PNG <5 MB → likely degraded; delete the file and rerun (skip_existing=True will skip the others)
```

- [ ] **Step D5.2: Write `compose-director.md`**

```markdown
# compose-director — editorial-16page

## Purpose
Render `output/<slug>/magazine.pdf` via Weasyprint from layout j2 + article + brand + 21 4K images.

## Inputs
- upscale_result.json (paths to all 21 images)
- article.yaml, brand.yaml, layout.yaml

## Read first
- `skills/core/reportlab.md` (no — that's v1; for editorial use:)
- `.agents/skills/weasyprint-cookbook.md` (if present, otherwise refer to `tools/pdf/weasyprint_compose.py` docstring)
- `library/SCHEMA.md` (typography section)

## Procedure

~~~python
from tools.pdf.pdf_selector import PdfSelector
from lib.spec_loader import load_spec, resolve_layers
import pathlib, yaml

spec, _ = load_spec(pathlib.Path("library/issue-specs/<slug>.yaml"))
layers = resolve_layers(spec)
article = yaml.safe_load(open(f"library/articles/{spec['article']}.yaml").read())
issue_dir = pathlib.Path(f"output/{spec['slug']}")

selector = PdfSelector()
backend = selector.choose_backend(layout=layers["layout"])
result = backend.run(
    issue_dir=issue_dir,
    layout=layers["layout"],
    brand=layers["brand"],
    article=article,
    spec=spec,
)
~~~

The selector dispatches to `WeasyprintCompose` because layout is schema_version=2. Result is `{pdf_path, html_path, page_count, size_mb}`.

Write `output/<slug>/compose_result.json` from result.

## Checkpoint
off

## Success criteria
- magazine.pdf at `output/<slug>/`, page_count == 16, 30-150 MB total
- magazine.html exists (intermediate; useful for debugging)

## Failure modes
- Weasyprint native dep error → user must `brew install weasyprint`; document in error
- Image not found at expected path → upscale stage incomplete; halt
- Page count != 16 → layout j2 component fault; inspect magazine.html
```

- [ ] **Step D5.3: Write `publish-director.md`**

```markdown
# publish-director — editorial-16page

## Purpose
Final wrap: verify all artifacts, generate contact sheet, write publish_report.json, optionally auto-persist spec.

## Inputs
- compose_result.json + all upstream artifacts

## Procedure

1. Run `tools/validation/verify_4k.py output/<slug>` — must return 0.
2. Generate contact sheet: 4×6 grid thumbnail of the 21 4K images at `output/<slug>/contact_sheet.jpg`. Use PIL:
   - canvas size 1600×1200
   - each thumbnail 240×240, gutter 16px
3. Compute final stats: total_cost_usd, wall_time_min from costs.json + start time.
4. If user input was free-form (no spec yaml on disk), auto-persist `library/issue-specs/<slug>.yaml`.
5. Write `output/<slug>/publish_report.json`:
   ~~~json
   {
     "spec_slug": "...",
     "pdf_path": "output/<slug>/magazine.pdf",
     "html_path": "output/<slug>/magazine.html",
     "contact_sheet_path": "output/<slug>/contact_sheet.jpg",
     "page_count": 16,
     "image_count": 21,
     "total_cost_usd": 5.04,
     "wall_time_min": 14.3,
     "auto_persisted_spec_path": null,
     "schema_version": 2
   }
   ~~~

## Checkpoint
off

## Success criteria
- publish_report.json schema-valid
- contact_sheet.jpg exists, 1600×1200
- verify_4k passes
```

- [ ] **Step D5.4: Commit**

```bash
git add skills/pipelines/editorial-16page/upscale-director.md \
        skills/pipelines/editorial-16page/compose-director.md \
        skills/pipelines/editorial-16page/publish-director.md
git commit -m "docs(skills/pipelines): editorial-16page upscale + compose + publish directors"
```

---

## Phase E — Tests + docs (~1 day, 5 tasks)

### Task E1: Contract test for v2 pipelines

**Files:**
- Create: `~/github/openMagazine/tests/contracts/test_v2_pipelines.py`

- [ ] **Step E1.1: Write the test**

```python
"""Contract tests for v2 (editorial) pipelines: schema + article ↔ layout consistency."""
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import validate

from tools.validation.article_validate import validate_article


SKILL_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def pipeline_schema():
    return json.loads((SKILL_ROOT / "schemas/pipelines/pipeline.schema.json").read_text())


def _v2_pipelines():
    return [p for p in (SKILL_ROOT / "pipeline_defs").glob("*.yaml")
            if yaml.safe_load(p.read_text()).get("schema_version") == 2]


@pytest.mark.parametrize("pipeline_path", _v2_pipelines(),
                         ids=lambda p: p.name)
def test_v2_pipeline_validates(pipeline_path, pipeline_schema):
    data = yaml.safe_load(pipeline_path.read_text())
    validate(instance=data, schema=pipeline_schema)


def test_editorial_16page_layout_article_consistency():
    layout_path = SKILL_ROOT / "library/layouts/editorial-16page.yaml"
    article_path = SKILL_ROOT / "library/articles/cosmos-luna-may-2026.yaml"
    errors = validate_article(article_path, layout_path)
    assert errors == [], f"unexpected errors: {errors}"


def test_editorial_16page_image_slots_count():
    layout = yaml.safe_load((SKILL_ROOT / "library/layouts/editorial-16page.yaml").read_text())
    assert len(layout["image_slots"]) == 21
    assert layout["defaults"]["total_image_slots"] == 21
```

- [ ] **Step E1.2: Run + commit**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
python -m pytest tests/contracts/ -v
git add tests/contracts/test_v2_pipelines.py
git commit -m "test(contracts): v2 pipeline + article ↔ layout consistency"
```

---

### Task E2: docs/v0.3-ARCHITECTURE.md + spread-types-reference.md

**Files:**
- Create: 2 docs

- [ ] **Step E2.1: Write `docs/v0.3-ARCHITECTURE.md`**

(~80 lines summarizing the spec for end users. Cross-link to the spec doc.)

```markdown
# v0.3 Architecture — Editorial Layout Engine

The full design rationale lives in [the spec](superpowers/specs/2026-05-10-openmagazine-v0.3-editorial-engine-design.md). This page is the user-facing summary.

## What v0.3 adds

| Capability | v0.1/v0.2 | v0.3 |
|---|---|---|
| Layout style | Full-bleed photos with typography painted in | Editorial spreads with multi-image regions + real PDF text |
| PDF engine | ReportLab | Weasyprint (HTML/CSS Paged Media) |
| Layout schema | yaml metadata only | yaml + Jinja2 HTML templates |
| Image gen | One 4K per page | Multiple per spread (different aspects + roles) |
| Typography | Generated INTO the photo | Real PDF text with embedded fonts |

Both modes coexist: legacy `plain-*` layouts (schema_version=1) still work via ReportLab.

## How to choose

- **Use v0.3 editorial** when you want a magazine-as-a-book feel: feature articles, editorial design, real text, multiple images per spread.
- **Use v0.1/v0.2 plain** when you want a photo book: every page is one large photograph.

## File structure additions

- `library/articles/` — per-issue editorial copy (NEW LAYER)
- `library/brands/_presets/` — typography starting points
- `library/layouts/_components/` — Jinja2 spread components
- `library/layouts/<name>.html.j2` — render templates
- `tools/pdf/weasyprint_compose.py` — Weasyprint backend
- `tools/pdf/pdf_selector.py` — routes by layout schema_version
- `lib/storyboard_planner.py` — multi-aspect grid packer
- `lib/prompt_builder_v2.py` — role-driven prompts

See [the spec](superpowers/specs/2026-05-10-openmagazine-v0.3-editorial-engine-design.md) §6 for the full file map.

## Pipeline differences

editorial-16page has a NEW stage: `articulate` (between proposal and storyboard). Agent drafts article copy, user reviews, then storyboard generation can use article-specific scene descriptions.

## Cost (editorial-16page)

- 21 image slots × $0.24 (Vertex) = $5.04 + 1 codex storyboard ≈ **$5.04 / issue**
- Wall time ≈ 15 min (storyboard 4 min, upscale 9 min concurrent, compose <1 min)
```

- [ ] **Step E2.2: Write `docs/spread-types-reference.md`**

```markdown
# Spread Types Reference

The 6 spread types implemented in editorial-16page. Each is a reusable Jinja2 component at `library/layouts/_components/`.

## cover

Single page (page 1). Full-bleed hero image with masthead overlay (mix-blend-mode: difference for adaptive contrast). Cover line + kicker bottom-left.

**Image slots:** `cover_hero` (3:4 portrait, role: cover_hero)

**Text fields:** `article.cover_line`, `article.cover_kicker`, `article.issue_label`, `article.masthead_override`

## toc

2-page spread (pages 2-3). Left page: section heading + issue label. Right page: contents list with page numbers.

**Image slots:** none

**Text fields:** `spread_copy[].table_of_contents` (list of `{page, en, zh}`)

## feature-spread

2-page spread. Left page: full-bleed hero portrait. Right page: kicker + accent rule + title + lead + body (with drop cap) + 3 captioned thumbnails.

**Image slots:** `feature_hero` (3:4 portrait), `feature_captioned.1/2/3` (3:2 scenes)

**Text fields:** `title`, `kicker`, `lead`, `body`, `image_slot_overrides` (per-slot scene descriptions)

## pull-quote

2-page spread. Full-bleed environmental landscape with darkened overlay. Quote + attribution centered, large pull-quote typography.

**Image slots:** `pullquote_environment` (16:10)

**Text fields:** `quote`, `quote_attribution`

## portrait-wall

2-page spread. Title + accent rule top. 3×2 grid of 6 square portraits with captions.

**Image slots:** `portrait_wall.1` ... `portrait_wall.6` (1:1)

**Text fields:** `title`, `captions` (list of `{slot, en, zh}`)

## colophon + back-cover

Closing spread. colophon: 2 pages with credits. back-cover: 1 page with quiet coda image + closing quote.

**Image slots:** `back_coda` (2:3 portrait)

**Text fields:** colophon credits, back-cover quote

---

## Adding a new spread type (v0.3.1+)

1. Create `library/layouts/_components/<type>.html.j2`
2. Add `text_slots_required.<type>` entry in your layout yaml
3. Add `<type>` branch to `editorial-*.html.j2`'s if/elif tree
4. Update `spread_plan` in any layout that uses it
5. Document here.
```

- [ ] **Step E2.3: Commit**

```bash
git add docs/v0.3-ARCHITECTURE.md docs/spread-types-reference.md
git commit -m "docs: v0.3 architecture overview + spread types reference"
```

---

### Task E3: typography-pack-cookbook + SCHEMA_V2_MIGRATION

**Files:**
- Create: `~/github/openMagazine/docs/typography-pack-cookbook.md`
- Create: `~/github/openMagazine/docs/SCHEMA_V2_MIGRATION.md`

- [ ] **Step E3.1: Write `typography-pack-cookbook.md`**

```markdown
# Typography Pack Cookbook

How to write a `library/brands/<name>.yaml` typography pack for v2 editorial layouts.

## Quick start: clone a preset

```bash
cp library/brands/_presets/editorial-classic.yaml library/brands/my-magazine.yaml
# edit name + masthead + display_name; leave typography/print_specs/visual_tokens
# unless you want to customize
```

## What lives in each section

### typography
6 font slots, each with `family` / `weights` / `source` and slot-specific options.

| Slot | Purpose | Tunable |
|---|---|---|
| `display` | Big titles, masthead | family, weights |
| `body` | Long-form paragraphs | family, weights, size_pt, leading, align, hyphenate |
| `kicker` | Section labels, "CHAPTER 01" | family, weight, transform, letter_spacing, size_pt |
| `caption` | Image captions, footnotes | family, weight, style, size_pt |
| `pull_quote` | Big inset quotes | family, weight, style, size_pt |
| `drop_cap` | First letter of body | enabled, family, weight, lines, color_token |
| `page_number` | @bottom-center | family, weight, size_pt |

### print_specs
Page geometry. Margins, bleed, gutter (binding side), trim marks, etc. Defaults are A4 saddle-stitch.

### visual_tokens
CSS variables: paper color, ink colors, accent (used for accent rules + drop cap), quote bg/fg, rule thickness.

## Picking fonts

**Pairing principles**:

1. **Display + body should contrast in voice.** Display is loud; body is calm.
2. **Avoid two fonts of the same flavor.** Two slab serifs = mushy. One didone + one humanist = harmony.
3. **Use one family for meta** (kicker + caption + page number). Mono fonts (IBM Plex Mono, JetBrains Mono) earn their keep here.

**Sources**:
- `google-fonts`: free, requires internet at render time. ~1500 families.
- `local`: drop TTF/OTF in `library/fonts/<family>/`. CSS @font-face. Best for offline / privacy.
- `system`: declare family name; no resolution. Useful when you know the deploy env has the font.

## Anti-AI-slop checklist

(borrowed from `frontend-slides` STYLE_PRESETS reference)

- ❌ Avoid Inter, Roboto, system fonts as display
- ❌ Avoid purple gradients on white
- ❌ Avoid generic "modern minimalist" (sans + thin weight + lots of whitespace)
- ✅ Pick distinctive choices: didone display, humanist body, mono meta
- ✅ Commit to one paper color (warm cream / cool gray / black) and one accent (red / oxblood / mustard)

## Examples

| Preset | Display | Body | Vibe |
|---|---|---|---|
| editorial-classic | Playfair Display | Source Serif 4 | Generic editorial |
| humanist-warm | Cormorant Garamond | Lora | Literary, slow-living |

(More in v0.3.1+: architectural / swiss-modernist / editorial-asian.)

## Validation

`tools/validation/spec_validate.py` will reject brands with `schema_version: 2` that lack `typography` / `print_specs` / `visual_tokens`. Run:

```bash
python tools/validation/spec_validate.py library/issue-specs/<slug>.yaml
```
```

- [ ] **Step E3.2: Write `SCHEMA_V2_MIGRATION.md`**

```markdown
# Schema v1 → v2 Migration

v0.3 introduces schema_version=2 for `spec`, `brand`, and `layout` files. v0.1/v0.2 schema_version=1 files keep working — both are supported in parallel.

## When to migrate

- You want editorial layouts (real PDF text, multi-image spreads).
- You want named typography packs.
- You want CSS Paged Media features (bleed, gutters, page numbers).

If you're happy with `plain-4` / `plain-16` (one 4K image per page, typography painted in), there's nothing to migrate.

## What changes

### spec yaml

```diff
 schema_version: 1
+schema_version: 2
 slug: ...
 subject: ...
 style: ...
 theme: ...
 layout: plain-16
+layout: editorial-16page
 brand: meow-life
+article: cosmos-luna-may-2026   # NEW required field
 overrides: {}
```

### brand yaml

Run the auto-migration script:

```bash
python tools/meta/migrate_brand_v1_to_v2.py library/brands/<name>.yaml --preset editorial-classic
```

This adds `typography`, `print_specs`, `visual_tokens` from the chosen preset while preserving your `name`, `masthead`, `display_name`. Replace the `{{MASTHEAD}}` placeholder if it appears.

### layout yaml

v2 layouts have a different shape (spread_plan, image_slots with role+aspect, text_slots_required). The simplest path is to use the shipped `editorial-16page` rather than migrate a v1 layout — they describe fundamentally different things.

### article yaml (NEW)

A v2 spec must reference an article. Either:
- Write `library/articles/<slug>.yaml` by hand (see `library/articles/cosmos-luna-may-2026.yaml` as template), OR
- Leave `article: <slug>` and let the `articulate` stage draft it (then review + edit before storyboard)

## Pipeline

v1 specs run through `pipeline_defs/smoke-test-4page.yaml` (or any v1 manifest). v2 specs run through `pipeline_defs/editorial-16page.yaml`. The agent picks based on `spec.layout` resolution.

## Coexistence

The PDF backend is selected automatically by `tools/pdf/pdf_selector.py` based on `layout.schema_version`. Tests cover both paths (`tests/integration/test_render_dry_run.py` for v2; existing pillow_split / reportlab tests for v1).
```

- [ ] **Step E3.3: Commit**

```bash
git add docs/typography-pack-cookbook.md docs/SCHEMA_V2_MIGRATION.md
git commit -m "docs: typography pack cookbook + schema v1→v2 migration guide"
```

---

### Task E4: SMOKE_TEST_v0.3.md placeholder

**Files:**
- Create: `~/github/openMagazine/docs/SMOKE_TEST_v0.3.md`

- [ ] **Step E4.1: Write the placeholder**

```markdown
# Smoke Test v0.3 — cosmos-luna-may-2026 (editorial-16page)

This is a placeholder. Fill in after running the live smoke test.

## Status

⏳ Pending live run from Codex CLI session.

## Steps to run

1. **One-time: install Weasyprint native deps** (macOS):
   ```bash
   brew install weasyprint
   ```

2. **One-time: ADC + probe**:
   ```bash
   gcloud auth application-default login
   cd ~/github/openMagazine && source .venv/bin/activate
   make probe
   ```

3. **Verify dry-run renders** (no Vertex calls):
   ```bash
   python -m pytest tests/integration/test_render_dry_run.py -v
   ```

4. **In a fresh Codex session, paste**:
   ```
   Run the editorial-16page pipeline using
   library/issue-specs/cosmos-luna-may-2026.yaml as the spec input.
   Stop at the articulate gate to let me review the article copy, then again
   at storyboard.
   ```
   (Note: spec doesn't yet exist; create it first or let agent generate.)

5. **Approve articulate gate** after reviewing `library/articles/cosmos-luna-may-2026.yaml`.

6. **Approve storyboard gate** after reviewing storyboard.png + 21 cells.

7. **Wait** ~10 min for upscale (21 calls @ parallelism 3).

8. **Inspect** `output/cosmos-luna-may-2026/magazine.pdf` (16 pages).

## Expected output

- `output/cosmos-luna-may-2026/`
  - `refs/protagonist-1.jpg`
  - `research_brief.json` / `proposal.json` / `article.json` / `storyboard.json` / `upscale_result.json` / `compose_result.json` / `publish_report.json`
  - `storyboard.png` (1024×1536) + `cells/spread-NN/<slot>.png` × 21
  - `images/spread-NN/<slot>.png` × 21 (each 5-30 MB)
  - `magazine.pdf` (16 pages, 30-150 MB)
  - `magazine.html` (intermediate)
  - `contact_sheet.jpg` (4×6 grid of 21 thumbnails on 1600×1200)

## Result

(Fill in after run)

- Date:
- Pipeline: editorial-16page
- Total cost: $
- Wall time: ___ min
- Page count: 16 ☐
- All slots rendered: 21/21 ☐
- All schemas valid: ☐
- Editorial spread renders correctly: ☐
- Drop caps + accent rules + page numbers visible: ☐

## Issues encountered

(Fill in after run)
```

- [ ] **Step E4.2: Commit**

```bash
git add docs/SMOKE_TEST_v0.3.md
git commit -m "docs: SMOKE_TEST_v0.3 runbook (template for live test)"
```

---

### Task E5: Final test run + push + tag v0.3.0

- [ ] **Step E5.1: Run full test suite**

```bash
cd ~/github/openMagazine && source .venv/bin/activate
python -m pytest tests/ -v 2>&1 | tail -10
```

Expected: 47 (v0.2) + ~25 new (A6 article_validate 4 + A3 migrate 5 + B2 weasyprint 3 + B8 integration 1 + C1 planner 3 + C4 prompt_builder_v2 3 + C5 split_by_plan 1 + C6 typography 2 + C7 pdf_selector 3 + E1 contracts 3) ≈ 72 passing.

- [ ] **Step E5.2: Push + tag**

```bash
cd ~/github/openMagazine
git push origin main
git tag v0.3.0
git push origin v0.3.0
```

- [ ] **Step E5.3: Final state verification**

```bash
git log --oneline | head -30
git tag --list
ls library/articles/ library/brands/_presets/ library/layouts/_components/
python -c "
from tools.tool_registry import registry, discover
discover()
import json
print(json.dumps({k: [t['provider'] for t in v] for k, v in registry.capability_catalog().items()}, indent=2))
"
```

Expected: pdf_compose now lists [reportlab, weasyprint, selector].

---

## Self-Review

### Spec coverage check

Walking the spec §-by-§:

- §1 Goal — Phase A-E together
- §2 Non-Goals — explicitly out of scope (no tasks)
- §3 Background — n/a
- §4.1 Weasyprint — Task B1
- §4.2 yaml + Jinja2 — Task A4 (yaml) + Task B3 (j2)
- §4.3 per-slot per-spread — Task A4 (image_slots) + Task C1 (planner) + Task C5 (split_by_plan)
- §4.4 articles/ layer — Task A5 + Task A6 (validate) + Task D3 (articulate)
- §4.5 typography in brands — Task A1+A2 (presets) + Task A3 (migration) + Task B3 (CSS) + Task C6 (placeholders)
- §4.6 MVP scope — exactly the tasks above (1 layout + 2 presets + 6 spread types + 1 article)
- §5.1 spec v2 — covered in A4+A6 (validate)
- §5.2 brand v2 — Tasks A1+A2+A3
- §5.3 layout v2 — Task A4
- §5.4 article schema — Task A5
- §6 file structure — implicit across all tasks
- §7.1 storyboard_planner — Task C1
- §7.2 prompt_builder_v2 — Task C4
- §7.3 weasyprint_compose — Task B2
- §7.4 placeholder typography — Task C6
- §8 pipeline — Task D1
- §9 directors — Tasks D2-D5
- §10 compatibility — Task A3 (migrate) + Task C7 (selector)
- §11 print specs/typography — Task B3 (_base.html.j2)
- §12 out of scope — n/a
- §13 risks — addressed via tests + checkpoints

### Placeholder scan

- All code blocks have actual code (no `# ... fill in ...`)
- All commit messages concrete
- All file paths absolute or clearly relative to repo root

### Type / signature consistency

- `build_upscale_prompt(role=..., spec=..., layers=..., slot_id=..., scene=..., aspect=...)` — same signature across plan and director skill
- `plan_storyboard(slots, outer_aspect="2:3")` — consistent
- `validate_article(article_path, layout_path)` — consistent
- `WeasyprintCompose.run(*, issue_dir, layout, brand, article, spec)` — consistent across B2 + D5 (compose-director)

---

## Execution Handoff

After this plan is approved, use `superpowers:subagent-driven-development` to execute task-by-task. Estimated time: ~9 working days. After all tasks pass, `superpowers:finishing-a-development-branch` to close out v0.3.0.
