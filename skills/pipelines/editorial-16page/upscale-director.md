# upscale-director — editorial-16page

## Purpose

Stage 5 of editorial-16page. Generate **21 × 4K** Vertex images, one per
`image_slot`, using role-driven prompts (portrait / scene / environment
/ detail / cover_hero / back_coda) and concurrent execution capped at 3
parallel calls. This is the most expensive stage in the pipeline (21 ×
$0.24 = $5.04).

## Inputs

- `output/<slug>/storyboard.json` — plan + cell paths.
- `output/<slug>/cells/spread-NN/<slot>.png` × 21 (storyboard cells).
- `output/<slug>/article.json` (image_slot_overrides per spread for scene text).
- `library/articles/<slug>.yaml` (canonical article copy with overrides).
- `library/layouts/editorial-16page.yaml` (image_slots with `role` + `aspect`).
- `output/<slug>/refs/protagonist-1.jpg` (character anchor).

Validate before proceeding:
- 21 cell PNGs exist, each ≥ 30 KB.
- protagonist-1.jpg long edge ≥ 1024 px.
- Cumulative cost from prior stages leaves headroom for $5.04 spend
  under the $5.50 pipeline budget (`cost-budget-enforcer`).

## Read first (sub-skills)

Layer 2:
- `skills/core/vertex-gemini.md` — wrapper API + auth.
- `skills/creative/photoreal-anti-illustration.md` — negative-prompt
  vocabulary for blocking AI gloss / illustration drift.
- `skills/creative/typography-integrated.md` — but note: typography is
  rendered by WeasyPrint at compose time, NOT inside the photo. The
  `cover_hero` and `back_coda` upscale templates explicitly forbid
  rendering text inside the image.
- `skills/meta/cost-budget-enforcer.md` — per-call cost announcement.

Layer 3:
- `.agents/skills/vertex-gemini-image-prompt-tips.md` — multi-ref
  ordering, aspect rules, Vertex 503 retry semantics.

## Procedure

### 1. Build per-slot jobs (21 of them)

~~~python
import pathlib, yaml
from concurrent.futures import ThreadPoolExecutor

from lib.spec_loader import load_spec, resolve_layers
from lib.prompt_builder_v2 import build_upscale_prompt
from lib.config_loader import get_parallelism
from tools.image.vertex_gemini_image import VertexGeminiImage

spec, _ = load_spec(pathlib.Path("library/issue-specs/<slug>.yaml"))
layers = resolve_layers(spec)
article = yaml.safe_load(
    open(f"library/articles/{spec['article']}.yaml", "r", encoding="utf-8")
)
issue_dir = pathlib.Path(f"output/{spec['slug']}")

def scene_for(short_slot_id, spread_idx):
    for sc in article["spread_copy"]:
        if sc["idx"] == spread_idx:
            return (sc.get("image_slot_overrides") or {}).get(short_slot_id, "")
    return ""

from lib.prompt_persistence import save_prompt
from lib.regions_loader import regions_for_image_prompt, RegionsNotFoundError

# Build spread_idx → spread_type once
spread_type_by_idx = {
    int(sp["idx"]): sp["type"]
    for sp in layers["layout"]["spread_plan"]
}

tool = VertexGeminiImage()
jobs = []
for s in layers["layout"]["image_slots"]:
    short = s["id"]                                           # e.g. "feature_hero"
    full = f"spread-{s['spread_idx']:02d}.{short}"            # e.g. "spread-03.feature_hero"
    scene = scene_for(short, s["spread_idx"])
    spread_type = spread_type_by_idx[s["spread_idx"]]
    try:
        regions_context = regions_for_image_prompt(spread_type, short)
    except (RegionsNotFoundError, ValueError):
        regions_context = None  # legacy CSS spread or slot not in regions yaml
    prompt = build_upscale_prompt(
        role=s["role"], spec=spec, layers=layers,
        slot_id=full, scene=scene, aspect=s["aspect"],
        regions_context=regions_context,
    )
    # Persist the rendered prompt before the paid Vertex call so each
    # spread-NN/<slot>.png has a recoverable .prompt.txt sibling.
    # Build the spec block (v0.3.2)
    imagegen_spec = {
        "intended_output": str(out_path),
        "reference_image": str(refs[0]) if refs else "",
        "size": "3500x4666",  # 4K-ish 3:4 for portrait
        "quality": "high",
        "format": "png",
        "background": "auto",
        "moderation": "auto",
    }
    save_prompt(
        issue_dir, kind="upscale", prompt_text=prompt, slot_id=full,
        spec=imagegen_spec,
    )

    cell = issue_dir / "cells" / f"spread-{s['spread_idx']:02d}" / f"{short}.png"
    refs = [cell]
    # Environment + detail roles don't need the protagonist photo
    # (subject is absent or implied through environmental traces).
    if s["role"] not in ("environment", "detail"):
        refs.append(issue_dir / "refs" / "protagonist-1.jpg")
    out_path = (
        issue_dir / "images" / f"spread-{s['spread_idx']:02d}" / f"{short}.png"
    )
    jobs.append((s, prompt, refs, out_path))
~~~

### 2. Run all 21 calls (parallelism ≤ 3)

~~~python
def _run_one(slot, prompt, refs, out_path):
    return tool.run(
        prompt=prompt,
        refs=refs,
        out_path=out_path,
        aspect=slot["aspect"],
        size="4k",
        skip_existing=True,
    )

max_workers = get_parallelism()  # config-driven, hard cap 3
with ThreadPoolExecutor(max_workers=max_workers) as ex:
    results = list(ex.map(lambda j: _run_one(*j), jobs))
~~~

`skip_existing=True` keeps regeneration cheap — if a single page comes
back broken, delete just that `images/spread-NN/<slot>.png` and rerun;
the other 20 are skipped.

### 3. Cost announcement

Per `skills/meta/cost-budget-enforcer.md`, announce each call:
`"Vertex spread-NN.<slot>: $0.24 (cumulative $X.XX of $5.50)"`. Hard-stop
if cumulative exceeds the proposal's `cost_estimate_usd` × 1.10
(= $5.59 for editorial-16page).

### 4. Write the artifact

`output/<slug>/upscale_result.json` matches
`schemas/artifacts/upscale_result.schema.json`:

~~~json
{
  "images": [
    "output/<slug>/images/spread-01/cover_hero.png",
    "output/<slug>/images/spread-03/feature_hero.png",
    "..."
  ],
  "vertex_calls_made": 21,
  "total_cost_usd": 5.04,
  "spec_slug": "<slug>"
}
~~~

## Checkpoint behavior

`checkpoint: off`. The 21 images flow straight into compose. (User
already gated style at storyboard.)

## Success criteria

- 21 4K PNGs at `images/spread-NN/<slot>.png`, each ≥ 5 MB.
- Each PNG matches its slot's declared `aspect` within 5% (validated
  downstream by `Verify4K`).
- `vertex_calls_made == 21` and `total_cost_usd ≤ 5.59` (10% headroom).

## Failure modes

- **Vertex 503 storms** → reduce parallelism (set
  `OPENMAGAZINE_PARALLELISM=1` and rerun). Don't burn budget on retries
  while the API is degraded.
- **Output PNG < 5 MB** → likely fell back to default-size response;
  delete that single image and rerun (`skip_existing=True` preserves
  the others).
- **Aspect drift** (page is square instead of 3:4) → the slot's
  `aspect` parameter wasn't passed correctly; regenerate just that
  page after fixing.
- **Style drifts to illustration** → research-director Tier 1/2/3
  resolution failed earlier; bounce back, do NOT attempt to fix
  in-stage.
- **Typography appears inside the photo** on cover or back coda →
  upscale_cover_hero / upscale_back_coda templates were under-weighted;
  rerun with stronger emphasis ("NO rendered text"). The PDF compose
  stage is responsible for typography, not the image generator.
