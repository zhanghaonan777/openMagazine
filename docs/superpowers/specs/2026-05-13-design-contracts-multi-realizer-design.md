# openMagazine v0.3.2 — Design Contracts & Multi-Realizer Output

> **Status:** spec (design only; awaiting agreement before plan).
> **Date:** 2026-05-13
> **Predecessor:** v0.3.1 ([spec](2026-05-11-regions-as-shared-contract-design.md),
> commit `2a7246b`).
> **Empirical anchor:** Codex Presentations skill end-to-end test on
> `cosmos-luna-may-2026`, thread `019e1729-3645-7c21-8c17-ba04f8164388`
> (2026-05-13). The test confirmed Presentations independently produces a
> 9-slide editorial deck whose layouts directly parallel our 7 spread
> types, plus exposes structured artifacts (profile-plan, design-system,
> text-safe contracts, layout JSONs, imagegen prompt files,
> contact-sheet, layout-quality QA) that map cleanly onto our existing
> data-layer pattern.

## 1. Goal

Solve three constraints simultaneously:

1. **Framework fit.** Any new output backend (PPTX, HTML deck, video,
   web preview) must be integrable through the same data-layer pattern
   the rest of openMagazine uses — yaml in, sidecar JSON out, contract
   tests in `tests/contracts/`. No black-box "skill plugged into the
   pipeline."
2. **Design intelligence retention.** Codex Presentations skill embeds
   ~10 years of editorial design judgment into a 743-line SKILL.md +
   7 deck profiles. Whatever we add must not regress on that judgment.
3. **Persistence & controllability.** Every design decision (profile
   chosen, typography substitution chain, text-safe contracts, brand
   authenticity gates, layout quality thresholds) must live as a
   committed yaml under `library/`, not as prose hidden in agent
   markdown or skill internals. A future engineer reading the repo cold
   should be able to find every decision.

End-state: openMagazine treats **design contracts** as a first-class
shared data layer (parallel to v0.3.1's regions data layer), and
multiple realizers (WeasyPrint for PDF, Presentations skill for PPTX,
future HTML / video) consume the same contracts. Adding a new output
format = adding a new realizer + an `output_selector` branch. Adding a
new design vocabulary = adding a profile yaml.

## 2. Non-Goals (v0.3.2.0)

- Replacing the Codex Presentations skill or reimplementing its design
  logic in-house. We use it as a realizer.
- A visual deck editor / GUI. All authoring stays in yaml + Codex CLI.
- Multi-language deck output. Same constraint as v0.3.1: one language
  per issue.
- New deck profiles beyond what's needed to ship the first parallel
  output. v0.3.2 ships `consumer-retail` (matches our existing
  editorial use case); other 6 profiles (`finance-ir`,
  `product-platform`, `gtm-growth`, `engineering-platform`,
  `strategy-leadership`, `appendix-heavy`) defer to v0.3.3+.
- HTML deck output (the `op7418/guizang-ppt-skill` aesthetic).
  Architecture supports it; implementation defers.
- Video / animation output. Architecture supports it; implementation
  defers.
- CMYK PPTX output. v0.3.2 ships RGB PPTX only.

## 3. Background

### 3.1 What v0.3.1 ships

- 7 regions yamls (`library/layouts/_components/<type>.regions.yaml`)
  declaring per-spread region rectangles, components, text fields.
- A closed component registry (`library/components/registry.yaml`,
  15 entries).
- `pdf_selector.py` routing by `layout.schema_version` to ReportLab (v1)
  or WeasyPrint (v2).
- `lib/prompt_persistence.py` saves prompts + a run manifest under
  `output/<slug>/prompts/`.
- Three consumers (image gen, HTML render, article validation) read the
  same regions data — the first time openMagazine lifted a decision out
  of code into a shared yaml.

### 3.2 What v0.3.1 cannot do well

- **Single output target.** A spec → one PDF. There is no notion of
  "the same article + brand + style can be expressed as both a magazine
  PDF and a deck PPTX."
- **Design judgment is implicit.** brand.yaml.typography lists font
  families, but doesn't encode "when this font isn't available, fall
  back to X; when the deck looks generic, regenerate; when text
  overlays an image, require negative space here." Those rules exist
  in our heads or in scattered prose.
- **No profile concept.** We hard-coded the assumption that every issue
  is image-led editorial. A finance-style or engineering-style magazine
  would require parallel work in 5 places.
- **Imagegen prompts are siloed.** Our `output/<slug>/prompts/` writes
  text files but they're not consumable by Codex's `image_gen.imagegen`
  tool directly; they're audit artifacts only.

### 3.3 What the Presentations smoke test (2026-05-13) showed

A 9-slide deck of `cosmos-luna-may-2026` ran in Codex CLI and produced
the following structured artifacts that map onto openMagazine's data
layer:

| Presentations artifact | openMagazine analog | Status |
|---|---|---|
| `profile-plan.txt` (chose `consumer-retail`) | NEW — we don't have a profile layer | gap to fill |
| `design-system.txt` (typography + palette + grammar) | `brand.yaml.typography` + scattered prose | partial — we have typography pack, not full design system |
| `text_safe_area` / `text_safe_areas` / `text_safe_contract` keys in layout JSON | `regions.yaml`'s `reserved_overlay_zones` | direct isomorph; we lack the `text_safe_contract.rule` prose |
| `prompts/slide-NN.prompt.txt` (JSON spec + prose) | `output/<slug>/prompts/...prompt.txt` | partial — we have prose only, not the size/quality JSON spec |
| `font-substitutions.txt` (Playfair → Georgia fallback) | NEW — we don't track font fallback | gap to fill |
| `qa/layout-quality.txt` (check_layout_quality.mjs output) | NEW — we want this as v0.3.1 followup | gap to fill (we verified the script standalone-works) |
| `qa/comeback-scorecard.txt` | NEW — we don't do scoring | gap to fill |
| 9 distinct slide layouts at thumbnail scale (contact sheet test) | our 7 spread types from regions yamls | parallel — Presentations independently invented 7 close to our 7 |

The smoke test's most important finding: **Presentations and
openMagazine arrived at near-identical editorial layouts from the same
inputs**. They are not competing aesthetics — they are two realizers
of the same design intent.

## 4. Architecture Decisions

Six decisions, each Decision / Rationale / Alternative / Risk.

### 4.1 Two new data layers: `profiles/` (closed set) + `design-systems/` (per-issue)

| Decision | Rationale |
|---|---|
| Form | `library/profiles/<name>.yaml` (closed registry, ships with repo, 1-2 entries in v0.3.2). `library/design-systems/<slug>.yaml` (per-issue, auto-persisted after stage 3 like spec yaml is today). |
| Why split | Profile is a **type of publication** (consumer-retail / finance-ir / engineering-platform / …). Design-system is **this particular issue's resolved decisions** (specific font fallback chain, specific text-safe rule wording, specific accent color). One profile → many design-systems. |
| Mapping to Presentations | profile → matches Presentations's 7-profile router 1:1. design-system → matches Presentations's `design-system.txt` artifact 1:1, but pre-computed (we tell Presentations what it is, not let it decide). |
| Alternative considered | Single combined yaml. Rejected — couples reusable type info to per-issue specifics, blocks reuse. |
| Alternative considered | Profile baked into pipeline yaml. Rejected — pipeline is the workflow, profile is the publication type; orthogonal. |
| Risk | Premature schema lock. Mitigation: v0.3.2 ships profile fields as a strict subset of Presentations's profile.md headings, so the schema is empirically grounded, not invented. |

### 4.2 Field translation: extract Presentations's design intelligence into our yaml

| Decision | Rationale |
|---|---|
| Source | Presentations skill's per-profile markdown (`profiles/<name>.md`, e.g. `consumer-retail.md`) + `design-system-template.md` + `SKILL.md` Phase 2 "Design System Lock" section. |
| Target | `library/profiles/<name>.yaml` (translated, structured) + `library/design-systems/<slug>.yaml` (per-issue resolved). |
| Why translate, not link | Profiles markdown is judgment + prose. We extract the *structural* parts (required proof objects, text-safe rules, brand authenticity gates) into yaml; we leave the *judgment* part (specific phrasings) in agent skills under `skills/meta/`. |
| Alternative considered | Read Presentations markdown directly at runtime. Rejected — couples us to the Presentations skill's exact file layout, version, and Codex bundled-runtime path. |
| Risk | Translation loses judgment. Mitigation: keep judgment-heavy prose in our `skills/meta/<profile-name>-author.md` (a sibling to `article-writer.md`), so the agent has the full context when authoring. Yaml carries the enforceable rules; markdown carries the taste. |

### 4.3 `output_selector` replaces `pdf_selector`, routing by `spec.output_target`

| Decision | Rationale |
|---|---|
| Form | `tools/output/output_selector.py` (or rename `tools/pdf/pdf_selector.py`) routes based on `spec.output_target`: `"a4-magazine"` (default, v0.3.1 behavior), `"deck-pptx"` (new), future `"deck-html"`, `"video"`. |
| Why generalize | Same input data (article + regions + design-system) can produce different output formats. The router is the dispatcher; realizers are the workers. |
| Alternative considered | Multiple parallel pipelines (`editorial-16page-pdf` vs `editorial-16page-deck`). Rejected — duplicates stages 1-5 entirely. |
| Backward compat | If `spec.output_target` is unset, default to `"a4-magazine"`. Existing v0.3.1 specs keep working. |

### 4.4 Presentations realizer adapter (`tools/output/presentations_adapter.py`)

| Decision | Rationale |
|---|---|
| Role | Adapter takes openMagazine's resolved layers (`spec`, `article`, `brand`, `regions`, `design-system`, `profile`) → invokes Codex Presentations skill via the agent loop (the director writes the appropriate prompt) → consumes Presentations's structured artifacts → maps them back into `output/<slug>/`. |
| Key contract | **We compute the design-system; Presentations does not redecide it.** We pass profile name, brand color, text-safe rules, font fallback chain, etc. as inputs. Presentations only handles layout composition + PPTX export. |
| Why this split | Keeps design intelligence under our control (constraint #3). Lets Presentations do what it's best at: artifact-tool's PPTX layout engine. |
| Implementation detail | The adapter cannot directly invoke Presentations from a Python `tool.run()` (that requires Codex CLI runtime). Instead, the `compose-director-deck.md` skill instructs the agent to invoke Presentations with a pre-rendered prompt. The Python adapter is responsible for reading back Presentations's `outputs/<thread>/...` artifacts. |
| Alternative considered | Run Presentations entirely outside the pipeline as a sibling tool. Rejected — would lose the schema-validated artifact integration. |
| Risk | Adapter brittleness if Presentations changes its artifact paths. Mitigation: contract test `tests/contracts/test_presentations_adapter.py` asserts the expected artifact tree exists after a smoke run; failures surface early. |

### 4.5 Imagegen prompt files: upgrade format to be Codex-consumable

| Decision | Rationale |
|---|---|
| Today (v0.3.1) | `output/<slug>/prompts/<slot>.prompt.txt` = prose only. Audit-only. |
| v0.3.2 | Upgrade to Presentations's format: JSON spec block + Markdown prose block in same file. The JSON spec contains `intended_output`, `reference_image`, `size`, `quality`, `format`, `background`, `moderation`. |
| Why | (a) Codex's `image_gen.imagegen` tool can read the JSON spec directly, eliminating the prose-to-arguments translation step in directors. (b) PDF and PPTX realizers can share the same prompt files — the prompt is paper-independent. |
| Alternative considered | Keep prose-only. Rejected — wastes the chance to make prompts production artifacts, not just audit artifacts. |
| Risk | Format drift if Presentations changes the JSON schema. Mitigation: snapshot the format we expect in `schemas/imagegen_prompt.schema.json`; validator catches drift. |

### 4.6 Font substitution + brand authenticity gates as first-class data

| Decision | Rationale |
|---|---|
| Font substitution | `design-system.yaml` has a `font_resolution_chain` field per slot: `[desired_family, fallback_1, fallback_2, system_safe]`. At render time, we resolve each chain via `fc-match` (Linux/Mac) or platform equivalent, and write the resolution log to `output/<slug>/font-resolution.json`. Presentations realizer reads this log; WeasyPrint renderer reads the resolution log to ensure same fallback. |
| Brand authenticity gate | `design-system.yaml.brand_authenticity` lists forbidden patterns: `"do_not_generate"` (e.g. logos, mascots, app icons), `"do_not_approximate"` (signature marks). Realizers (both WeasyPrint and Presentations) must respect this list; image gen prompts are pre-checked against it. |
| Why first-class | These two are the two most common failure modes when authoring (font not installed → Verdana fallback; AI-drawn logo → trademark concern). Promoting them to yaml + validator catches both at compose time, not at human-review time. |
| Alternative considered | Leave font fallback implicit (let renderer's default substitution win). Rejected — silent, untrackable, irreproducible. |
| Risk | `fc-match` invocation differs by platform; CI environment may differ from local. Mitigation: vendor a font resolution table + check at install time, fail loudly. |

## 5. Schema

### 5.1 `library/profiles/<name>.yaml`

```yaml
# library/profiles/consumer-retail.yaml — extracted from Presentations
# skills/.../profiles/consumer-retail.md plus our editorial conventions

schema_version: 1
name: consumer-retail
display_name:
  en: "Consumer / Retail / Editorial"
  zh: "消费品 / 零售 / 编辑型"

# Maps to Presentations profile router
presentations_profile: consumer-retail   # 1:1 link to Codex skill

# Hard gates: from consumer-retail.md
hard_gates:
  - rule: image_led_subject_gate
    description: |
      Use sourced imagery with provenance, user-provided assets, or
      imagegen — never Python drawings or programmatic vector
      illustrations for the primary subject.
    applies_when: "subject is visually inspectable (animal, person, product, place, food)"
  - rule: brand_authenticity_gate
    description: |
      Do not generate / approximate logos / mascots / app icons /
      signature marks. Use verified assets or omit.
    forbidden_generations:
      - logo
      - mascot
      - app_icon
      - signature_mark
      - product_ui_screenshot

# Required proof objects(每个 spread 必须至少一个)
required_proof_objects:
  - image_hero_or_look_page
  - product_or_look_rationale
  - audience_journey
  - editorial_hierarchy

# Recommended palette features
visual_preferences:
  paper_color: warm_neutral_or_deep_ink     # not pale dashboard white
  display_face: refined_serif_or_didone
  body_face: utilitarian_sans_or_humanist_serif
  meta_face: monospace
  layout: open_composition                  # not repeated cards
  rules: hairline                           # not box outlines
  data_labels: direct                       # not heavy legends

# Banned motifs
banned_motifs:
  - corporate_scorecard
  - faux_kpi_grid
  - generic_saas_dashboard
  - consulting_card_grid

# Required spread types for this profile
spread_types_required:
  - cover
  - feature_spread       # at least 1
spread_types_optional:
  - toc
  - pull_quote
  - portrait_wall
  - colophon
  - back_cover
```

### 5.2 `library/design-systems/<slug>.yaml` (per-issue, auto-persisted)

```yaml
# library/design-systems/cosmos-luna-may-2026.yaml — resolved at stage 3
# (articulate) and persisted; subsequent stages read it.

schema_version: 1
slug: cosmos-luna-may-2026
profile: consumer-retail                    # → library/profiles/consumer-retail.yaml
brand: meow-life                            # → library/brands/meow-life.yaml
inheritance:
  base_brand_typography: true               # inherits brand.typography pack
  base_brand_print_specs: true
  base_brand_visual_tokens: true

# Per-issue overrides + resolution
typography_resolution:
  display:
    desired_family: "Playfair Display"
    fallback_chain:
      - "Source Serif 4"
      - "Georgia"
      - "Times New Roman"
    resolved_at_render: null                # filled at compose time
  body:
    desired_family: "Source Serif 4"
    fallback_chain:
      - "Georgia"
      - "Times New Roman"
    resolved_at_render: null
  meta:
    desired_family: "IBM Plex Mono"
    fallback_chain:
      - "Menlo"
      - "Courier"
    resolved_at_render: null

# Text-safe contracts (extends regions yaml)
text_safe_contracts:
  default_rule: |
    When text overlays or sits inside a generated visual field, keep
    clean negative space inside each text-safe rectangle.
  per_spread_overrides: {}                  # rare; mostly use regions.yaml

# Brand authenticity gates (from profile but per-issue tunable)
brand_authenticity:
  do_not_generate:
    - logo
    - mascot
    - app_icon
  do_not_approximate:
    - "MEOW LIFE wordmark"
    - "Luna's specific face proportions"
  asset_provenance_required:
    - cover_hero
    - feature_hero
  asset_provenance_optional:
    - feature_captioned_thumbnails

# Layout quality thresholds
layout_quality:
  min_gap_px: 16
  max_text_image_overlap_px: 25
  max_text_text_overlap_px: 10
  fail_on: error                            # error / warn / never

# Output targets
output_targets:
  - format: a4-magazine                     # default WeasyPrint PDF
    realizer: weasyprint
    page_size: A4
    bleed_mm: 3
  - format: deck-pptx                       # NEW v0.3.2
    realizer: presentations
    slide_size: 1280x720
    page_count: 9                           # one per spread

# Contact-sheet rubric
contact_sheet_rubric:
  distinct_layouts_required: 7              # of 9 slides, ≥7 must look different at thumbnail
  template_collapse_threshold: 3            # no more than 3 slides share same layout grammar
```

### 5.3 Imagegen prompt file format (v0.3.2 upgrade)

```markdown
# Codex Imagegen Prompt

Use the Codex imagegen tool with this prompt. Do not call external image APIs from scripts.

\`\`\`json
{
  "intended_output": "output/cosmos-luna-may-2026/images/spread-03/feature_hero.png",
  "reference_image": "output/cosmos-luna-may-2026/refs/protagonist-1.jpg",
  "size": "3500x4666",
  "quality": "high",
  "format": "png",
  "background": "auto",
  "moderation": "auto"
}
\`\`\`

## Prompt

Subject: Luna, a healthy adult British Shorthair cat, real proportions, …
Scene: Luna at module windowsill, three-quarter front view, …
Composition: maintain region 'hero_image' (rect_norm [0, 0, 0.5, 1]) …
DO NOT paint into reserved overlay zones: title (rect [0.55, 0.15, 0.95, 0.30]), …

[role-template-rendered prose]

Negative prompt: cartoonish, AI-looking, plastic skin/fur, …
```

This format **directly consumable by Codex `image_gen.imagegen`** (the JSON
block tells it where to write, what size, etc.) AND readable as audit /
debugging artifact (the Markdown prose section).

## 6. New file structure

```
~/github/openMagazine/
├── library/
│   ├── profiles/                          # NEW
│   │   ├── README.md
│   │   └── consumer-retail.yaml           # v0.3.2 ships 1; v0.3.3+ adds 6 more
│   ├── design-systems/                    # NEW (mostly auto-persisted)
│   │   ├── README.md
│   │   └── cosmos-luna-may-2026.yaml      # example, hand-written
│   └── (existing layers unchanged)
├── lib/
│   ├── design_system_loader.py            # NEW
│   ├── font_resolver.py                   # NEW: wraps fc-match
│   └── (existing modules)
├── tools/
│   ├── output/                            # NEW (replaces tools/pdf/)
│   │   ├── output_selector.py             # generalized router
│   │   ├── weasyprint_compose.py          # moved from tools/pdf/
│   │   ├── reportlab_compose.py           # moved from tools/pdf/
│   │   └── presentations_adapter.py       # NEW
│   └── validation/
│       ├── design_system_validate.py      # NEW
│       └── (existing)
├── schemas/
│   ├── profile.schema.json                # NEW
│   ├── design-system.schema.json          # NEW
│   └── imagegen_prompt.schema.json        # NEW (snapshots Presentations format)
├── skills/
│   ├── pipelines/
│   │   └── editorial-16page/
│   │       ├── (existing 7 directors)
│   │       └── compose-director-deck.md   # NEW (PPTX path)
│   └── meta/
│       ├── design-system-author.md        # NEW (sibling to article-writer.md)
│       └── (existing)
├── pipeline_defs/
│   ├── editorial-16page.yaml              # MODIFIED: supports multi-output
│   └── (existing)
└── docs/
    ├── superpowers/specs/
    │   └── 2026-05-13-design-contracts-multi-realizer-design.md  # THIS FILE
    ├── design-system-reference.md         # NEW (post-implementation)
    └── profiles-reference.md              # NEW
```

## 7. Tooling additions

### 7.1 `lib/design_system_loader.py`

```python
def load_profile(name: str) -> dict:
    """Load library/profiles/<name>.yaml, validate against schema."""

def load_design_system(slug: str) -> dict:
    """Load library/design-systems/<slug>.yaml."""

def resolve_design_system(
    spec: dict, layers: dict, profile_name: str | None = None
) -> dict:
    """Compose the per-issue design-system from spec + profile + brand
    inheritance. Returns the dict that gets persisted to disk and read
    by realizers."""
```

### 7.2 `lib/font_resolver.py`

```python
def resolve_font(
    desired_family: str, fallback_chain: list[str]
) -> dict:
    """Walk the chain via fc-match (or platform equivalent); return
    {requested, matched, fallback_used: bool, reason}."""

def resolve_typography_pack(design_system: dict) -> dict:
    """Run resolve_font for every slot in design_system.typography_resolution.
    Returns a resolution log; writes to output/<slug>/font-resolution.json
    when run during compose stage."""
```

### 7.3 `tools/output/presentations_adapter.py`

```python
class PresentationsAdapter(BaseTool):
    """Realizer adapter for Codex Presentations skill.

    The adapter does NOT directly invoke Presentations (that requires
    Codex CLI runtime). Instead it:
      1. pre-computes profile + design_system + regions as Presentations
         input
      2. writes a prompt-builder dispatch file the director skill follows
      3. after Presentations finishes, reads back the expected artifact
         tree (profile-plan.txt, design-system.txt, slides/, layout/,
         preview/, output/*.pptx)
      4. validates artifact integrity via contract test
      5. copies the final .pptx into output/<slug>/deck/
    """
    capability = "output_realizer"
    provider = "presentations"
    output_target = "deck-pptx"
```

### 7.4 `tools/output/output_selector.py`

Replaces `tools/pdf/pdf_selector.py`. Routes by `spec.output_target`:

| target | realizer | output |
|---|---|---|
| `a4-magazine` (default) | `WeasyprintCompose` | `output/<slug>/magazine.pdf` |
| `photobook-plain` | `ReportlabCompose` | `output/<slug>/magazine.pdf` (v1 path) |
| `deck-pptx` | `PresentationsAdapter` | `output/<slug>/deck/<slug>.pptx` |
| (future) `deck-html` | `HTMLDeckCompose` | `output/<slug>/deck/<slug>.html` |
| (future) `video-mp4` | `VideoComposer` | `output/<slug>/video/<slug>.mp4` |

### 7.5 `tools/validation/design_system_validate.py`

CLI: `python tools/validation/design_system_validate.py library/design-systems/<slug>.yaml`. Checks:

- json-schema validates
- `profile` references an existing `library/profiles/<name>.yaml`
- `brand` references an existing `library/brands/<name>.yaml`
- Every `typography_resolution.*.fallback_chain` has at least 1
  system-safe option
- `output_targets[*].realizer` is in the known realizer registry
- `brand_authenticity.do_not_generate` entries match the profile's
  `hard_gates.brand_authenticity_gate.forbidden_generations` (no new
  inventions per issue)

## 8. Pipeline integration

### 8.1 Where the new stage 3.5 sits

```
research → proposal → articulate ─┬─→ storyboard → upscale → compose → publish
                                  │
                                  └─→ NEW: design-system resolution
                                      ├─ pick profile (default from layout)
                                      ├─ resolve typography chain
                                      ├─ resolve brand authenticity gates
                                      ├─ persist design-systems/<slug>.yaml
                                      └─ run design_system_validate
```

Articulate is the natural home because:

- it's already a checkpoint stage (user sees + edits article)
- it runs after spec + brand + theme are loaded (everything we need)
- it runs before storyboard / upscale (the design-system can shape
  imagegen prompts)

### 8.2 Multi-output at compose stage

`compose-director.md` becomes the orchestrator:

```python
spec_targets = layers["design_system"]["output_targets"]
for target in spec_targets:
    realizer = OutputSelector().choose_backend(target=target)
    realizer.run(issue_dir, layers, design_system=...)
```

For `a4-magazine`: WeasyprintCompose runs (same as v0.3.1).
For `deck-pptx`: PresentationsAdapter triggers the new
`compose-director-deck.md` skill, which guides the agent to invoke
Presentations with our pre-computed inputs.

Both can run sequentially in the same stage. Same issue dir.

### 8.3 Director changes

| Director | Change |
|---|---|
| `research-director.md` | No change |
| `proposal-director.md` | Add: if spec has `output_targets`, sum cost across realizers |
| `articulate-director.md` | Add: resolve design-system, persist to library/design-systems/, run validator |
| `storyboard-director.md` | Add: read design-system.brand_authenticity into the storyboard prompt's negative-prompt section |
| `upscale-director.md` | Add: use the upgraded imagegen prompt file format (JSON spec + prose); read design-system.font_resolution_chain (for prompt notes only — images don't have fonts) |
| `compose-director.md` | **Major rewrite**: orchestrate multiple realizers per `output_targets` list |
| `compose-director-deck.md` | NEW: guides agent to invoke Presentations skill with our inputs |
| `publish-director.md` | Add: include all output artifacts (pdf AND deck) in publish_report.json |

## 9. Compatibility & migration

### 9.1 Phased rollout

| Phase | Scope | Risk |
|---|---|---|
| S1 | Schemas + loaders (profile.schema.json, design-system.schema.json, lib/design_system_loader.py, lib/font_resolver.py). No consumer wires yet. | Zero. |
| S2 | Author `consumer-retail.yaml` profile + example `cosmos-luna-may-2026.yaml` design-system. Validator passes. No compose changes yet. | Low. |
| S3 | Articulate stage resolves + persists design-system. Existing PDF compose stays green (just reads the new design-system; behavior unchanged). | Medium — verify v0.3.1 dry-run integration test still passes. |
| S4 | output_selector replaces pdf_selector. Both PDF realizers (Reportlab, WeasyPrint) keep working through new selector. | Medium — pure refactor; covered by existing tests. |
| S5 | PresentationsAdapter + compose-director-deck.md. Smoke test on cosmos-luna-may-2026: produces both PDF and PPTX in one pipeline run. | High — first real cross-realizer integration. |
| S6 | Imagegen prompt format upgrade (JSON spec + prose). Backward compat: existing v0.3.1 prose-only prompts still work for audit, just no JSON spec block. | Low — additive. |
| S7 | Font resolution + brand authenticity gates as compose-time enforcement (not just yaml declarations). | Medium. |
| S8 | Documentation: design-system-reference.md, profiles-reference.md, update v0.3-ARCHITECTURE.md. | Zero. |

### 9.2 Backward compatibility

v0.3.1 specs (no `output_target` field) → default to `a4-magazine` →
same code path → same output. Zero break for existing issues.

v0.3.1 brand yamls (no inheritance into design-system) → design-system
auto-derives from brand.typography + brand.visual_tokens at articulate
time → works.

### 9.3 What's deprecated

- `tools/pdf/pdf_selector.py` → moved to `tools/output/output_selector.py`. Import shim left in place for one minor version.
- Standalone `brand.yaml.typography` resolution at render time → all
  font resolution now goes through `design_system.typography_resolution.fallback_chain`.

## 10. Out of scope / future roadmap

- **6 more profiles** (`finance-ir`, `product-platform`, `gtm-growth`,
  `engineering-platform`, `strategy-leadership`, `appendix-heavy`): v0.3.3+
- **HTML deck output** via op7418/guizang-ppt-skill aesthetic: v0.3.4+
- **Video / animation output**: v0.4+
- **Cross-realizer image reuse**: today PDF and PPTX share the same 4K
  PNGs; future: PPTX might want lower-res or different crops. Add a
  per-realizer image variant system: v0.3.3
- **Reference-beating mode** (give Presentations a target deck to beat):
  defer until we have a use case
- **Comeback rubric** (Presentations's per-slide scoring): translate to
  yaml in v0.3.3
- **`run_prompt_battle.mjs`** (Presentations's prompt A/B): defer
- **CMYK PPTX**: v0.4+

## 11. Open questions / risks

### 11.1 Risks

- **Cross-process artifact paths.** PresentationsAdapter reads back
  artifacts at `outputs/<thread_id>/presentations/<slug>/...`. The
  `<thread_id>` is Codex CLI's session-scoped, not openMagazine's slug.
  We need to either (a) symlink/copy artifacts into `output/<slug>/deck/`,
  or (b) pass our slug to Presentations as `task-slug` parameter so its
  workspace path is predictable. Approach (b) is what SKILL.md
  supports (`$WORKSPACE=$PWD/outputs/$THREAD_ID/presentations/<task-slug>`).
- **Imagegen prompt format drift.** Presentations may change the JSON
  spec keys between versions. Mitigation: schema snapshot in
  `schemas/imagegen_prompt.schema.json`; CI test reads a Presentations
  example artifact and validates.
- **Font resolution platform variance.** `fc-match` on macOS may match
  differently than on Linux CI. Mitigation: vendor a font-resolution
  policy file checked into repo; resolver compares against expected,
  fails loudly on drift.
- **Translation lossiness.** Presentations's `consumer-retail.md` has
  judgment-heavy prose we can't capture in yaml. Mitigation: keep prose
  in `skills/meta/<profile>-author.md` for agent context; yaml carries
  only the *enforceable* rules.
- **PPTX render quality without artifact-tool.** Our Python-side adapter
  can't render slides itself; we depend on Codex's artifact-tool to
  produce the .pptx. If artifact-tool isn't available in the agent's
  Codex CLI, the deck stage fails. Mitigation: check at install /
  preflight; document in CODEX.md.

### 11.2 Open questions

1. Should `design-system.yaml` be auto-generated from
   `(spec, brand, theme, profile)` at articulate time, or hand-authored
   per issue? Tentative answer: auto-generate + persist; user edits
   at the articulate checkpoint.
2. How do realizers signal cost/budget? PresentationsAdapter doesn't
   know imagegen call counts in advance. Tentative: the realizer
   declares a cost-estimate function; OutputSelector aggregates.
3. Should `output_targets` be an ordered list or unordered set? Order
   matters if some realizers depend on others (e.g., the deck reuses
   the PDF's 4K images). Tentative: ordered list, late realizers can
   read earlier realizers' outputs.
4. PPTX 1280×720 vs PDF 4K aspect mismatch. PDF cover is 3:4 portrait,
   PPTX slide is 16:9 landscape. Cropping or different image variants?
   Tentative: PPTX uses crops of the same 4K image (CSS-style), not
   regenerated assets, to share imagegen cost.
5. What happens if PresentationsAdapter expects artifact-tool v2.7.3
   but the user's Codex CLI ships v2.6? Tentative: detect at preflight;
   require upgrade, don't try to work around.

## Appendix A: Worked example — adding `deck-pptx` to `cosmos-luna-may-2026`

### A.1 User edits `library/issue-specs/cosmos-luna-may-2026.yaml`

```diff
 schema_version: 2
 slug: cosmos-luna-may-2026
 subject: luna
 style: national-geographic
 theme: cosmos
 layout: editorial-16page
 brand: meow-life
 article: cosmos-luna-may-2026
+output_targets:
+  - format: a4-magazine
+    realizer: weasyprint
+  - format: deck-pptx
+    realizer: presentations
 overrides: {}
```

### A.2 Stage 1-2 unchanged.

### A.3 Stage 3 articulate (new resolve_design_system step)

```python
design_system = resolve_design_system(
    spec=spec, layers=layers, profile_name=None
)
# → library/design-systems/cosmos-luna-may-2026.yaml written
design_system_validate(design_system_path) → []  # no errors
```

User sees the design-system summary in the articulate checkpoint:

```
Profile: consumer-retail
Typography:
  display: Playfair Display (fallback: Source Serif 4 → Georgia)
  body:    Source Serif 4 (fallback: Georgia)
  meta:    IBM Plex Mono (fallback: Menlo)
Brand authenticity: no logo/mascot/app_icon generation
Output targets: a4-magazine + deck-pptx
```

### A.4 Stage 4 storyboard, Stage 5 upscale unchanged.

### A.5 Stage 6 compose runs both realizers

```
[WeasyprintCompose] cosmos-luna-may-2026 → output/.../magazine.pdf
[PresentationsAdapter] preparing inputs from design_system + regions
                       → agent invokes Presentations with task-slug=cosmos-luna-deck
                       → outputs/<thread>/presentations/cosmos-luna-deck/ produced
                       → adapter copies output/.../deck/cosmos-luna.pptx
```

### A.6 Stage 7 publish_report.json

```json
{
  "spec_slug": "cosmos-luna-may-2026",
  "outputs": {
    "a4-magazine": {
      "path": "output/.../magazine.pdf",
      "size_mb": 42.1,
      "page_count": 16
    },
    "deck-pptx": {
      "path": "output/.../deck/cosmos-luna.pptx",
      "size_mb": 14.0,
      "slide_count": 9
    }
  },
  "total_cost_usd": 5.04,
  "wall_time_min": 16.2
}
```

## Self-Review

- ✅ No "TBD" / "TODO" / "implement later" in normative sections
- ✅ Three constraints from goal answered explicitly in §4.1-§4.6 and
  again in §9.1 phasing
- ✅ Each architectural decision has Decision / Rationale / Alternative /
  Risk
- ✅ Schemas show concrete fields with example values
- ✅ Phased rollout S1-S8 makes each step independently releasable
- ✅ Backward compat for v0.3.1 specs documented (§9.2)
- ✅ Risks acknowledged (§11.1); five open questions surfaced (§11.2)
- ✅ Worked example shows the diff to user input, no jargon
- ✅ Cross-references to v0.3.1 regions spec made explicit (same
  architectural pattern, second application)

## Next Step

1. **Do not implement** until at least the following is confirmed:
   - User reviews spec and approves architecture (especially §4.1
     two-layer split and §4.4 Presentations adapter approach)
   - The v0.3.1 smoke test on a real editorial pipeline has been run
     (still pending; tracked in `docs/SMOKE_TEST_v0.3.md`)
2. After spec approval, file
   `docs/superpowers/plans/2026-05-XX-design-contracts-multi-realizer.md`
   using `superpowers:writing-plans`. Phases match S1-S8 above.
3. Implement via `superpowers:subagent-driven-development` (same
   pattern as v0.3.1's 23-task plan). S1+S2+S6 are independent and good
   candidates for parallel sub-agent dispatch; S3+S4+S5 are sequenced.
4. Live smoke test: produce both PDF and PPTX for
   `cosmos-luna-may-2026` from one pipeline run, verify cost stays
   within $7.50 budget (≤50% increase over single-format $5.04).
