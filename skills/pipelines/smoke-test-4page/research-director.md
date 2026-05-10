# research-director — smoke-test-4page

## Purpose

Stage 1 of the smoke-test-4page pipeline. Turn the user's free-form input
(or a pre-existing spec yaml) into a schema-valid `research_brief.json`
artifact. This stage is read-only with respect to paid APIs — it does
nothing but interview the user, analyze the protagonist photo, and
resolve the style anchor through the styles library.

## Inputs

Two mutually exclusive input modes:

- **Free-form**: a natural-language user message ("做一本太空号 of my cat")
  + a protagonist photo at `output/<slug>/refs/protagonist-1.jpg`.
- **Spec**: a path to `library/issue-specs/<slug>.yaml` produced by an
  earlier run.

Validate before proceeding:
- The protagonist photo path resolves to a readable file ≥ 200 KB and a
  recognizable JPEG/PNG header.
- The user has named (or implied) a magazine theme that maps to a
  `library/themes/*.yaml`; if not, ask once.

## Read first (sub-skills)

Layer 2 — project conventions:
- `skills/meta/creative-intake.md` — interview protocol for traits / style
  / theme / page count.
- `skills/meta/reference-photo-analyst.md` — how to derive
  `library/subjects/<name>.yaml` from a photo.
- `skills/creative/style-anchor-resolution.md` — Tier 1 / Tier 2 / Tier 3
  style normalization.

## Procedure

1. **Spec mode** — if input is a yaml path, load it and validate via
   `from tools.validation.spec_validate import spec_validate`. On success,
   skip steps 2–4 and synthesize `research_brief.json` directly from the
   spec fields. Skip to step 5.

2. **Free-form intake** — run the creative-intake protocol to extract:
   - `traits` (5–8 verbatim trait phrases, copy-paste exactly)
   - `style` (raw user phrase; will be normalized in step 4)
   - `theme` (must map to a `library/themes/<theme>.yaml`)
   - `page_count` (must be 4 for this pipeline)
   - `magazine_name`, `cover_line` (optional but recorded if given)

3. **Subject resolution** — if the named subject does NOT have a
   `library/subjects/<slug>.yaml`, run reference-photo-analyst against the
   protagonist photo to author one. Land it before proceeding so subjects
   become reusable.

4. **Style resolution** — apply 3-tier:
   - Tier 1: substring-match user's style against
     `library/brands/*.yaml` and `styles/*.yaml` `trigger_keywords`. On
     hit, use the file's `style_anchor` verbatim. DONE.
   - Tier 2: scaffold a new style yaml via `skills/meta/scaffold-style.md`,
     then re-enter Tier 1.
   - Tier 3: inline rewrite per Class A/B/C rules in
     `style-anchor-resolution.md`. Result NOT persisted.

5. **Write artifact** — `output/<slug>/research_brief.json`, matching
   `schemas/artifacts/research_brief.schema.json`:

   ~~~json
   {
     "traits": "<verbatim user trait string>",
     "style_anchor": "<resolved style anchor>",
     "theme_world": "<from theme yaml or user>",
     "magazine_name": "<masthead text>",
     "cover_line": "<optional cover headline>",
     "page_count": 4,
     "spec_slug": "<slug>"
   }
   ~~~

## Output artifact

`output/<slug>/research_brief.json` — see schema reference above.

## Checkpoint behavior

Per `pipeline_defs/smoke-test-4page.yaml`, the research stage has
`checkpoint: off` by default. Proceed to proposal-director without user
approval. The user will see the research_brief content reflected in the
proposal stage's page_plan (which IS checkpointed if the pipeline def
flips it on).

## Success criteria

- `research_brief.json` exists, parses, and validates against schema.
- `traits` is non-empty and copied verbatim from user input (no rephrasing).
- `style_anchor` is the resolved string from Tier 1/2/3 (NOT the raw user
  phrase if a painter / movement / mood keyword was present).
- `theme_world` matches the chosen `library/themes/<theme>.yaml` exactly
  if Tier 1 hit.
- `page_count == 4`.

## Failure modes

- **Photo missing or unreadable** → STOP. Ask the user for a usable
  protagonist photo. Do NOT fabricate traits without the photo.
- **Theme has no library yaml** → STOP and offer to scaffold one
  (route to scaffold-style if it's a style; otherwise route to a manual
  theme-author flow).
- **page_count ≠ 4** → STOP. The smoke-test-4page pipeline is
  hard-locked at 4 pages; route the user to a different pipeline if they
  asked for 16.
- **Tier 1 hit but `style_anchor` field missing in yaml** → STOP and fix
  the library file before continuing.
