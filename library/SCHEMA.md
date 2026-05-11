# Library Schema

openMagazine accepts two input sources:

- **Free-form** — user one-liner + photo. Agent infers traits, looks up styles
  via Author Obligation 2 (Tier 1/2/3), gives sensible defaults for theme /
  layout / brand.
- **Spec yaml** — user writes `library/issue-specs/<name>.yaml`. v1 specs
  reference subject / style / theme / layout / brand. v2 editorial specs use
  those same references plus an optional `article` reference.

Both sources feed a declared pipeline. v1 simple specs use storyboard → split
→ gate → 4K → PDF; v2 editorial specs add an articulate stage before
storyboard and compose with real PDF text.

Free-form runs **auto-persist** their resolved configuration as a new
`library/issue-specs/<slug>.yaml` after the storyboard gate, so subsequent
runs of the same issue can use spec input directly.

---

## Layers

```
styles/             风格库 (top-level; covered by styles/README.md)
library/
├── subjects/       protagonist 卡片 — name + traits + reference photo
├── themes/         主题世界 — theme_world + lighting_principles + page_plan_hints
├── layouts/        版面参数 — page_count + aspect + storyboard_grid + typography_mode
├── brands/         杂志品牌 — masthead + url + persona
├── articles/       v0.3 editorial copy — spread_copy + image_slot_overrides
└── issue-specs/    一站式 spec — 引用上面层 + spec-level overrides
```

The styles layer is **orthogonal**: it carries `style_anchor` text injected
verbatim into all prompts. Styles are looked up by trigger keyword (Author
Obligation 2). The other layers + spec compose deterministically.

---

## subjects/<name>.yaml

```yaml
schema_version: 1
name: luna                          # filename stem
display_name:
  en: Luna
  zh: Luna
species: cat                        # animal | person | place | product | concept
breed: British Shorthair            # optional, free-form
reference_image: ./refs/luna.png    # path relative to subjects/<name>.yaml
                                    # OR absolute path. Required.
traits: |
  Luna, healthy adult British Shorthair cat, silver-golden coat with
  beige-gray tabby markings on forehead and back, round face, clear
  bright amber eyes, upright ears, slightly chubby build.
  # 5-8 sentences max. Becomes {{TRAITS}} verbatim across all 16 prompts.
```

Required: `schema_version`, `name`, `species`, `reference_image`, `traits`.

---

## themes/<name>.yaml

```yaml
schema_version: 1
name: cosmos
display_name:
  en: Cosmos
  zh: 太空号

theme_world: |
  Outer space, vast, sublime. ISS-style modules. Single hard sun.
  Earth visible as small blue marble.
  # One sentence to 1 short paragraph. Becomes {{THEME_WORLD}} verbatim.

lighting_principles: |
  Single hard sun from front-left. Sky pure black with pinhole stars.
  Long sharp shadows. Earth's blue is the only saturated color.
  # 50-80 words. Embedded in storyboard prompt as scene mood guidance.

default_cover_line:
  en: "THE COSMOS ISSUE / {{PROTAGONIST_NAME}} walks the Moon"
  zh: "太空号 / {{PROTAGONIST_NAME}} 行走于月球"
  # Will receive a second-pass {{PROTAGONIST_NAME}} substitution.

page_plan_hints:
  # 16 (or 4 / 8 / 12) hints, one per page. Each hint is a short scene phrase.
  # Becomes the page plan inside the storyboard prompt's "Page plan:" block.
  # SCENE_NN values during 4K generation derive from these hints.
  - "01: hero cover, low-angle, character framed center-left"
  - "02: opening EVA approach, wide reportage"
  - "03: close-up paw prints in regolith"
  - "04: ..."
  - "10: tension, character in tight spacecraft module"
  - "11: climax visual peak, full-frame Earth backdrop"
  - "13: ..."
  - "16: back-cover wide-fade silhouette"

# Optional. Use when pages will receive HTML/PDF overlays after image
# generation. These contracts are injected into storyboard and 4K prompts.
page_overlay_contracts:
  - page: 3
    subject_zone: right-center
    protected_zones:
      - {name: face, rect: [0.52, 0.14, 0.92, 0.58]}
    reserved_overlay_zones: [left-rail, bottom-strip]
    negative_space: ["left 32%", "bottom 18%"]
    html_components: [EvidenceRail, BottomPinboard, Folio]
    forbidden: [cards-over-face, cross-face-lines]
```

Required: `schema_version`, `name`, `theme_world`, `default_cover_line.en`,
`page_plan_hints` (length must match the layout's `page_count`).

---

## layouts/<name>.yaml

```yaml
schema_version: 1
name: plain-16
display_name: Plain 16-page A4

page_count: 16                      # 4 / 8 / 12 / 16 — fixed for the layout
aspect: "2:3"                       # cell + 4K page aspect; A4 portrait friendly
storyboard_grid: "4x4"              # rows×cols for split-storyboard
                                    # Must satisfy rows*cols == page_count
top_crop_px_default: 60             # cells/<>.png top-crop to remove page-number labels

typography_mode: full-bleed         # full-bleed | footer-bar
                                    # full-bleed: cover/back masthead/colophon
                                    #             integrated INTO photo
                                    # footer-bar: cover/back have separate
                                    #             cream footer strip (legacy)

caption_overlay: false              # Whether build_pdf should overlay
                                    # captions per page (currently false-only;
                                    # captions feature is orphan)
```

Required: `schema_version`, `name`, `page_count`, `aspect`, `storyboard_grid`,
`typography_mode`.

`storyboard_grid` parsing: `"4x4"` → rows=4 cols=4. Must satisfy
`rows*cols == page_count`. Common combos:
- `page_count=16` → `4x4`
- `page_count=12` → `3x4` or `4x3`
- `page_count=8`  → `2x4` or `4x2`
- `page_count=4`  → `2x2`

v2 editorial layouts use a different shape:

```yaml
schema_version: 2
name: editorial-16page
typography_mode: editorial-spread
format:
  page_count: 16
  spreads: 9
spread_plan:
  - {idx: 1, type: cover, pages: [1]}
image_slots:
  - {id: cover_hero, role: cover_hero, aspect: "3:4", min_long_edge_px: 3500, spread_idx: 1}
text_slots_required:
  feature-spread: [title, kicker, lead, body]
```

Required for v2: `schema_version`, `name`, `typography_mode`, `format`,
`spread_plan`, `image_slots`, `text_slots_required`.

---

## brands/<name>.yaml

```yaml
schema_version: 1
name: meow-life
display_name:
  en: MEOW LIFE
  zh: 主子号

masthead: MEOW LIFE                 # becomes {{MAGAZINE_NAME}} for cover prompt
url: meowlife.cn                    # optional
persona: |
  Editor-in-chief: the cat itself. First-person editorial voice for
  any cover-line copy.
```

Required: `schema_version`, `name`, `masthead`.

v2 editorial brands additionally require `default_language`, `typography`,
`print_specs`, and `visual_tokens`. Use
`tools/meta/migrate_brand_v1_to_v2.py` with a preset to upgrade a v1 brand.

---

## articles/<name>.yaml (v0.3 editorial)

```yaml
schema_version: 1
slug: cosmos-luna-may-2026
display_title: {en: "Luna Walks the Moon"}
issue_label: {en: "ISSUE 03 / MAY 2026"}
cover_line: {en: "A small astronaut on the lunar regolith"}
cover_kicker: {en: "FEATURE STORY"}
spread_copy:
  - idx: 1
    type: cover
    image_slot_overrides:
      cover_hero: "Luna in EVA suit standing on lunar regolith"
```

Required: `schema_version`, `slug`, `display_title`, `issue_label`,
`cover_line`, `cover_kicker`, `spread_copy`. For v2 editorial production,
`article_validate` also checks that each layout image slot has a matching
`image_slot_overrides` entry on the corresponding spread.

---

## issue-specs/<name>.yaml (spec input — one file per issue)

```yaml
schema_version: 1

slug: cosmos-luna-01                # output dir name; usually <theme>-<subject>-<NN>
issue_number: "01"
date: "MAY 2026"                    # optional; falls back to current month uppercase

# 5 layers — by name reference
subject: luna                       # → library/subjects/luna.yaml
style: matisse-fauve                # → styles/matisse-fauve.yaml
theme: cosmos                       # → library/themes/cosmos.yaml
layout: plain-16                    # → library/layouts/plain-16.yaml
brand: meow-life                    # → library/brands/meow-life.yaml

# Optional overrides — take precedence over layer defaults
overrides:
  cover_line: "THE COSMOS ISSUE / Luna explores zero-G"   # overrides theme.default_cover_line
  masthead: "LUNA"                                          # overrides brand.masthead
```

Required: `schema_version`, `slug`, `subject`, `style`, `theme`, `layout`,
`brand`. The 5 layer references must each correspond to a yaml in the matching
library directory; `style` may also be a name not yet in `styles/`,
in which case it triggers the scaffold-style meta-protocol (Tier 2).

v2 editorial issue specs use the same required fields with `schema_version: 2`
and usually add `article`:

```yaml
schema_version: 2
slug: cosmos-luna-may-2026
subject: luna
style: national-geographic
theme: cosmos
layout: editorial-16page
brand: meow-life
article: cosmos-luna-may-2026
overrides: {}
```

`article` is optional during early research so the articulate stage can draft
it, but final production should reference a persisted
`library/articles/<slug>.yaml`.

---

## Placeholder map — value resolution order

For each placeholder, take the first source that has a value:

| Placeholder | 1st source | 2nd source | 3rd source | 4th source |
|---|---|---|---|---|
| `{{TRAITS}}` | `subjects/<name>.yaml.traits` | (free-form) agent infers from photo | — | — |
| `{{STYLE_ANCHOR}}` | `styles/<name>.yaml.style_anchor` | (Tier 2) scaffold-style meta-protocol | (Tier 3) inline rewrite per Obligation 2 | — |
| `{{THEME_WORLD}}` | `themes/<name>.yaml.theme_world` | (free-form) user one-liner | (free-form) agent default | — |
| `{{MAGAZINE_NAME}}` | `spec.overrides.masthead` | `brands/<name>.yaml.masthead` | (free-form) user input | — |
| `{{COVER_LINE}}` | `spec.overrides.cover_line` | `themes/<name>.yaml.default_cover_line.en` | (free-form) user input or agent | — |
| `{{PROTAGONIST_NAME}}` | `subjects/<name>.yaml.display_name.en` | `subjects/<name>.yaml.name` | (free-form) agent | — |
| `{{ISSUE_NUMBER}}` | `spec.issue_number` | last digits of `spec.slug` | "01" | — |
| `{{DATE}}` | `spec.date` | current month uppercase | — | — |

Per-page placeholders (filled by agent during Phase 3+4):

| Placeholder | Source |
|---|---|
| `{{SCENE_NN}}` | derived from `themes/<name>.yaml.page_plan_hints[NN-1]` + agent looking at `cells/cell-NN.png` |
| `{{ACTION_VERB_NN}}` | agent infers from page plan hint |

---

## Auto-persist after free-form input

After a successful free-form run has enough resolved configuration, the agent
writes the values back as a new spec yaml:

```
library/issue-specs/<slug>.yaml
```

This captures the inferred traits, looked-up style, agent-given theme/layout/
brand, optional article slug, and any user-provided overrides. The yaml lands
automatically — user can re-run with `"用 <slug> spec 跑"` to reproduce.

If the free-form run inferred a subject not in `library/subjects/`, the
agent ALSO auto-persists `library/subjects/<auto-name>.yaml` so future
specs can reference it by name.

---

## Validation

`tools/validation/spec_validate.py` checks:

1. spec.yaml `schema_version` is 1 or 2.
2. All required layer references exist as files (style is exempt — Tier 2 fallback).
3. Each layer yaml has the expected `schema_version` and required fields.
4. v1: `page_plan_hints` length matches layout page count.
5. v1: `storyboard_grid` rows*cols equals page count.
6. v1/v2: `subjects/<name>.yaml.reference_image` resolves to an existing file.
7. v2 with `article`: article copy is consistent with layout spread/text/image slots.

Run:

```bash
uv run python -m tools.validation.spec_validate library/issue-specs/cosmos-luna-01.yaml
uv run python -m tools.validation.spec_validate library/issue-specs/cosmos-luna-may-2026.yaml
```

Exit 0 if valid; non-zero with diagnostics if not.

---

## library/templates/

Prompt templates referenced by `lib.prompt_builder`. Each `.prompt.md` is a
markdown file using `{{PLACEHOLDER}}` tokens filled by
`lib.placeholder_resolver.build_placeholder_map`.

| Template | Used by |
|---|---|
| `storyboard.prompt.md` | Stage 3 storyboard (layout-driven 2×2 / 3×3 / 4×4) |
| `upscale_cover.prompt.md` | Stage 4 page 01 (cover) |
| `upscale_inner.prompt.md` | Stage 4 inner pages |
| `upscale_back.prompt.md` | Stage 4 final page (back cover) |

Adding a new prompt variant: drop the `.prompt.md` file in this directory,
add a corresponding `build_*_prompt` function to `lib/prompt_builder.py`,
and reference it from the relevant stage director.
