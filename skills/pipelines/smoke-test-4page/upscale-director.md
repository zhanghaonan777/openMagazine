# upscale-director — smoke-test-4page

## Purpose

Stage 4 of smoke-test-4page. Produce 4 4K-resolution page PNGs by feeding
each storyboard cell — plus the protagonist photo as a character anchor —
into Vertex Gemini 3 Pro Image. Three distinct prompt templates are used:
one for the cover (page 01), one for the two inner pages (02-03), and one
for the back cover (page 04). Typography for cover and back is rendered
INTO the photograph (painted on walls / printed on banners in-scene), never
as a footer bar or barcode strip overlay. This is the most expensive stage
in the pipeline (4 × $0.24 = $0.96).

## Inputs

- `output/<slug>/storyboard.json` (cells_dir + page_plan).
- `output/<slug>/research_brief.json` (traits, style_anchor, theme_world,
  magazine_name, cover_line).
- `output/<slug>/cells/cell-0{1..4}.png` (storyboard cells on disk).
- `output/<slug>/refs/protagonist-1.jpg` (character anchor).

Validate before proceeding:
- 4 cell PNGs exist, each ≥ 30 KB.
- protagonist-1.jpg exists with long edge ≥ 1024 px (per
  `tools/validation/reference_photo_check.py`); byte-size is not a criterion.
- `cost-budget-enforcer` (`skills/meta/cost-budget-enforcer.md`) sees
  $0.96 of remaining budget for this issue.

## Read first (sub-skills)

Layer 2:
- `skills/core/vertex-gemini.md` — wrapper API + auth.
- `skills/creative/typography-integrated.md` — masthead-painted-into-scene
  rule (cover and back cover only).
- `skills/creative/photoreal-anti-illustration.md` — negative-prompt
  vocabulary for blocking AI gloss / illustration drift.
- `skills/meta/cost-budget-enforcer.md` — per-call cost announcement.

Layer 3:
- `.agents/skills/vertex-gemini-image-prompt-tips.md` — multi-ref ordering,
  aspect rules, Vertex 503 retry semantics.

## Procedure

### 1. Build per-page prompts

All 4K prompts are rendered from layout-driven templates. The 4 pages map to
3 templates:

| Page index | Template | Builder function |
|---|---|---|
| 01 | `library/templates/upscale_cover.prompt.md` | `build_cover_prompt(spec, layers)` |
| 02 — N-1 | `library/templates/upscale_inner.prompt.md` | `build_inner_prompt(spec, layers, scene=...)` |
| N (last) | `library/templates/upscale_back.prompt.md` | `build_back_prompt(spec, layers, scene=...)` |

Where N is the layout's `page_count`. For the 4-page smoke test, N=4 → page
01 is cover, pages 02-03 are inner, page 04 is back. For a 9-page variant,
pages 02-08 would all use the inner template.

References per call (order matters — first ref dominates composition):

| Page | Refs (in order) | Output path |
|---|---|---|
| 01 cover | `cells/cell-01.png`, `refs/protagonist-1.jpg` | `images/page-01.png` |
| 02 inner | `cells/cell-02.png`, `refs/protagonist-1.jpg` | `images/page-02.png` |
| 03 inner | `cells/cell-03.png`, `refs/protagonist-1.jpg` | `images/page-03.png` |
| 04 back | `cells/cell-04.png`, `refs/protagonist-1.jpg` | `images/page-04.png` |

Per-page scene comes from `layers['theme'].page_plan_hints[i-1]` with the
leading `NN: ` prefix stripped. Use `page_plan_scene_for(layers, i)` to get
it.

~~~python
from lib.spec_loader import load_spec, resolve_layers
from lib.prompt_builder import (
    build_cover_prompt,
    build_inner_prompt,
    build_back_prompt,
    page_plan_scene_for,
)
import pathlib

spec, _ = load_spec(pathlib.Path("library/issue-specs/<slug>.yaml"))
layers = resolve_layers(spec)
page_count = int(layers["layout"]["page_count"])

prompts = {}
for i in range(1, page_count + 1):
    if i == 1:
        prompts[i] = build_cover_prompt(spec, layers)
    elif i == page_count:
        prompts[i] = build_back_prompt(spec, layers, scene=page_plan_scene_for(layers, i))
    else:
        prompts[i] = build_inner_prompt(spec, layers, scene=page_plan_scene_for(layers, i))
~~~

Verify each prompt has all placeholders filled (no `{{...}}` tokens remain)
before the Vertex calls.

### 2. Run all 4 calls (concurrently)

The 4 Vertex calls are independent — drive them through a thread pool. Concurrency
is read from config (`config.yaml` → `defaults.parallelism`, default 3) and can be
overridden via the `OPENMAGAZINE_PARALLELISM` env var. The hard cap is 3 — Vertex
Gemini 3 Pro Image emits 503 storms above that.

~~~python
from concurrent.futures import ThreadPoolExecutor
from tools.image.vertex_gemini_image import VertexGeminiImage
from lib.config_loader import get_parallelism
import pathlib

tool = VertexGeminiImage()
issue_dir = pathlib.Path("output/<slug>")

jobs = [(i, prompts[i]) for i in range(1, page_count + 1)]

def _run_one(page_idx, prompt):
    return tool.run(
        prompt=prompt,
        refs=[
            issue_dir / f"cells/cell-{page_idx:02d}.png",
            issue_dir / "refs/protagonist-1.jpg",
        ],
        out_path=issue_dir / f"images/page-{page_idx:02d}.png",
        aspect="2:3",
        size="4k",
        skip_existing=True,
    )

max_workers = get_parallelism()  # config-driven, hard cap 3
with ThreadPoolExecutor(max_workers=max_workers) as ex:
    results = list(ex.map(lambda j: _run_one(*j), jobs))
~~~

Wall time: with 4 jobs at parallelism 3, expect 2 batches (3+1) ≈ 1.5× one
single call's latency, vs 4× for serial. Typical: ~60-90 s per 4K call → ~2-3
minutes total parallel vs ~4-6 minutes serial.

`skip_existing=True` keeps regeneration cheap — if a single page comes back
broken, delete just `images/page-NN.png` and re-run; the other 3 are skipped.

### 3. Cost announcement

Per `skills/meta/cost-budget-enforcer.md`, announce each call before issuing
it: `"Vertex page-NN: $0.24 (cumulative $X.XX of $0.96)"`. Hard-stop if
cumulative exceeds the proposal's `cost_estimate_usd` by more than 10%.

### 4. Write the artifact

Schema: `schemas/artifacts/upscale_result.schema.json`. Path:
`output/<slug>/upscale_result.json`.

~~~json
{
  "images": [
    "output/<slug>/images/page-01.png",
    "output/<slug>/images/page-02.png",
    "output/<slug>/images/page-03.png",
    "output/<slug>/images/page-04.png"
  ],
  "vertex_calls_made": 4,
  "total_cost_usd": 0.96,
  "spec_slug": "<slug>"
}
~~~

## Output artifact

`output/<slug>/upscale_result.json` (above) plus 4 PNGs at
`output/<slug>/images/page-0{1..4}.png`.

## Checkpoint behavior

Default `checkpoint: off` in `pipeline_defs/smoke-test-4page.yaml`. The 4
pages flow straight into compose-director. (User would have caught style
drift at the storyboard checkpoint already.)

## Success criteria

- 4 PNGs at `images/page-0{1..4}.png`, each 5–30 MB.
- Each is 2:3 portrait at ≥ 2048 × 3072 (validated downstream by `Verify4K`).
- `upscale_result.json` validates against schema; `vertex_calls_made == 4` and
  `total_cost_usd <= 1.05` (10% headroom over $0.96).

## Failure modes

- **Vertex 503 storms** → reduce parallelism (3 → 1) and rerun. Don't burn
  budget on retries when the API is down.
- **Output PNG < 5 MB** → likely fell back to a default-size response;
  delete that single page and rerun (`skip_existing=True` will preserve
  the other 3).
- **Page-number marker leaks through** (cell page-number visible in 4K) →
  expand the negative prompt with the verbatim leaked text (e.g. "the digit
  04 in the upper-left corner") and rerun that page.
- **Typography drifts to footer-bar / barcode strip** on cover or back →
  the integrated-typography rule was under-weighted; rerun with stronger
  emphasis ("masthead PAINTED ON the wall, not overlaid on the photo").
- **Style drifts to illustration** → research-director Tier 1/2/3
  resolution failed earlier; bounce back to research-director, do NOT
  attempt to fix in-stage.
