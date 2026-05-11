# openMagazine v0.3.1 — Regions as Shared Contract

> **Status:** spec (design only; awaiting empirical signal from a v0.3.0 live
> smoke run before scheduling implementation).
> **Date:** 2026-05-11
> **Predecessor:** v0.3.0 ([spec](2026-05-10-openmagazine-v0.3-editorial-engine-design.md),
> commit `7794053`).
> **Related:** overlay-safe-layout meta skill (`skills/meta/overlay-safe-layout.md`),
> landed in commit `5bb2792`.

## 1. Goal

Make the "where stuff lives on a spread" decision **a single piece of data
that three consumers all read** instead of an implicit convention re-encoded
in three different places:

| Consumer today | Reads what | Result |
|---|---|---|
| Image generation (`upscale_*.prompt.md`) | Free-prose `image_slot_overrides` + a soft `overlay_contract` hint in 5bb2792 | Model decides composition with vague awareness of overlay zones |
| HTML render (`library/layouts/_components/*.j2`) | CSS rules + inline `style=` with hand-tuned `mm` / `%` values | Components positioned by component author |
| Article copy (`library/articles/*.yaml` via `article-writer.md`) | `text_slots_required` declaring field names | Article drafted without knowing where the text will sit |

These three live on parallel tracks. They synchronize through human attention.
When they drift, the symptoms are: typography overlays the subject's face;
hero image hugs the wrong half of the spread; a captioned thumbnail strip
collides with body text.

The proposal: **promote "regions" to a first-class data layer**. Each spread
type ships a `regions.yaml` declaring every visible bounding box on the
spread — what fills it, where it sits in normalized coordinates, what role
it serves. All three consumers read this one file.

End-state: adding a new spread type means writing **one regions yaml +
one component j2 stub**. Tweaking layout proportions means **editing
coordinates in one place**. The image generation prompt automatically gets
told which parts of the canvas are calm zones for later text. CSS positioning
is no longer the source of truth — it's derived.

## 2. Non-Goals (v0.3.1.0)

- Replacing the existing 7 `_components/*.j2` files in one shot. Components
  opt in to regions-driven positioning; CSS-defined layout remains as
  fallback during migration.
- A visual region editor / GUI. Regions are authored in yaml.
- Cross-spread region declarations. A region is scoped to one spread.
- Animation / interaction. Regions are static print-time rectangles.
- Multi-language coexistence on the same region. Each region renders one
  language at a time (chosen by `brand.default_language`).
- Replacing the overlay-safe-layout meta skill outright. v0.3.1 subsumes its
  function but the meta skill stays as a higher-level rationale doc.

## 3. Background

### 3.1 What v0.3.0 ships

- 7 hand-crafted Jinja2 spread components, each baking layout into CSS
  declarations and inline `style=` blocks. See `library/layouts/_components/`.
- `text_slots_required` map at layout level says which article fields each
  spread type expects.
- Image slots declare `id`, `role`, `aspect`, `spread_idx`, `min_long_edge_px`.
  They know which spread they belong to but NOT where in the spread they sit.
- Overlay-safe-layout meta skill (5bb2792) introduces `page_overlay_contracts`
  at theme level: a free-form list of `subject_zone`, `protected_zones`,
  `reserved_overlay_zones`, `forbidden`. It's prose-shaped and applied in v1
  prompts only.

### 3.2 What v0.3.0 cannot do well

- Tell the image gen model **specifically** which rectangles of the canvas
  will receive a Title vs a Kicker vs a captioned thumbnail. The model only
  hears "keep left calm".
- Auto-position HTML components from data. Each `_components/*.j2` is
  hand-tuned with `position: absolute; top: 12mm; right: 18mm; …`.
- Validate that the article copy + image composition + HTML overlay agree.
  Today this is human eyeballing.
- Add a new spread type without writing **three** disconnected things
  (regions schema in head, .j2 component, image prompt notes).

### 3.3 What 5bb2792 already does and what it doesn't

The overlay-safe-layout meta skill **identifies the right problem** and
**solves half of it**:

| ✅ Done in 5bb2792 | ❌ Still ad-hoc |
|---|---|
| Concept that image gen + HTML must share zone info | Zone info is prose hints in theme yaml, not structured data |
| `protected_zones` with normalized `[x1,y1,x2,y2]` rects | Mixed with `subject_zone: "right-center"` named slot — two coordinate languages |
| Reserved overlay zones (`left-rail`, `bottom-strip` etc.) | Named slots are vibe, not coordinates — HTML can't position from them |
| Hint plumbed to v1 storyboard + upscale prompts | v2 path (editorial-16page) doesn't consume the hint yet |
| Lives in `theme.page_overlay_contracts` | But zoning is a per-issue per-page concern, not theme (cross-issue) |

This spec **lifts 5bb2792's intuition** into a structured shared schema.

## 4. Architecture Decisions

Six decisions, each with rationale + alternatives considered.

### 4.1 Coordinate system: normalized `[0, 1] × [0, 1]` per spread

| Decision | Rationale |
|---|---|
| Form | Each region declares `rect_norm: [x1, y1, x2, y2]` with values in `[0.0, 1.0]` representing fractions of the spread's bounding box |
| Why | Scale-independent. Same regions yaml works for A4 / Letter / custom page sizes. Already matches 5bb2792's `protected_zones.rect`. Easy to inspect ("right half" = `[0.5, 0.0, 1.0, 1.0]`) |
| Alternative considered | Absolute `mm` — tied to paper size, more brittle. Rejected. |
| Alternative considered | Grid columns (Swiss-style `span: 6, start: 0`) — adds grammar, requires column count per spread. Defer to v0.3.2 if grid systems prove valuable. |
| Edge case | Two-page spreads: the bounding box is the full spread (left page + right page joined). `x = 0.5` is the gutter. Single-page spread: bounding box is one page. |

### 4.2 File layout: one `<type>.regions.yaml` next to each `<type>.html.j2`

| Decision | Rationale |
|---|---|
| Form | `library/layouts/_components/<type>.regions.yaml` colocated with `<type>.html.j2` |
| Why | A region declaration and its component template are intrinsically coupled — they describe the same thing. Co-location matches how `_presets/` already pairs preview images with brand yamls. |
| Alternative considered | New top-level `library/regions/` directory — separates region from component, requires lookups. Rejected. |
| Alternative considered | Embed regions inline in the layout yaml (under each `spread_plan` entry) — convenient but bloats layout yaml and prevents component reuse across layouts. Rejected. |

### 4.3 Component vocabulary: closed registry

| Decision | Rationale |
|---|---|
| Form | `library/components/registry.yaml` lists every component name (e.g. `Kicker`, `Title`, `Lead`, `Body`, `BodyWithDropCap`, `PullQuote`, `Caption`, `CaptionedThumbnail`, `AccentRule`, `Folio`, `Masthead`, `CoverLine`) with its expected props |
| Why | Mirrors PPT skill's closed 22-layout pattern. Director skills can't invent new component names; if a new visual element is needed, it must be added to the registry first (small PR). Forces consistency and lets `article_validate` confirm regions only reference known components. |
| Alternative considered | Free-string component names — flexible but invites drift; would re-create the current "implicit convention" problem at a different layer. Rejected. |
| Alternative considered | Auto-discover from `_components/` j2 files — too magical; component names buried in markup are not searchable. Rejected. |

### 4.4 Region role taxonomy: 6 fixed roles

| Decision | Rationale |
|---|---|
| Roles | `image` / `image_grid` / `text` / `text_decorative` / `negative_space` / `accent` |
| Why | Each role implies how renderers handle the region. `image` slot pulls from `output/<slug>/images/spread-NN/<slot>.png`. `text` pulls from `article.spread_copy[N].<text_field>`. `text_decorative` is page number / masthead echo (not from article). `negative_space` reserves a calm zone. `accent` is decorative rule / pattern. |
| Alternative considered | Single role + many props — encodes the same info but loses semantic clarity. Rejected. |

### 4.5 Image-gen prompt injection: per-image, with sibling regions context

| Decision | Rationale |
|---|---|
| Form | When `prompt_builder_v2.build_upscale_prompt()` renders a prompt for slot `feature_hero` in spread 3, it embeds:<br>1. The slot's own region rect (where the image lives)<br>2. The OTHER regions in the same spread, with role + rect, marked as "do not paint into" |
| Why | Tells the model "this is your canvas, BUT regions A, B, C are reserved for HTML/PDF overlays — keep those rects calm and low-detail". Single source of truth for "where my image is" + "where other things will land". |
| Alternative considered | A separate overlay-contract field per upscale prompt (current 5bb2792 approach) — splits the data, harder to keep in sync. Rejected. |

### 4.6 Migration: one component at a time, coexist during transition

| Decision | Rationale |
|---|---|
| Form | Migrate `feature-spread` first as the pilot. The other 6 components keep working with current CSS-only positioning until each is migrated. |
| Why | De-risk. Pilot exposes hidden issues (drop-cap-in-positioned-box interactions, gutter handling, WeasyPrint quirks) before all 7 are touched. Rollback cheap. |
| Alternative considered | Big-bang migrate all 7 — high risk; if WeasyPrint surprises one component it taints the others. Rejected. |
| Alternative considered | Defer migration; only consume regions for image prompts, leave HTML unchanged — keeps the seam open, wastes most of the value. Rejected for v0.3.1.1+. |

## 5. Schema

### 5.1 `<type>.regions.yaml`

```yaml
# library/layouts/_components/feature-spread.regions.yaml
schema_version: 1
spread_type: feature-spread
pages_per_instance: 2

# Optional: bounding-box override. Default is full spread (single page or
# two-page). Useful when a spread has bleed margins handled per component.
bounds: full   # full | left-page | right-page | custom (custom requires rect)

regions:
  - id: hero_image
    rect_norm: [0.0, 0.0, 0.5, 1.0]        # left page, full height
    role: image
    image_slot: feature_hero               # links to layout.image_slots[*].id
    aspect: "3:4"
    image_prompt_hint: |
      The protagonist subject lives in this region. Sharp focus, primary
      lighting, full color.

  - id: kicker
    rect_norm: [0.55, 0.08, 0.95, 0.12]
    role: text
    component: Kicker
    text_field: kicker                     # links to article.spread_copy[*].kicker
    image_prompt_hint: "calm zone for a small uppercase mono label"

  - id: accent_rule_1
    rect_norm: [0.55, 0.13, 0.70, 0.135]
    role: accent
    component: AccentRule
    image_prompt_hint: "calm zone for a hairline rule"

  - id: title
    rect_norm: [0.55, 0.15, 0.95, 0.30]
    role: text
    component: Title
    text_field: title
    image_prompt_hint: |
      Uniform low-detail background. The title (large display serif) will
      be overlaid here.

  - id: lead
    rect_norm: [0.55, 0.32, 0.95, 0.42]
    role: text
    component: Lead
    text_field: lead

  - id: body
    rect_norm: [0.55, 0.45, 0.95, 0.83]
    role: text
    component: BodyWithDropCap
    text_field: body
    component_props:
      drop_cap: true
      hyphenate: true
      align: justify

  - id: captioned_strip
    rect_norm: [0.55, 0.86, 0.95, 0.98]
    role: image_grid
    image_slots: [feature_captioned.1, feature_captioned.2, feature_captioned.3]
    grid_cols: 3
    image_prompt_hint: |
      Three small 3:2 thumbnails will be placed here. Keep this strip
      visually calm.

  - id: folio
    rect_norm: [0.55, 0.99, 0.95, 1.0]
    role: text_decorative
    component: Folio
```

Required: `schema_version`, `spread_type`, `regions`. Each region needs `id`,
`rect_norm`, `role`. `role`-specific required fields below.

### 5.2 Role-specific required fields

| Role | Required | Optional |
|---|---|---|
| `image` | `image_slot`, `aspect` | `image_prompt_hint` |
| `image_grid` | `image_slots` (list), `grid_cols` | `image_prompt_hint` |
| `text` | `component`, `text_field` | `component_props`, `image_prompt_hint` |
| `text_decorative` | `component` | `component_props`, `image_prompt_hint` |
| `negative_space` | — | `image_prompt_hint` |
| `accent` | `component` | `component_props`, `image_prompt_hint` |

### 5.3 Component registry

```yaml
# library/components/registry.yaml
schema_version: 1

components:
  Kicker:
    description: Small uppercase label, mono font. e.g. "Chapter 01"
    typography_slot: kicker                # from brand.typography
    typical_size: "8-10pt"
    accepts_props: []

  Title:
    description: Large display headline
    typography_slot: display
    typical_size: "32-48pt"
    accepts_props: [align]

  Lead:
    description: Italic intro paragraph
    typography_slot: body
    typical_size: "11-13pt italic"
    accepts_props: []

  Body:
    description: Long-form running text
    typography_slot: body
    accepts_props: [hyphenate, align, columns]

  BodyWithDropCap:
    description: Body but first paragraph has raised initial
    extends: Body
    accepts_props: [drop_cap, drop_cap_lines, hyphenate, align]

  PullQuote:
    description: Large inset quote
    typography_slot: pull_quote
    accepts_props: [align]

  Caption:
    description: Small italic image caption
    typography_slot: caption

  CaptionedThumbnail:
    description: image + caption pair
    typography_slot: caption

  AccentRule:
    description: Horizontal hairline in accent color
    accepts_props: [thickness, width_pct]

  Folio:
    description: Page number + optional footer text
    typography_slot: page_number

  Masthead:
    description: Brand masthead (e.g. "MEOW LIFE")
    typography_slot: display

  CoverLine:
    description: Cover sub-headline
    typography_slot: display
```

A `text` region must reference a `component` that exists in this registry.
`article_validate` enforces this.

### 5.4 Article integration

No schema change to article yaml needed. The link is:

```
<type>.regions.yaml → regions[*].text_field
                           ↓
                  article.spread_copy[*].<text_field>
```

`article_validate.py` gains a new check: for every region with `role: text`
in the spread's regions, the article's matching `spread_copy` entry must
have `<text_field>` populated.

### 5.5 Persisted sidecar (per-spread)

After image generation, the persisted output gains a regions sidecar per
spread:

```
output/<slug>/prompts/spread-03/feature-spread.regions.json
```

```json
{
  "spread_idx": 3,
  "spread_type": "feature-spread",
  "regions": [
    {
      "id": "hero_image",
      "rect_norm": [0.0, 0.0, 0.5, 1.0],
      "role": "image",
      "image_slot": "feature_hero",
      "fulfilled_by": "output/<slug>/images/spread-03/feature_hero.png"
    },
    {
      "id": "title",
      "rect_norm": [0.55, 0.15, 0.95, 0.30],
      "role": "text",
      "component": "Title",
      "text_field": "title",
      "rendered_text": "DEPARTURE"
    }
    // …
  ]
}
```

This lets downstream tools (audit, A/B compare, retry-with-modified-region)
read a single file per spread instead of cross-referencing 3 yamls.

## 6. New file structure

```
~/github/openMagazine/
├── library/
│   ├── components/                        # NEW
│   │   ├── README.md
│   │   └── registry.yaml                  # component vocabulary
│   ├── layouts/
│   │   └── _components/
│   │       ├── feature-spread.html.j2     # existing (eventually rewritten)
│   │       ├── feature-spread.regions.yaml # NEW
│   │       ├── cover.html.j2
│   │       ├── cover.regions.yaml          # NEW
│   │       ├── pull-quote.html.j2
│   │       ├── pull-quote.regions.yaml     # NEW
│   │       ├── portrait-wall.html.j2
│   │       ├── portrait-wall.regions.yaml  # NEW
│   │       ├── toc.html.j2
│   │       ├── toc.regions.yaml            # NEW
│   │       ├── colophon.html.j2
│   │       ├── colophon.regions.yaml       # NEW
│   │       ├── back-cover.html.j2
│   │       └── back-cover.regions.yaml     # NEW
├── lib/
│   ├── regions_loader.py                  # NEW: load + validate <type>.regions.yaml
│   ├── prompt_builder_v2.py               # MODIFIED: inject regions into upscale prompts
│   └── prompt_persistence.py              # MODIFIED: write regions sidecar
├── tools/
│   └── validation/
│       ├── article_validate.py            # MODIFIED: cross-check regions text_field
│       └── regions_validate.py            # NEW: structural validation
├── schemas/
│   ├── regions.schema.json                # NEW: json-schema for regions yaml
│   └── components-registry.schema.json    # NEW
├── skills/
│   └── meta/
│       └── overlay-safe-layout.md         # MODIFIED: subsumed-by note pointing at regions
├── tests/
│   ├── unit/
│   │   ├── test_regions_loader.py         # NEW
│   │   ├── test_regions_validate.py       # NEW
│   │   └── test_prompt_builder_v2.py      # EXTENDED: regions injection cases
│   ├── integration/
│   │   └── test_render_dry_run.py         # EXTENDED: assert regions-driven output
│   └── contracts/
│       └── test_v2_pipelines.py           # EXTENDED: all 7 regions yamls validate
└── docs/
    ├── superpowers/specs/
    │   └── 2026-05-11-regions-as-shared-contract-design.md  # THIS FILE
    ├── regions-reference.md               # NEW: each spread type's regions
    └── component-registry-reference.md    # NEW: every component + props
```

## 7. Tooling additions

### 7.1 `lib/regions_loader.py`

```python
def load_regions(spread_type: str) -> dict:
    """Load library/layouts/_components/<type>.regions.yaml, validate
    against schemas/regions.schema.json, return dict.

    Raises FileNotFoundError if no regions yaml for this spread type
    (during migration, only feature-spread will return a dict; others
    raise and callers fall back to legacy CSS path).
    """

def regions_for_image_prompt(spread_type: str, image_slot_id: str) -> dict:
    """Return:
      {
        "own_region": <region dict for the image_slot>,
        "sibling_regions": [<every other region in the spread>]
      }
    Caller renders this into prompt text via prompt_builder_v2.
    """
```

### 7.2 `tools/validation/regions_validate.py`

Standalone CLI: `python tools/validation/regions_validate.py <type>` →
returns 0 if the regions yaml is valid; non-zero with diagnostics if not.
Checks:

- json-schema validates
- All `rect_norm` values in `[0, 1]`
- No two regions with overlapping rects above 5% area (configurable)
- All `text` regions reference components in the registry
- All `image` / `image_grid` regions reference image_slots that exist in the
  corresponding layout yamls

### 7.3 `prompt_builder_v2.build_upscale_prompt()` extension

```python
def build_upscale_prompt(
    *, role, spec, layers, slot_id, scene, aspect,
    regions_context: dict | None = None,   # NEW optional kwarg
) -> str:
    """If regions_context is provided, append a section to the prompt:

    'This image fills region <id> at rect (x1, y1, x2, y2). The same spread
     contains the following sibling regions (DO NOT paint into these areas
     — they receive HTML/PDF overlays in post): <list>'
    """
```

The director (upscale-director) is responsible for calling
`regions_loader.regions_for_image_prompt()` to build `regions_context` and
passing it in.

### 7.4 Component renderer (Jinja2 macro)

```jinja2
{# library/layouts/_components/_macros/region.j2.html #}
{% macro render_region(region, sc, slot_path, language) %}
  {%- set x1, y1, x2, y2 = region.rect_norm %}
  <div class="region region-{{ region.id }}"
       data-component="{{ region.component | default('') }}"
       style="position: absolute;
              left:   {{ x1 * 100 }}%;
              top:    {{ y1 * 100 }}%;
              width:  {{ (x2 - x1) * 100 }}%;
              height: {{ (y2 - y1) * 100 }}%;">
    {%- if region.role == 'image' %}
      <img src="{{ slot_path(region.image_slot) }}"
           style="width: 100%; height: 100%; object-fit: cover;">
    {%- elif region.role == 'text' %}
      {%- set text = sc[region.text_field][language] %}
      {{- render_component(region.component, text, region.component_props or {}) }}
    {%- elif region.role == 'image_grid' %}
      {{- render_image_grid(region) }}
    {%- elif region.role == 'accent' %}
      {{- render_accent(region) }}
    {%- elif region.role == 'text_decorative' %}
      {{- render_decorative(region.component, region.component_props or {}) }}
    {%- endif %}
  </div>
{% endmacro %}
```

Then `feature-spread.html.j2` becomes mostly a `{% for region in regions %}`
loop:

```jinja2
{%- from '_components/_macros/region.j2.html' import render_region %}

<section class="spread feature-spread" data-spread-idx="{{ spread_idx }}">
  <div class="spread-bounds" style="position: relative; height: var(--content-h);">
    {%- for region in regions %}
      {{ render_region(region, sc, slot_path, language) }}
    {%- endfor %}
  </div>
</section>
```

## 8. Pipeline integration

### 8.1 Stages that change

| Stage | Change |
|---|---|
| `research` | No change |
| `proposal` | No change |
| `articulate` | `article_validate` now requires text_field for every `role: text` region (stricter check) |
| `storyboard` | Storyboard prompt's `CELL_LIST` is augmented with regions context per spread (model knows multi-slot spreads have specific layouts) |
| `upscale` | Each upscale call's prompt embeds `regions_context` for its slot's spread (see 7.3) |
| `compose` | WeasyPrint renderer reads regions yaml for each spread, drives `_components/*.j2` via macros |
| `publish` | Writes `regions.json` sidecar per spread alongside `<slot>.prompt.txt` |

### 8.2 Director changes

`skills/pipelines/editorial-16page/`:

- **articulate-director.md** — add a step: "Confirm every `role: text`
  region in the spread's regions yaml has its `text_field` populated in
  the article entry."
- **storyboard-director.md** — add a step: "Load regions for each spread,
  pass to `build_storyboard_prompt_v2(... regions_by_spread=...)`."
- **upscale-director.md** — modify the per-slot loop:
  ```python
  from lib.regions_loader import regions_for_image_prompt
  regions_context = regions_for_image_prompt(spread_type, slot_id_short)
  prompt = build_upscale_prompt(
      role=s["role"], spec=spec, layers=layers,
      slot_id=full, scene=scene, aspect=s["aspect"],
      regions_context=regions_context,
  )
  ```
- **compose-director.md** — no agent-visible change; the change lives in
  the j2 template plus the macros.
- **publish-director.md** — add a step: "Persist per-spread
  `<slug>/prompts/spread-NN/<type>.regions.json` for downstream audit."

## 9. Compatibility & migration

### 9.1 Phased rollout

Five phases, each releasable independently.

| Phase | Scope | Risk |
|---|---|---|
| R1 (schema) | Author `regions.schema.json` + `registry.yaml` + `lib/regions_loader.py` + `tools/validation/regions_validate.py` + tests. No consumer wires yet. | Zero — additive only. |
| R2 (pilot) | Migrate `feature-spread`: write `feature-spread.regions.yaml`, rewrite `feature-spread.html.j2` to read regions via macro, wire upscale prompts to include regions context for `feature_hero` + `feature_captioned.{1,2,3}`. Other 6 spreads still on CSS path. | Medium — first j2 migration likely surfaces WeasyPrint quirks. |
| R3 (image prompts) | All 21 image slots get regions context in prompt (even for spread types where the j2 isn't migrated yet). Tells the model about spread layout even before HTML uses it. | Low — prompt additions only. |
| R4 (remaining 6) | Migrate cover / toc / pull-quote / portrait-wall / colophon / back-cover one at a time. | Medium per spread; cumulative test fatigue. |
| R5 (cleanup) | Update `skills/meta/overlay-safe-layout.md` to point at regions as canonical. Remove `theme.page_overlay_contracts` field from theme schema (or deprecate). Update `docs/spread-types-reference.md` to reference regions yamls. | Low. |

### 9.2 Coexistence during R2–R4

A component j2 is in one of two states:

- **Legacy (CSS-positioned)**: ships its old form. WeasyprintCompose
  invokes it as before. `text_field` mapping is done inline. No regions
  yaml — `regions_loader.load_regions(<type>)` returns None and renderer
  falls through to direct `{% include %}`.
- **Regions-driven**: ships a regions yaml + a thin j2 that delegates to
  `render_region` macro. `regions_loader.load_regions(<type>)` returns the
  dict.

`WeasyprintCompose` chooses path per spread type, not per issue. Mixing in
the same magazine is fine — feature-spread can be regions-driven while
cover is still legacy.

### 9.3 5bb2792's overlay contracts: deprecated, not removed

The `theme.page_overlay_contracts` field continues to be read by v1 prompt
builder (smoke-test-4page) until that pipeline is also migrated. v2 paths
prefer regions. The meta skill `skills/meta/overlay-safe-layout.md` gets
an "Update — superseded by regions" banner pointing at this spec.

## 10. Out of scope / future roadmap

- **Multi-region constraints** (e.g. "Title and Lead must align by baseline
  grid"): v0.3.2+. Would need a per-spread layout-solver pass.
- **Responsive regions** (e.g. region resizes when title is longer than
  predicted): v0.3.2+. Today: enforce length budgets in `article-writer.md`.
- **Region-aware reflow** (e.g. body region overflows → auto-pull from
  captioned strip): explicit out of scope. Article copy length is the
  author's responsibility.
- **Visual region inspector** (a debug HTML view that overlays region
  rects on the rendered PDF): nice-to-have, v0.3.2+.
- **Cross-spread region linkage** (e.g. spread 3's title typeface scaling
  feeds spread 6's): not planned.
- **Bleed-aware regions**: today `rect_norm` is relative to the spread
  bounds (after page margins). Bleed regions (full-bleed-with-3mm-overshoot)
  are a separate concept; if needed, declare via `bounds: full-bleed`.

## 11. Open questions / risks

### 11.1 Risks

- **Model respect for explicit rect coordinates is empirically unknown.**
  Telling Gemini 3 Pro Image "keep the rect (0.55, 0.10, 0.95, 0.13) calm"
  may not generalize as well as named-zone vocabulary
  ("top-right small band"). We assume rect → text translation in the
  prompt-builder helps. Live smoke test data needed before fully
  committing.
- **WeasyPrint absolute-positioning quirks at scale.** Migrating one
  component (R2) likely surfaces issues; ten regions per spread × seven
  spread types = 70 positioned rects per issue. Page-break behavior near
  high-y regions deserves explicit testing.
- **Article overflow.** A `BodyWithDropCap` region with a fixed height that
  receives 400 words instead of 250 either clips, overflows, or
  auto-shrinks. We need a policy. Tentative: clip and warn; article-writer
  enforces length budget upstream.
- **Drop-cap inside positioned div.** v0.3.0's drop-cap is a raised-initial
  inline trick. Inside an absolute-positioned div the line-height math has
  to still work. Should work but needs verification.
- **Two-page spread / gutter handling.** A region with `rect_norm` straddling
  `x = 0.5` will be physically split in print. Either forbid (validator
  rejects) or accept and tolerate the visible gutter line.

### 11.2 Open questions (resolve during implementation)

1. Should `image_prompt_hint` be a free string or a closed enum of canned
   phrases? Free-form is easy now; if model behavior is sensitive,
   canonicalize later.
2. Where do regions live in the resolved-layers dict in `lib/spec_loader.py`?
   New top-level `regions_by_spread_type` keyed by spread type seems clean.
3. Do we expose `region.id` as a CSS class for designer hooks?
   (`.region-hero_image`, etc.) Yes — useful for cross-issue debugging.
4. Component registry as yaml vs as Python module? yaml for now (easier
   diff/PR review); Python only if we need typed access patterns.
5. For overlapping regions (e.g. accent rule under title): do we explicitly
   support z-index? Probably yes; default `z_index: 0`, regions stack in
   declaration order with explicit overrides allowed.

## Appendix A: Worked example — feature-spread

### A.1 Three yamls + one j2 + one article

```yaml
# library/layouts/_components/feature-spread.regions.yaml
schema_version: 1
spread_type: feature-spread
pages_per_instance: 2
regions:
  - id: hero_image
    rect_norm: [0.0, 0.0, 0.5, 1.0]
    role: image
    image_slot: feature_hero
    aspect: "3:4"
  - id: kicker
    rect_norm: [0.55, 0.08, 0.95, 0.12]
    role: text
    component: Kicker
    text_field: kicker
  - id: title
    rect_norm: [0.55, 0.16, 0.95, 0.30]
    role: text
    component: Title
    text_field: title
  - id: lead
    rect_norm: [0.55, 0.33, 0.95, 0.43]
    role: text
    component: Lead
    text_field: lead
  - id: body
    rect_norm: [0.55, 0.46, 0.95, 0.83]
    role: text
    component: BodyWithDropCap
    text_field: body
  - id: captioned_strip
    rect_norm: [0.55, 0.86, 0.95, 0.98]
    role: image_grid
    image_slots: [feature_captioned.1, feature_captioned.2, feature_captioned.3]
    grid_cols: 3
```

```yaml
# excerpt from library/articles/cosmos-luna-may-2026.yaml
spread_copy:
  - idx: 3
    type: feature-spread
    kicker: {en: "CHAPTER 01", zh: "第一章"}
    title:  {en: "DEPARTURE",  zh: "启程"}
    lead:   {en: "She steps from…", zh: "她踏出…"}
    body:   {en: "…", zh: "…"}
    image_slot_overrides:
      feature_hero: "Luna at module windowsill, three-quarter front view"
      feature_captioned.1: "footprints in regolith, low sun"
      feature_captioned.2: "wide lunar plain, mid-frame"
      feature_captioned.3: "close-up of glove on rock"
```

### A.2 Rendered upscale prompt for `spread-03.feature_hero`

```
Subject: Luna, a healthy adult British Shorthair cat […traits…].

Scene: Luna at module windowsill, three-quarter front view.

Composition: This image fills region `hero_image` at rect
(0.0, 0.0, 0.5, 1.0) — the left page of the spread. The protagonist
subject lives in this region; sharp focus, primary lighting, full color.

The same spread contains 5 sibling regions that receive HTML/PDF overlays
after generation. DO NOT paint into these areas; keep them calm and low-
detail (model: do not generate typography or layout chrome here):

- `kicker` (right page, top ~8%-12%): calm zone for a small uppercase
  mono label
- `title` (right page, ~16%-30%): uniform low-detail background; the
  title text "DEPARTURE" will be overlaid here
- `lead` (right page, ~33%-43%): calm zone for italic intro paragraph
- `body` (right page, ~46%-83%): no important detail; long-form body
  text with drop cap will be overlaid here
- `captioned_strip` (right page, bottom ~86%-98%): negative space; three
  small 3:2 thumbnails will be placed here

Camera: shot on Sony Alpha 7R V with Sigma 35mm f/1.4 Art lens. Raw
uncorrected file, no LUTs.

Style: Annie Leibovitz, Hasselblad H6D-100c style.

Aspect: 3:4.

Negative prompt: cartoonish, AI-looking, plastic skin/fur, over-smoothed,
glossy CGI, anime cute, oversized eyes, beauty-filter, plush appearance,
3D render look, oily highlights, painted whiskers, mournful expression,
droopy eyes, deformed anatomy, garbled typography, watermarks, logos,
visible page numbers from storyboard cell. Do not paint readable text,
mock magazine layouts, or UI elements anywhere in the image.
```

### A.3 Rendered HTML for the same spread

```html
<section class="spread feature-spread" data-spread-idx="3">
  <div class="spread-bounds"
       style="position: relative; height: 250mm;">

    <div class="region region-hero_image"
         data-component=""
         style="position: absolute;
                left: 0%; top: 0%; width: 50%; height: 100%;">
      <img src="output/.../images/spread-03/feature_hero.png"
           style="width: 100%; height: 100%; object-fit: cover;">
    </div>

    <div class="region region-kicker" data-component="Kicker"
         style="position: absolute;
                left: 55%; top: 8%; width: 40%; height: 4%;">
      <span class="kicker">CHAPTER 01</span>
    </div>

    <div class="region region-title" data-component="Title"
         style="position: absolute;
                left: 55%; top: 16%; width: 40%; height: 14%;">
      <h2 class="title">DEPARTURE</h2>
    </div>

    <!-- … lead / body / captioned_strip … -->

  </div>
</section>
```

## Appendix B: Component registry skeleton (first cut)

| Component | Typography slot | Notable props |
|---|---|---|
| `Kicker` | `kicker` | — |
| `Title` | `display` | `align` |
| `Lead` | `body` (italic) | — |
| `Body` | `body` | `hyphenate`, `align`, `columns` |
| `BodyWithDropCap` | `body` + `drop_cap` | `drop_cap`, `drop_cap_lines` |
| `PullQuote` | `pull_quote` | `align` |
| `Caption` | `caption` | — |
| `CaptionedThumbnail` | `caption` (caption text) | `aspect` (image) |
| `AccentRule` | — | `thickness`, `width_pct` |
| `Folio` | `page_number` | `position` |
| `Masthead` | `display` | — |
| `CoverLine` | `display` | `align` |

## Self-review checklist

- ✅ No "TBD" / "TODO" in normative sections
- ✅ Cross-references: every region in 5.1 example references a real
  `text_field` (kicker / title / lead / body) that exists in v0.3.0 article
  schema; every component in 5.1 references registry entries in 5.3.
- ✅ Migration plan is incremental (5 phases, each releasable)
- ✅ Empirical risks (11.1) acknowledged: rect-coord model respect, drop-cap
  positioning interactions, gutter handling, overflow
- ✅ Coexistence with 5bb2792 explicit (9.3) — not removing the overlay
  contract field; deprecating via banner
- ✅ Estimated implementation cost surfaced in 9.1 phases
- ✅ Component registry as closed set (4.3) for consistency with PPT-skill
  philosophy

## Next step

1. **Do not implement** until at least one live editorial-16page smoke run
   has happened with v0.3.0 (`commit 7794053`). The smoke run will show
   whether prose-shaped overlay hints are sufficient, marginal, or broken
   — the answer informs how aggressive R3 should be.

2. After the smoke run, file `docs/superpowers/plans/2026-05-XX-regions-as-shared-contract.md`
   using `superpowers:writing-plans`, focused on R1–R5 phases. Empirical
   findings from the smoke run populate the open questions (11.2).

3. Implement via `superpowers:executing-plans` / `subagent-driven-development`.
   R1 + R2 + R3 are independent and good candidates for parallel sub-agent
   dispatch; R4's 6 spread migrations can also run in parallel after R2 is
   green.
