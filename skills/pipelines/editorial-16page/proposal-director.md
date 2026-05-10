# proposal-director — editorial-16page

## Purpose

Stage 2 of editorial-16page. Produce a 9-spread `page_plan` plus a
cost / wall-time estimate before any paid API call. This is the last
opportunity for the user to redirect the run cheaply (everything after
the storyboard checkpoint spends real money on Vertex Gemini 3 Pro Image
× 21 calls).

## Inputs

- `output/<slug>/research_brief.json` — produced by research-director.
- `library/layouts/editorial-16page.yaml` — the layout this pipeline locks to.

Validate before proceeding:
- research_brief.json validates against schema.
- The layout yaml has exactly 9 entries in `spread_plan` and 21
  `image_slots` (after expanding `count: N` entries).

## Read first (sub-skills)

- `library/SCHEMA.md` — 6-layer composition + spread_plan / image_slots
  conventions.
- `skills/meta/cost-budget-enforcer.md` — per-call cost announcement.

## Procedure

1. **Load layout** — read `library/layouts/editorial-16page.yaml`.
   Confirm `spread_plan.length == 9` and that `image_slots` flattens to
   21 entries.

2. **Build page_plan** — one entry per spread (9 total), each:

   ~~~json
   {
     "spread_idx": 1,
     "type": "cover",
     "pages": [1],
     "image_slot_count": 1
   }
   ~~~

3. **Compute cost_estimate_usd** — fixed math for this pipeline:
   - 1 storyboard call via `image_gen.imagegen` ≈ $0.04
   - 21 upscale calls via Vertex Gemini 3 Pro Image @ $0.24 each = $5.04
   - **Total ≈ $5.08**

4. **Compute wall_time_estimate_min**:
   - Storyboard: ~4 min single inference
   - Upscale: 21 calls at parallelism ≤ 3 → ~7 batches × ~1.5 min = ~10 min
   - Compose + verify + contact sheet: ~1 min
   - **Total ≈ 15 min** (record `wall_time_estimate_min: 15`).

5. **Write artifact** — `output/<slug>/proposal.json` matching
   `schemas/artifacts/proposal.schema.json`:

   ~~~json
   {
     "page_plan": [{"spread_idx": 1, "type": "cover", "pages": [1], "image_slot_count": 1}, ...],
     "cost_estimate_usd": 5.08,
     "wall_time_estimate_min": 15,
     "spec_slug": "<slug>"
   }
   ~~~

## Output artifact

`output/<slug>/proposal.json` — see schema reference above.

## Checkpoint behavior

`checkpoint: off`. Pass the proposal to articulate-director without
prompting the user.

## Success criteria

- `proposal.json` validates against schema.
- `page_plan.length == 9`.
- Sum of `image_slot_count` across the 9 entries == 21.
- `cost_estimate_usd ≤ 5.50` (pipeline budget_default_usd).

## Failure modes

- **`spread_plan.length != 9`** → layout yaml is malformed; STOP.
- **`image_slots` flattens to ≠ 21** → layout yaml is malformed; STOP.
- **Cost estimate > $5.50** → user has likely chosen a wrong pipeline or
  the layout has more slots than declared. STOP.
