# openMagazine v0.3 — Editorial Layout Engine Design

> **Status:** spec (brainstorm complete; awaiting user review before plan).
> **Date:** 2026-05-10
> **Predecessor:** v0.2.0 ([README](../../../README.md), [PROJECT_CONTEXT](../../../PROJECT_CONTEXT.md))
> **Subagents:** this spec consumed via `superpowers:brainstorming`. Next step is `superpowers:writing-plans` to produce a task-by-task plan.

## 1. Goal

Add a new pipeline branch — **editorial layout** — that produces real magazine spreads (multi-image regions + real PDF text + decorative elements) instead of v0.1/v0.2's "every page = one 4K full-bleed image with typography painted into the photo."

End-state visual target: a 16-page A4 portrait magazine with cover / TOC / 4 feature spreads / portrait wall / pull quote / colophon / back-cover. PDF has real selectable text, embedded fonts, bleed marks, gutter offset, page numbers.

## 2. Non-Goals (v0.3.0)

- Replacing v0.1/v0.2 `full-bleed` mode — both modes coexist (legacy schema_version=1 still works)
- More than 1 layout (`editorial-16page`); 4-page and 32-page editorial variants are v0.3.1+
- More than 2 brand presets; 5 presets total is v0.3.1+
- More than 6 spread types; 10+ types is v0.3.1+
- CMYK output (RGB only in v0.3.0)
- Bilingual side-by-side spreads (single language per issue)
- Web preview / EPUB / animated cover (v0.4+)

## 3. Background

### 3.1 What v0.1/v0.2 ships

- Pipeline: research → proposal → storyboard → upscale → compose → publish
- Each page = 1 × 4K Vertex Gemini 3 Pro Image at 2:3 portrait
- Typography (masthead / cover line / colophon) generated _inside_ the photograph by the model
- ReportLab compose just stamps each PNG full-bleed onto an A4 page
- 5-layer composition: subject × style × theme × layout × brand
- Schema v1 layouts have `typography_mode: full-bleed` as the only implemented mode

### 3.2 What this can't do

The mode above can't produce true editorial spreads (the kind found in printed Vogue / Kinfolk / Monocle). Specifically:

- Multi-image regions per spread (hero + portrait wall + captioned scenes)
- Multi-aspect images (1:1 portraits + 3:2 scenes + 16:10 environments on the same spread)
- Real PDF body text (selectable, embedded fonts, hyphenation)
- Drop caps, pull quotes, kickers, captions
- Spread-aware layout (left/right page differ; gutter offset; running headers)

### 3.3 Reference skills examined

Two HTML/CSS-based slide skills validated the "single-file HTML output + strict layout snippet library + style preset" approach:

- [`op7418/guizang-ppt-skill`](https://github.com/op7418/guizang-ppt-skill) — 10 layouts, 5 themes, single-HTML deck output. Strict aspect-ratio standardization (16:10 / 4:3 / 16:9 / 1:1 / 3:2 / 3:4 only). Pre-defined class names in root `template.html`. Anti-pattern docs.
- [`zarazhangrui/frontend-slides`](https://github.com/zarazhangrui/frontend-slides) — Zero-dependency HTML, viewport-fitting non-negotiable, named style presets ("Bold Signal" / "Electric Studio") with full typography + colors + signature elements, AI-slop avoidance prose.

We borrow: HTML/Jinja template family, named brand presets (typography + colors + tokens), strict aspect-ratio enumeration, anti-pattern documentation. We do NOT borrow: 16:9 viewport (we're A4 print), JS animations (PDF static), zero-dependency (we accept Weasyprint as a Python dep).

## 4. Architecture Decisions

Six decisions established during brainstorm (all confirmed by user):

### 4.1 PDF engine: Weasyprint

| Decision | Rationale |
|---|---|
| Engine | **Weasyprint** (`uv pip install weasyprint`) |
| Why | CSS Paged Media support (bleed / marks / `@page :left/:right` / running headers) is print-first. No JS / no Chrome dep. Pure Python, fits existing tool family. |
| Alternative considered | Playwright (rejected: heavy Chrome dep, JS unnecessary for print). ReportLab Platypus (rejected: imperative Python layout vs declarative CSS too painful for editorial). |
| Risk | Cairo / Pango native deps on macOS (`brew install weasyprint`); CI environment must have these. |

### 4.2 Layout expression: hybrid yaml + Jinja2

| Decision | Rationale |
|---|---|
| Form | `library/layouts/<name>.yaml` (metadata) + `library/layouts/<name>.html.j2` (render template) |
| Why | yaml drives `spec_validate` and prompt_builder (image slot specs feed image gen); j2 drives Weasyprint compose. Designer writes HTML directly; planner reads yaml; both stay in sync via shared slot IDs. |
| Alternative considered | Pure HTML (rejected: spec_validate loses teeth). Pure region-schema yaml (rejected: yaml-to-HTML translator over-engineered). |
| Influence | guizang's class-name discipline: root `_base.html.j2` defines all CSS; spread components reuse classes. Designers don't invent new class names. |

### 4.3 Image asset ↔ layout slot: per-slot per-spread

| Decision | Rationale |
|---|---|
| Granularity | Each `image_slot` is independently generated (1 storyboard cell + 1 Vertex call) |
| Storyboard | Still ONE inference of a multi-aspect grid covering all slots in the issue (locks character / style / lighting across all images) |
| Naming | `<spread_idx>.<slot_name>[.<n>]` (e.g. `spread-03.portrait_wall.4`) |
| Filesystem | `output/<slug>/storyboard/cells/spread-NN/<slot_id>.png` and `output/<slug>/images/spread-NN/<slot_id>.png` |
| Alternative considered | flat per-page (rejected: portrait wall infeasible). per-spread storyboard (rejected: character consistency lost). |

### 4.4 Content schema: new `articles/` layer (6 fields total)

| Decision | Rationale |
|---|---|
| Layer | New `library/articles/<slug>.yaml` |
| Spec impact | spec schema bumps to v2; new required field `article` (6 fields total: subject × style × theme × layout × brand × article) |
| Why | theme = visual world (reusable across issues); article = specific issue's copy. Industry separates these. |
| Auto-persist | If user provides only spec without `article`, agent drafts article in Stage 1 (research) and writes `library/articles/<slug>.yaml` to disk; user can edit before Stage 3 gate. |
| Alternative considered | theme yaml stuffed with copy (rejected: ties theme to one issue). spec inline copy (rejected: bloats spec, no reuse). |

### 4.5 Typography system: embedded in `brands/`

| Decision | Rationale |
|---|---|
| Location | `library/brands/<name>.yaml` schema v2 has `typography` + `print_specs` + `visual_tokens` |
| Why | Industry default: typography is brand identity. Vogue=Didone, NatGeo=Caslon, Kinfolk=geometric sans. |
| Presets | `library/brands/_presets/<name>.yaml` provides starting points: editorial-classic / humanist-warm (v0.3.0); architectural / swiss-modernist / editorial-asian (v0.3.1+). |
| Font sources | `google-fonts` (default; Weasyprint resolves) / `local` (`library/fonts/<family>/*.ttf`) / `system`. |
| Alternative considered | Independent typography_packs/ 7th layer (rejected: too many layers). Embed in styles/ (rejected: styles are image-gen prompt anchors, mixing concepts). |

### 4.6 v0.3.0 MVP scope: 1 layout + 2 presets + 6 spread types

In scope:

- 1 layout: `editorial-16page`
- 2 brand presets: `editorial-classic`, `humanist-warm`
- 6 spread types: cover, toc, feature-spread, portrait-wall, pull-quote, colophon, back-cover (technically 7; "cover" + "back-cover" share infrastructure)
- 1 example article: `cosmos-luna-may-2026`
- End-to-end testable

Out of scope (v0.3.1+):

- editorial-4 / editorial-32 layouts
- 3 remaining brand presets
- chapter-opener / index / advertorial / two-column-feature spread types
- 2nd / 3rd example articles

## 5. Schema v2

### 5.1 Spec schema v2

```yaml
# library/issue-specs/<slug>.yaml — schema_version: 2
schema_version: 2                # bumps from 1
slug: cosmos-luna-may-2026
subject: luna                     # → library/subjects/luna.yaml
style: kinfolk                    # → styles/kinfolk.yaml (Tier 1/2/3 fallback)
theme: cosmos                     # → library/themes/cosmos.yaml
layout: editorial-16page          # → library/layouts/editorial-16page.{yaml,html.j2}
brand: meow-life                  # → library/brands/meow-life.yaml
article: cosmos-luna-may-2026     # → library/articles/cosmos-luna-may-2026.yaml (NEW)
overrides: {}
```

Schema v1 specs (legacy `plain-4` / `plain-16`) lack `article` and continue working via the v0.1/v0.2 codepath.

### 5.2 Brand schema v2

```yaml
schema_version: 2
name: meow-life
display_name: {en: "MEOW LIFE", zh: "喵生杂志"}
masthead: "MEOW LIFE"
default_language: en

typography:
  display:    {family: "Playfair Display", weights: [700, 900], source: google-fonts}
  body:       {family: "Source Serif 4",   weights: [400, 600], source: google-fonts,
               size_pt: 10, leading: 1.45, align: justify, hyphenate: true}
  kicker:     {family: "IBM Plex Mono", weight: 500, transform: uppercase,
               letter_spacing: 0.08em, size_pt: 8}
  caption:    {family: "IBM Plex Mono", weight: 400, style: italic, size_pt: 8}
  pull_quote: {family: "Playfair Display", weight: 900, style: italic, size_pt: 32}
  drop_cap:   {enabled: true, family: "Playfair Display", weight: 900,
               lines: 3, color_token: accent}
  page_number: {family: "IBM Plex Mono", weight: 400, size_pt: 9}
  pairing_notes: |
    Playfair (display, didone-adjacent) + Source Serif (body) + IBM Plex Mono (meta).

print_specs:
  page_size: A4                    # A4 | Letter | custom
  page_size_custom_mm: ~
  bleed_mm: 3
  trim_marks: true
  registration_marks: false
  binding: saddle-stitch           # saddle-stitch | perfect-bound | spiral
  binding_gutter_mm: 8
  margin_top_mm: 20
  margin_bottom_mm: 22
  margin_outer_mm: 18
  margin_inner_mm: 22
  baseline_grid_mm: 4
  paper_stock_note: "80gsm uncoated"
  color_mode: rgb                  # rgb | cmyk

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

### 5.3 Layout schema v2

```yaml
# library/layouts/editorial-16page.yaml — schema_version: 2
schema_version: 2
name: editorial-16page
display_name: Editorial 16-page A4 Spread
typography_mode: editorial-spread  # vs full-bleed (v1) / collage / etc

format:
  page_count: 16
  spreads: 9                       # cover (1) + toc (1) + 4 features (4) + portrait wall (1) + pull quote (1) + colophon (1) + back (1)... wait, recount: see spread_plan
  page_size: A4
  bleed_mm: 3
  binding: saddle-stitch

spread_plan:                       # ordered; idx referenced by article.spread_copy
  - {idx: 1, type: cover,           pages: [1]}
  - {idx: 2, type: toc,             pages: [2, 3]}
  - {idx: 3, type: feature-spread,  pages: [4, 5]}
  - {idx: 4, type: feature-spread,  pages: [6, 7]}
  - {idx: 5, type: pull-quote,      pages: [8, 9]}
  - {idx: 6, type: feature-spread,  pages: [10, 11]}
  - {idx: 7, type: portrait-wall,   pages: [12, 13]}
  - {idx: 8, type: colophon,        pages: [14, 15]}
  - {idx: 9, type: back-cover,      pages: [16]}

image_slots:
  # cover
  - {id: cover_hero,             role: cover_hero,   aspect: "3:4",  min_long_edge_px: 3500, in_spread: 1}
  # feature-spread (each spread has 1 hero + 3 captioned)
  - {id: feature_hero,           role: portrait,     aspect: "3:4",  min_long_edge_px: 3000, count: 3}  # spreads 3, 4, 6
  - {id: feature_captioned,      role: scene,        aspect: "3:2",  min_long_edge_px: 2500, count: 9}  # 3 scenes × 3 spreads
  # pull-quote
  - {id: pullquote_environment,  role: environment,  aspect: "16:10", min_long_edge_px: 3500, in_spread: 5}
  # portrait-wall
  - {id: portrait_wall,          role: portrait,     aspect: "1:1",  min_long_edge_px: 1500, count: 6, in_spread: 7}
  # back
  - {id: back_coda,              role: back_coda,    aspect: "2:3",  min_long_edge_px: 2500, in_spread: 9}

  # total: 1 + 3 + 9 + 1 + 6 + 1 = 21 image slots
  # Vertex 4K cost: 21 × $0.24 = $5.04 + 1 codex storyboard ≈ $5.04 USD

text_slots_required:               # what article.spread_copy must provide per spread type
  cover: [cover_line, cover_kicker]
  toc: [table_of_contents]         # list of {page, title}
  feature-spread: [title, kicker, lead, body]
  pull-quote: [quote, attribution]
  portrait-wall: [title, captions] # captions: list per portrait_wall.N
  colophon: [credits]
  back-cover: [quote, attribution]
```

### 5.4 Article schema (NEW)

```yaml
# library/articles/<slug>.yaml — schema_version: 1 (new layer)
schema_version: 1
slug: cosmos-luna-may-2026
display_title: {en: "Luna Walks the Moon", zh: "月行猫"}

masthead_override: ~               # null = use brand.masthead
issue_label: {en: "ISSUE 03 / MAY 2026", zh: "第 03 期 / 2026 年 5 月"}
cover_line: {en: "...", zh: "..."}
cover_kicker: {en: "FEATURE STORY", zh: "封面故事"}

spread_copy:                       # MUST match length and idx of layout.spread_plan
  - idx: 1
    type: cover
    notes: "cover line + kicker provided above"
  - idx: 3
    type: feature-spread
    pages: [4, 5]
    title: {en: "DEPARTURE", zh: "启程"}
    kicker: {en: "Chapter 01", zh: "第一章"}
    lead: {en: "She steps from...", zh: "她踏出..."}
    body:
      en: |
        First paragraph.

        Second paragraph.

        Third paragraph.
      zh: |
        正文第一段。

        正文第二段。

        正文第三段。
    image_slot_overrides:          # optional; map article-specific scenes to layout's slots
      feature_hero: "subject in EVA suit at module windowsill, Earth visible upper right"
      feature_captioned.1: "footprints in regolith, low angle"
      feature_captioned.2: "wide lunar plain, subject mid-frame"
      feature_captioned.3: "close-up of glove on rock"
  # ... (rest of spreads)

  - idx: 7
    type: portrait-wall
    pages: [12, 13]
    title: {en: "STILLS FROM A MISSION", zh: "任务剪影"}
    captions:
      - {slot: portrait_wall.1, en: "Approach", zh: "接近"}
      - {slot: portrait_wall.2, en: "Pause",    zh: "停顿"}
      - {slot: portrait_wall.3, en: "Touch",    zh: "触碰"}
      - {slot: portrait_wall.4, en: "Listen",   zh: "聆听"}
      - {slot: portrait_wall.5, en: "Climb",    zh: "攀登"}
      - {slot: portrait_wall.6, en: "Look Back", zh: "回望"}

  - idx: 8
    type: colophon
    pages: [14, 15]
    credits:
      photographer: "..."
      art_direction: "..."
      printing: "..."
      copyright: "..."
```

## 6. New file structure

```
~/github/openMagazine/
├── library/
│   ├── brands/
│   │   ├── _presets/
│   │   │   ├── editorial-classic.yaml      # NEW
│   │   │   └── humanist-warm.yaml          # NEW
│   │   └── meow-life.yaml                  # bumped to v2
│   ├── articles/                           # NEW LAYER
│   │   ├── README.md
│   │   └── cosmos-luna-may-2026.yaml
│   ├── layouts/
│   │   ├── _base.html.j2                   # NEW root template
│   │   ├── _components/                    # NEW spread components
│   │   │   ├── cover.html.j2
│   │   │   ├── toc.html.j2
│   │   │   ├── feature-spread.html.j2
│   │   │   ├── portrait-wall.html.j2
│   │   │   ├── pull-quote.html.j2
│   │   │   ├── colophon.html.j2
│   │   │   └── back-cover.html.j2
│   │   ├── editorial-16page.yaml           # NEW
│   │   ├── editorial-16page.html.j2        # NEW
│   │   ├── plain-4.yaml                    # legacy v1
│   │   └── plain-16.yaml                   # legacy v1
│   ├── fonts/                              # NEW (only if local fonts used)
│   │   └── README.md
│   ├── templates/
│   │   ├── storyboard.prompt.md            # v0.2 (still used by legacy plain-*)
│   │   ├── storyboard_v2.prompt.md         # NEW (multi-aspect grid)
│   │   ├── upscale_cover.prompt.md         # v0.2 (legacy)
│   │   ├── upscale_inner.prompt.md         # v0.2 (legacy)
│   │   ├── upscale_back.prompt.md          # v0.2 (legacy)
│   │   ├── upscale_portrait.prompt.md      # NEW role-driven
│   │   ├── upscale_scene.prompt.md         # NEW
│   │   ├── upscale_environment.prompt.md   # NEW
│   │   ├── upscale_detail.prompt.md        # NEW
│   │   ├── upscale_cover_hero.prompt.md    # NEW
│   │   └── upscale_back_coda.prompt.md     # NEW
│   └── SCHEMA.md                           # updated with v2 + articles
├── lib/
│   ├── config_loader.py                    # v0.1.2
│   ├── checkpoint.py
│   ├── cost_tracker.py
│   ├── placeholder_resolver.py             # extended for typography placeholders
│   ├── prompt_builder.py                   # v0.2 (legacy paths)
│   ├── prompt_builder_v2.py                # NEW role-driven
│   ├── spec_loader.py
│   └── storyboard_planner.py               # NEW
├── tools/
│   ├── pdf/
│   │   ├── reportlab_compose.py            # v0.2 (legacy plain-* uses this)
│   │   └── weasyprint_compose.py           # NEW
│   ├── meta/
│   │   ├── scaffold_style.py
│   │   └── migrate_brand_v1_to_v2.py       # NEW
│   └── validation/
│       ├── spec_validate.py                # extended for v2
│       └── article_validate.py             # NEW (article ↔ layout consistency)
├── pipeline_defs/
│   ├── smoke-test-4page.yaml               # v0.2 legacy
│   └── editorial-16page.yaml               # NEW
├── skills/
│   ├── pipelines/
│   │   ├── smoke-test-4page/               # v0.2 legacy 6 directors
│   │   └── editorial-16page/               # NEW 6 directors
│   │       ├── research-director.md
│   │       ├── proposal-director.md
│   │       ├── articulate-director.md      # NEW (article copy generation)
│   │       ├── storyboard-director.md
│   │       ├── upscale-director.md
│   │       ├── compose-director.md
│   │       └── publish-director.md
│   └── meta/
│       └── article-writer.md               # NEW (used by articulate-director)
├── tests/
│   ├── unit/
│   │   ├── test_storyboard_planner.py      # NEW
│   │   ├── test_prompt_builder_v2.py       # NEW
│   │   ├── test_weasyprint_compose.py      # NEW
│   │   └── test_brand_v2_schema.py         # NEW
│   ├── integration/
│   │   └── test_render_dry_run.py          # NEW (placeholder PNG → full PDF)
│   └── contracts/
│       └── test_v2_pipelines.py            # NEW
└── docs/
    ├── v0.3-ARCHITECTURE.md                # NEW
    ├── spread-types-reference.md           # NEW
    ├── typography-pack-cookbook.md         # NEW
    ├── SCHEMA_V2_MIGRATION.md              # NEW
    └── SMOKE_TEST_v0.3.md                  # NEW (filled after end-to-end run)
```

## 7. Tooling additions

### 7.1 `lib/storyboard_planner.py`

```python
def plan_storyboard(image_slots: list[dict], outer_aspect: str = "2:3") -> dict:
    """Pack heterogeneous-aspect slots into a single 2:3 portrait grid.

    Input:
      image_slots: [{slot_id, role, aspect, count, ...}]  (flattened from layout)
      outer_aspect: storyboard outer aspect; default 2:3 portrait

    Output:
      {
        "outer_aspect": "2:3",
        "outer_size_px": [1024, 1536],
        "cells": [
          {"slot_id": "spread-01.cover_hero", "row": 0, "col": 0,
           "rowspan": 2, "colspan": 1, "aspect": "3:4",
           "bbox_px": [x, y, w, h], "page_label": "01"},
          ...
        ]
      }
    """
```

Algorithm sketch: bin-pack via greedy (sort slots by area desc, place into rows). For 21 slots in editorial-16page, a 6×4 grid with some 1×2 / 2×1 cells works.

### 7.2 `lib/prompt_builder_v2.py`

```python
def build_storyboard_prompt_v2(spec: dict, layers: dict, plan: dict) -> str:
    """Renders library/templates/storyboard_v2.prompt.md with multi-aspect grid."""

def build_upscale_prompt(
    *, role: str, spec: dict, layers: dict,
    slot_id: str, scene: str, ref_paths: list[Path]
) -> str:
    """Render role-specific upscale template; per-call scene plus shared placeholders."""

ROLE_TEMPLATES = {
    "portrait":     "upscale_portrait.prompt.md",
    "scene":        "upscale_scene.prompt.md",
    "environment":  "upscale_environment.prompt.md",
    "detail":       "upscale_detail.prompt.md",
    "cover_hero":   "upscale_cover_hero.prompt.md",
    "back_coda":    "upscale_back_coda.prompt.md",
}
```

### 7.3 `tools/pdf/weasyprint_compose.py`

```python
class WeasyprintCompose(BaseTool):
    capability = "pdf_compose"
    provider = "weasyprint"
    cost_per_call_usd = 0.0
    agent_skills = ["weasyprint-cookbook"]

    def run(self, *, issue_dir: Path, layout: dict, brand: dict,
            article: dict, spec: dict) -> dict:
        """Render output/<slug>/magazine.pdf via Weasyprint.

        Reads:
          - layout html.j2 + components
          - 4K images at output/<slug>/images/spread-NN/<slot_id>.png
          - article copy (text content)
          - brand typography + visual tokens

        Writes:
          - output/<slug>/magazine.pdf
          - output/<slug>/magazine.html (intermediate; gitignored)

        Returns: {"pdf_path": str, "page_count": int, "size_mb": float, "html_path": str}
        """
```

Implementation:

1. Load `library/layouts/<name>.html.j2` via Jinja2 environment
2. Build template context: `{layout, brand, article, spec, images, page_plan, language: brand.default_language}`
3. Render to single HTML string → write `magazine.html`
4. `weasyprint.HTML(string=html).write_pdf("magazine.pdf")`
5. Return metadata

### 7.4 `lib/placeholder_resolver.py` extensions

Add typography-aware placeholders for prompts that reference typography (e.g., cover_hero prompt mentions masthead font style):

```python
return {
    ...existing,
    "{{TYPOGRAPHY_DISPLAY_FAMILY}}": brand["typography"]["display"]["family"],
    "{{TYPOGRAPHY_BODY_FAMILY}}": brand["typography"]["body"]["family"],
    "{{TYPOGRAPHY_PAIRING_HINT}}": brand["typography"].get("pairing_notes", ""),
    "{{COLOR_ACCENT}}": brand["visual_tokens"]["color_accent"],
    "{{COLOR_BG_PAPER}}": brand["visual_tokens"]["color_bg_paper"],
}
```

These let the cover_hero prompt say e.g. "masthead set in a serif resembling Playfair Display, accent color #c2272d painted into the scene as a real visual element."

## 8. Pipeline definition

```yaml
# pipeline_defs/editorial-16page.yaml
name: editorial-16page
version: "1.0"
schema_version: 2
description: 16-page editorial A4 magazine with multi-image spreads + real PDF text.
category: editorial
stability: experimental                # bumps to production after smoke validates

reference_input:
  supported: true
  analysis_depth: shallow

orchestration:
  parallelism: 3                       # config-driven via lib.config_loader.get_parallelism
  budget_default_usd: 5.50             # 21 vertex × $0.24 = $5.04, plus codex storyboard
  max_wall_time_minutes: 30

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

  - name: proposal
    skill: pipelines/editorial-16page/proposal-director
    produces: proposal.json
    checkpoint: "off"
    reviewer: "enabled"

  - name: articulate                   # NEW STAGE
    skill: pipelines/editorial-16page/articulate-director
    produces: article.yaml             # written to library/articles/<slug>.yaml
    checkpoint: "required"             # user reviews/edits article copy
    reviewer: "enabled"

  - name: storyboard
    skill: pipelines/editorial-16page/storyboard-director
    produces:
      - storyboard.png
      - storyboard.json
      - cells/spread-NN/<slot_id>.png  # 21 cell PNGs
    checkpoint: "required"
    reviewer: "enabled"

  - name: upscale
    skill: pipelines/editorial-16page/upscale-director
    produces:
      - images/spread-NN/<slot_id>.png  # 21 4K PNGs
      - upscale_result.json
    checkpoint: "off"
    reviewer: "enabled"

  - name: compose
    skill: pipelines/editorial-16page/compose-director
    produces:
      - magazine.pdf
      - magazine.html
      - compose_result.json
    checkpoint: "off"
    reviewer: "enabled"

  - name: publish
    skill: pipelines/editorial-16page/publish-director
    produces:
      - publish_report.json
      - contact_sheet.jpg
    checkpoint: "off"
    reviewer: "disabled"

defaults:
  storyboard_grid_outer: "2:3"
  storyboard_size_px: [1024, 1536]
  page_count: 16
  aspect: "2:3"
```

Pipeline now has **7 stages** (added `articulate`); the article copy is the new content artifact between proposal and storyboard.

## 9. Director skills (highlights)

### 9.1 articulate-director (NEW)

- **Inputs**: research_brief.json, proposal.json, layout yaml, theme yaml
- **Outputs**: writes `library/articles/<slug>.yaml`; writes `output/<slug>/article.json` (artifact)
- **Behavior**: if spec.article exists & file exists, load and skip generation. Else: agent drafts article copy aligned with layout.spread_plan + theme.page_plan_hints, then auto-persists.
- **Checkpoint**: required (user can edit yaml before storyboard)

### 9.2 storyboard-director (rewrite)

- **Inputs**: article.yaml, layout yaml, brand yaml
- **Procedure**:
  1. Flatten layout's image_slots into a list (~21 slots for editorial-16page)
  2. Call `plan_storyboard(slots)` → grid plan
  3. Render storyboard_v2 prompt with the plan
  4. Call codex `image_gen.imagegen` (BEFORE/AFTER capture as in v0.2)
  5. Split storyboard into per-slot cells using `pillow_split` extended to multi-aspect mode (cells map to plan.cells, not uniform grid)
  6. Write storyboard.json artifact
- **Checkpoint**: required

### 9.3 upscale-director (rewrite)

- **Inputs**: storyboard.json (cells per slot), article.yaml, layout yaml
- **Procedure**:
  1. For each image_slot in flattened layout:
     - role = slot.role; pick template via `ROLE_TEMPLATES[role]`
     - scene = `article.spread_copy[idx].image_slot_overrides[slot_id]` if present, else theme hint
     - refs = `[cells/spread-NN/<slot_id>.png, refs/protagonist-1.jpg]` (protagonist optional for environment / detail roles)
     - call VertexGeminiImage with computed aspect from slot
  2. Drive via ThreadPoolExecutor with `lib.config_loader.get_parallelism()` (cap 3)
  3. Write upscale_result.json with all 21 image paths

### 9.4 compose-director (rewrite)

- **Inputs**: all 21 4K images, article.yaml, layout yaml + j2, brand yaml
- **Procedure**: call `WeasyprintCompose.run(...)`; output `magazine.pdf` + intermediate `magazine.html`

## 10. Compatibility & migration

### 10.1 v1 → v2 brand migration

`tools/meta/migrate_brand_v1_to_v2.py library/brands/<name>.yaml`:

- Keep existing fields (name, masthead, display_name)
- Add typography from `editorial-classic` preset (default)
- Add print_specs with sensible A4 defaults
- Add visual_tokens with neutral palette
- Bump schema_version to 2
- Write back; print before/after diff

### 10.2 Coexistence

| User runs | Pipeline path | Compose engine |
|---|---|---|
| smoke-test-4page (v1 layout, v1 brand) | v0.1/v0.2 directors | ReportLab |
| editorial-16page (v2 layout, v2 brand, v2 spec, article) | v0.3 directors | Weasyprint |

`spec_validate` detects schema_version and routes to the correct codepath.

### 10.3 Tools registry

Both `ReportlabCompose` and `WeasyprintCompose` register under capability `pdf_compose`. A new selector `tools/pdf/pdf_selector.py` (modeled on `image_selector`) routes by `spec.layout` schema_version:

```python
class PdfSelector(BaseTool):
    def choose_backend(self, *, spec, layout) -> BaseTool:
        if layout.get("schema_version") == 2:
            return self._weasyprint
        return self._reportlab
```

This keeps director skills declarative ("dispatch pdf_compose") instead of choosing engines explicitly.

## 11. Print spec / typography details

### 11.1 CSS Paged Media implementation

Root `_base.html.j2` declares:

```css
@page {
  size: {{ brand.print_specs.page_size }};
  bleed: {{ brand.print_specs.bleed_mm }}mm;
  marks: {% if brand.print_specs.trim_marks %}crop{% endif %};
  margin:
    {{ brand.print_specs.margin_top_mm }}mm
    {{ brand.print_specs.margin_outer_mm }}mm
    {{ brand.print_specs.margin_bottom_mm }}mm
    {{ brand.print_specs.margin_inner_mm }}mm;

  @bottom-center {
    content: counter(page);
    font-family: '{{ brand.typography.page_number.family }}', monospace;
    font-size: {{ brand.typography.page_number.size_pt }}pt;
  }
}
@page :left  { margin-right: {{ brand.print_specs.margin_inner_mm }}mm; }
@page :right { margin-left:  {{ brand.print_specs.margin_inner_mm }}mm; }
```

### 11.2 Drop cap

```css
.drop-cap p:first-of-type::first-letter {
  font-family: '{{ brand.typography.drop_cap.family }}', serif;
  font-weight: {{ brand.typography.drop_cap.weight }};
  font-size: calc({{ brand.typography.body.size_pt }}pt *
                 {{ brand.typography.drop_cap.lines }} *
                 {{ brand.typography.body.leading }});
  float: left;
  line-height: 0.85;
  margin: 0 0.1em -0.1em 0;
  color: var(--color-{{ brand.typography.drop_cap.color_token }});
}
```

### 11.3 Hyphenation

Body paragraphs get `hyphens: auto` and `text-align: justify`. Weasyprint supports hyphens for languages it has dictionaries for (English, German, French, etc.). Chinese: hyphens not applicable; use `text-justify: inter-character`.

### 11.4 Font loading

Default `source: google-fonts`: `_base.html.j2` includes `<link href="https://fonts.googleapis.com/css2?family=...">`. Weasyprint's HTTP fetcher resolves these.

`source: local`: `@font-face { src: url('library/fonts/Family/file.ttf'); }`. Path is relative to the rendered HTML's location.

`source: system`: `font-family: 'X', serif;` only; no resolution. Used for "I have these fonts on my mac" workflows.

## 12. Out of scope / v0.3.1+ roadmap

- editorial-4 (~6 spreads) and editorial-32 (~16 spreads) layouts
- 3 remaining brand presets: architectural / swiss-modernist / editorial-asian
- spread types: chapter-opener / index / advertorial / two-column-feature / spread-of-3
- 2nd article example (different theme)
- Automatic spread layout solver (today: hand-crafted j2 components)
- CMYK output (Weasyprint supports via PDF profile assignment)
- Bilingual side-by-side spreads
- HTML web preview (reuse magazine.html with viewport-base.css)
- EPUB / Kindle export
- Animated cover (HTML+CSS animation rendered via Playwright)

## 13. Open questions / risks

### 13.1 Risks

- **Weasyprint native deps**: cairo / pango / harfbuzz on macOS via brew. CI environment must `brew install weasyprint` or use a docker base image. Mitigation: document in `pyproject.toml` README; fallback to Playwright if Weasyprint won't install.
- **Storyboard planner complexity**: 21-slot multi-aspect packing. First implementation uses greedy bin-pack; if visual quality is poor, may need to hand-curate plan per layout.
- **Codex `image_gen.imagegen` multi-aspect compliance**: even with explicit "cell N is 1:1, cell M is 3:4" prompt instructions, the model may pull cells back to uniform aspect. Mitigation: storyboard prompt sanity check (tools/image/pillow_split.py warns on aspect drift).
- **Article auto-draft quality**: agent's first-cut copy may be generic. Mitigation: checkpoint required; user always edits before storyboard.
- **Vertex 4K cost**: 21 calls × $0.24 = $5.04 per issue. Mitigation: smoke test uses placeholder PNGs for dry-run; live test budget is explicit.

### 13.2 Open questions (to resolve during plan / impl)

1. Should `articulate` stage run BEFORE `proposal` (so proposal sees the actual article)? Current order is research → proposal → articulate → storyboard. Argument for swap: proposal's cost estimate depends on slot count, which depends on layout, which depends on article structure (does the article have 4 pull quotes or 2?). Argument against: proposal can use layout's slot count without article copy. **Tentative decision: keep articulate after proposal; revisit during impl if blocking.**
2. How to handle "missing article copy fields" gracefully (e.g. user wrote article but skipped a body paragraph)? **Tentative: Weasyprint render shows visible empty blocks in dev; spec_validate flags missing fields with warnings (not errors).**
3. Should `_components/` j2 files be self-contained or extend a base component? **Tentative: self-contained `{% include %}` from layout-level j2; base only for `_base.html.j2`. Reduces include depth.**
4. Output PDF size target? Editorial spread = real photos + text + vector decoration. Weasyprint embeds PNGs as JPEG by default. Expect ~30-80 MB for 16-page editorial. **Update success criteria post-smoke.**

## Appendix A: Reference inspirations

### A.1 [op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)
- Single-HTML deck output; root `template.html` defines class names; layouts are paste-ready `<section class="slide grid-N-N">` snippets.
- Strict aspect-ratio enumeration: `r-16x10`, `r-4x3`, `r-16x9`, `r-1x1`, `r-3x2`, `r-3x4`. No arbitrary `aspect-ratio: ...` values.
- Anti-pattern docs: "❌ `align-self: end` outside flex/grid is invalid; ✓ use grid + `align-items: start`."
- Aspect alignment table by use case (left-text-right-image / image grid / corner art).
- **Borrowed**: class-name discipline, aspect-ratio standardization, anti-pattern docs format.

### A.2 [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides)
- Zero-dep single HTML; viewport-fitting non-negotiable.
- Named style presets (typography family + colors + signature elements).
- AI-slop avoidance: avoid Inter / Roboto / generic gradients; use distinctive choices.
- Content density limits per slide type.
- **Borrowed**: brand preset format (typography pack), anti-AI-slop prose, content density discipline (per-spread copy length).

## Appendix B: 6 spread types (visual sketch)

For reference; component j2 files implement these.

```
COVER (1 page)              FEATURE-SPREAD (2 pages)        PULL-QUOTE (2 pages)
┌─────────────┐             ┌──────┬──────┐                 ┌─────────────────┐
│  HERO IMG   │             │      │ kicker│                 │                 │
│  3:4        │             │      │ TITLE │                 │   "QUOTE"       │
│             │             │ HERO │ ────  │                 │   — attrib      │
│  MASTHEAD   │             │ 3:4  │ ▢▢ ▢  │                 │   over env img  │
│  cover_line │             │      │ body  │                 │                 │
└─────────────┘             └──────┴──────┘                 └─────────────────┘

TOC (2 pages)               PORTRAIT-WALL (2 pages)         COLOPHON (2 pages)  BACK (1 page)
┌──────┬──────┐             ┌──┬──┬──┬──┐                  ┌──────┬──────┐    ┌─────────────┐
│ TOC  │      │             │  │  │  │  │                  │ MEOW │      │    │  small      │
│ 04 - │  *   │             │  │  │  │  │                  │ LIFE │ body │    │  coda img   │
│ 06 - │      │             ├──┼──┼──┼──┤                  │      │ text │    │             │
│ 08 - │      │             │  │  │  │  │                  │ —    │      │    │  "quote"    │
└──────┴──────┘             └──┴──┴──┴──┘                  └──────┴──────┘    └─────────────┘
```

---

## Self-review checklist

(per `superpowers:brainstorming` skill spec self-review step)

- ✅ No "TBD" / "TODO" placeholders in normative sections
- ✅ Internal consistency: schema v2 fields cross-referenced (brand.typography ↔ CSS vars; layout.image_slots ↔ article.spread_copy.image_slot_overrides ↔ ROLE_TEMPLATES)
- ✅ Scope check: 1 layout + 6 spread types + 2 brand presets is achievable in ~9 working days
- ✅ Ambiguity check: open questions explicitly listed in §13.2

## Next step

User reviews this spec. If approved, `superpowers:writing-plans` produces a step-by-step implementation plan at `docs/superpowers/plans/2026-05-10-openmagazine-v0.3-editorial-engine.md` with bite-sized TDD tasks for each phase (A through E).
