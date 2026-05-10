# Library Schema

Simple mode accepts two input sources:

- **Free-form** — user one-liner + photo. Agent infers traits, looks up styles
  via Author Obligation 2 (Tier 1/2/3), gives sensible defaults for theme /
  layout / brand.
- **Spec yaml** — user writes `library/issue-specs/<name>.yaml` referencing
  6 layers (subject / style / theme / layout / brand + spec-level overrides).
  Agent reads the spec, resolves layers, fills the placeholder map.

Both sources feed the same Phase 1+ pipeline (storyboard → split → gate → 4K → PDF).

Free-form runs **auto-persist** their resolved configuration as a new
`library/issue-specs/<slug>.yaml` after the storyboard gate, so subsequent
runs of the same issue can use spec input directly.

---

## 6 layers (5 explicit + styles)

```
styles/             风格库 (top-level; covered by styles/README.md)
library/
├── subjects/       protagonist 卡片 — name + traits + reference photo
├── themes/         主题世界 — theme_world + lighting_principles + page_plan_hints
├── layouts/        版面参数 — page_count + aspect + storyboard_grid + typography_mode
├── brands/         杂志品牌 — masthead + url + persona
└── issue-specs/    一站式 spec — 引用上面 5 层 + spec-level overrides
```

The styles layer is **orthogonal**: it carries `style_anchor` text injected
verbatim into all prompts. Styles are looked up by trigger keyword (Author
Obligation 2). The other 4 layers + spec compose deterministically.

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

After a successful free-form run reaches the storyboard gate (Phase 2.5),
the agent writes the resolved values back as a new spec yaml:

```
library/issue-specs/<slug>.yaml
```

This captures the inferred traits, looked-up style, agent-given theme/layout/
brand, and any user-provided overrides. The yaml lands automatically — user
can re-run with `"用 <slug> spec 跑"` to reproduce.

If the free-form run inferred a subject not in `library/subjects/`, the
agent ALSO auto-persists `library/subjects/<auto-name>.yaml` so future
specs can reference it by name.

---

## Validation

`tools/validation/spec_validate.py` checks:

1. spec.yaml schema_version == 1
2. All 5 layer references exist as files (style is exempt — Tier 2 fallback)
3. Each layer yaml's schema_version == 1 and required fields present
4. `themes/<name>.yaml.page_plan_hints` length == `layouts/<layout>.yaml.page_count`
5. `layouts/<layout>.yaml.storyboard_grid` rows*cols == page_count
6. `subjects/<name>.yaml.reference_image` resolves to an existing file (long edge ≥ 1024 if PIL is available)

Run:

```bash
python tools/validation/spec_validate.py library/issue-specs/cosmos-luna-01.yaml
```

Exit 0 if valid; non-zero with diagnostics if not.
