# research-director — editorial-16page

## Purpose

Stage 1 of the editorial-16page pipeline. Convert user input (free-form
photo + one-liner) or a v2 spec yaml into a `research_brief.json` artifact
identifying all 6 layer references: subject / style / theme / layout /
brand / article. This stage is read-only with respect to paid APIs — it
interviews the user, analyzes the protagonist photo, and resolves the
style anchor through the styles library.

## Inputs

Two mutually exclusive input modes:

- **Free-form**: a natural-language user message ("做一本太空号 of my cat")
  + a protagonist photo at `output/<slug>/refs/protagonist-1.jpg`. Layout
  defaults to `editorial-16page`; brand defaults to `meow-life`; article
  reference is deferred to the articulate stage.
- **Spec**: a path to `library/issue-specs/<slug>.yaml` produced by an
  earlier run. Schema v2 is required for this pipeline. The spec may
  reference an existing `library/articles/<slug>.yaml` or omit `article`
  (in which case articulate will draft it).

Validate before proceeding:
- The protagonist photo path resolves to a readable JPEG/PNG with a
  recognizable header and long edge ≥ 1024 px (per
  `tools/validation/reference_photo_check.py`).
- The user has named (or implied) a magazine theme that maps to a
  `library/themes/*.yaml`; if not, ask once.

## Read first (sub-skills)

- `skills/meta/creative-intake.md` — interview protocol for traits / style
  / theme / page count.
- `skills/meta/reference-photo-analyst.md` — how to derive
  `library/subjects/<name>.yaml` from a photo.
- `skills/creative/style-anchor-resolution.md` — Tier 1 / Tier 2 / Tier 3
  style normalization.

## Procedure

1. **Spec mode** — if input is a yaml path, load it and validate via
   `python tools/validation/spec_validate.py library/issue-specs/<slug>.yaml`.
   Verify `schema_version: 2`. On success, skip steps 2–4 and synthesize
   `research_brief.json` directly from the spec fields. Skip to step 5.

2. **Free-form intake** — run the creative-intake protocol to extract:
   - `traits` (5–8 verbatim trait phrases, copy-paste exactly)
   - `style` (raw user phrase; will be normalized in step 4)
   - `theme` (must map to a `library/themes/<theme>.yaml`)
   - `page_count` (must be 16 for this pipeline)
   - `magazine_name` (defaults to brand masthead if user didn't name one)

3. **Subject resolution** — if the named subject does NOT have a
   `library/subjects/<slug>.yaml`, run reference-photo-analyst against the
   protagonist photo to author one. Land it before proceeding so subjects
   become reusable.

4. **Style resolution** — apply the 3-tier flow from
   `skills/creative/style-anchor-resolution.md`. Tier 1 hit → use the
   matched yaml's `style_anchor` verbatim. Otherwise scaffold (Tier 2) or
   inline rewrite (Tier 3).

5. **Write artifact** — `output/<slug>/research_brief.json` matching
   `schemas/artifacts/research_brief.schema.json`:

   ~~~json
   {
     "traits": "<verbatim user trait string>",
     "style_anchor": "<resolved style anchor>",
     "theme_world": "<from theme yaml>",
     "magazine_name": "<from brand.masthead>",
     "page_count": 16,
     "spec_slug": "<slug>"
   }
   ~~~

## Output artifact

`output/<slug>/research_brief.json` — see schema reference above.

## Checkpoint behavior

`checkpoint: off` (per `pipeline_defs/editorial-16page.yaml`). Proceed to
proposal-director without user approval.

## Success criteria

- `research_brief.json` exists, parses, and validates against schema.
- spec_validate returns 0 OR the spec lacks `article` (deferred to
  articulate stage).
- `traits` is non-empty and copied verbatim from user input.
- `style_anchor` is the resolved string from Tier 1/2/3 (NOT raw painter
  / movement words).
- `page_count == 16`.

## Failure modes

- **Photo missing or unreadable** → STOP. Ask the user for a usable
  protagonist photo. Do NOT fabricate traits.
- **Theme has no library yaml** → STOP and offer to scaffold one.
- **`page_count != 16`** → wrong pipeline; route the user to
  `smoke-test-4page` (4 pages) or future `editorial-32page`.
- **Tier 1 hit but `style_anchor` field missing in yaml** → STOP and fix
  the library file before continuing.
