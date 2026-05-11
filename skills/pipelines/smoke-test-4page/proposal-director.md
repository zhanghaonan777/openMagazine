# proposal-director — smoke-test-4page

## Purpose

Stage 2 of smoke-test-4page. Produce a 4-row `page_plan` plus a
cost / wall-time estimate before any paid API call is made. This is the
last opportunity for the user to redirect the run cheaply (everything
after this stage spends real money on Vertex Gemini 3 Pro Image).

## Inputs

- `output/<slug>/research_brief.json` — produced by research-director.
- `library/themes/<theme>.yaml` — theme world + page-plan hints.
- `library/layouts/plain-4.yaml` — the layout this pipeline locks to.

Validate before proceeding:
- research_brief.json validates against schema.
- The theme yaml has a non-empty `page_plan_hints` list of length ≥ 4
  (we'll use the first 4 entries OR the theme's dedicated 4-page hints
  if it ships them).

## Read first (sub-skills)

- `library/themes/<theme>.yaml` — read the theme's lighting principles +
  page_plan_hints.
- `library/layouts/plain-4.yaml` — `page_count: 4`, `aspect: "2:3"`,
  `storyboard_grid: "2x2"`, `top_crop_px_default: 60`.
- `skills/creative/shot-scale-variety.md` — the "no two adjacent pages
  share the same shot scale" rule.
- `skills/meta/overlay-safe-layout.md` — when HTML/PDF overlays are planned,
  define protected subject zones and reserved overlay zones before paid image
  generation.

## Procedure

1. **Load theme + layout.** From the theme yaml, take the first 4
   `page_plan_hints` (or the theme's 4-page dedicated hints, if shipped).
   From the layout yaml, confirm `page_count: 4`.

2. **Build page_plan** — exactly 4 entries: cover (page 1), action
   (page 2), quiet (page 3), back coda (page 4). Each entry is an object
   with:

   ~~~json
   {
     "page": 1,
     "scene_summary": "<theme-grounded one-line scene>",
     "shot_scale": "wide-hero | medium | close-up | overhead-coda",
     "lighting": "<one-line lighting note from theme.lighting_principles>",
     "action": "<one-verb action phrase>"
   }
   ~~~

   Apply shot-scale-variety: page 1 must be hero / dramatic, page 4 must
   be quiet / coda; pages 2 and 3 must each differ in shot scale from
   their neighbours.

   If the issue will use HTML/PDF overlays, also author
   `theme.page_overlay_contracts` (or an issue-local equivalent) before
   storyboard. The contract should name `subject_zone`, `protected_zones`,
   `reserved_overlay_zones`, `html_components`, and `forbidden` overlaps.
   This contract is injected into both storyboard and 4K prompts.

3. **Compute cost_estimate_usd** — fixed math for this pipeline:
   - 1 storyboard call via `image_gen.imagegen` ≈ $0.04
   - 4 upscale calls via Vertex Gemini 3 Pro Image @ $0.24 each = $0.96
   - **Total ≈ $1.00**

4. **Compute wall_time_estimate_min** — fixed math:
   - Storyboard: ~4 min single inference
   - Upscale: 4 calls at parallelism ≤ 3 → ~6 min
   - Compose + verify + contact sheet: ~1 min
   - **Total ≈ 10–12 min** (record `wall_time_estimate_min: 11`).

5. **Write artifact** — `output/<slug>/proposal.json`, matching
   `schemas/artifacts/proposal.schema.json`:

   ~~~json
   {
     "page_plan": [
       {"page": 1, "scene_summary": "...", "shot_scale": "wide-hero", "lighting": "...", "action": "..."},
       {"page": 2, "scene_summary": "...", "shot_scale": "medium",    "lighting": "...", "action": "..."},
       {"page": 3, "scene_summary": "...", "shot_scale": "close-up",  "lighting": "...", "action": "..."},
       {"page": 4, "scene_summary": "...", "shot_scale": "overhead-coda", "lighting": "...", "action": "..."}
     ],
     "cost_estimate_usd": 1.00,
     "wall_time_estimate_min": 11,
     "spec_slug": "<slug>"
   }
   ~~~

## Output artifact

`output/<slug>/proposal.json` — see above.

## Checkpoint behavior

Default `checkpoint: off` in `pipeline_defs/smoke-test-4page.yaml`. Pass
the proposal to storyboard-director without prompting the user. (If the
pipeline def is overridden to checkpoint here, follow
`skills/meta/checkpoint-protocol.md`.)

## Success criteria

- `proposal.json` validates against schema.
- `page_plan.length == 4`.
- All 4 entries have distinct `shot_scale` values from their neighbours.
- If HTML/PDF overlays are planned, every overlay-heavy page has a
  `page_overlay_contracts` entry before paid generation.
- `cost_estimate_usd ≤ 1.10` (cost-budget-enforcer hard ceiling for this
  pipeline).

## Failure modes

- **`theme.page_plan_hints.length < 4`** → caught by spec_validate at
  research-director time; should never reach this director. If it does,
  STOP and report the malformed theme yaml.
- **Cost estimate > $1.10** → STOP; user has likely chosen a wrong
  pipeline. Route them to a different pipeline def.
- **Shot scales adjacent-duplicated** → re-roll page_plan (don't ship a
  proposal that violates shot-scale-variety; the storyboard prompt will
  inherit the violation and produce four flat-scale cells).
