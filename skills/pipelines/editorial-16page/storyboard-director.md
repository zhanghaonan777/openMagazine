# storyboard-director — editorial-16page

## Purpose

Stage 4 of editorial-16page and the heart of the pipeline. ONE codex
`image_gen.imagegen` inference produces a 2:3 portrait multi-aspect grid
containing all **21 image slots**, locked in style / character /
lighting. The storyboard locks consistency across all 21 downstream 4K
upscales — if the storyboard is off-style, regenerate the whole grid (do
not salvage individual cells).

## Inputs

- `output/<slug>/research_brief.json`, `output/<slug>/proposal.json`,
  `output/<slug>/article.json` (with `image_slot_overrides` per spread).
- `library/articles/<slug>.yaml`
- `library/layouts/editorial-16page.yaml` (resolved via `resolve_layers`).
- `output/<slug>/refs/protagonist-1.jpg` (already on disk from intake).

Validate before proceeding:
- All upstream artifacts validate against schemas.
- `article_validate` on the article yaml returns 0.
- The Codex CLI runtime is active (`echo $CODEX_HOME` resolves) — see CODEX.md.

## Read first (sub-skills)

Layer 2:
- `skills/core/codex-image-gen.md` — wrapper + capture protocol.
- `skills/creative/prompt-style-guide.md` — verbatim trait/style rules.
- `skills/creative/shot-scale-variety.md` — ensure 21 cells aren't all
  the same scale.

Layer 3:
- `.agents/skills/codex-image-gen-plumbing.md` — full BEFORE/AFTER
  capture contract.
- `CODEX.md` — runtime adapter (Codex CLI is the ONLY backend with
  native `image_gen.imagegen`).

## Procedure

### 1. Build the storyboard prompt via the planner + v2 builder

~~~python
import pathlib, yaml
from lib.spec_loader import load_spec, resolve_layers
from lib.storyboard_planner import plan_storyboard
from lib.prompt_builder_v2 import build_storyboard_prompt_v2

spec, _ = load_spec(pathlib.Path("library/issue-specs/<slug>.yaml"))
layers = resolve_layers(spec)
article = yaml.safe_load(
    open(f"library/articles/{spec['article']}.yaml", "r", encoding="utf-8")
)

# Flatten image_slots: each entry gets its full spread-NN.<slot> id.
slots = []
for s in layers["layout"]["image_slots"]:
    slots.append({
        **s,
        "id": f"spread-{s['spread_idx']:02d}.{s['id']}",
    })

plan = plan_storyboard(slots)  # → {grid: {rows: 6, cols: 4}, cells: [...]}

# Map article's per-spread image_slot_overrides into a flat slot_id → scene dict.
scenes_by_slot = {}
for sc in article["spread_copy"]:
    for slot, scene in (sc.get("image_slot_overrides") or {}).items():
        scenes_by_slot[f"spread-{sc['idx']:02d}.{slot}"] = scene

# Load per-spread regions yamls (gracefully skip spreads without yamls
# during migration). Build the spread_type → regions map and the
# spread_idx → spread_type map for the prompt builder.
from lib.regions_loader import load_regions, RegionsNotFoundError

regions_by_spread_type: dict[str, list[dict]] = {}
spread_type_by_idx: dict[int, str] = {}
for sp in layers["layout"]["spread_plan"]:
    spread_type_by_idx[int(sp["idx"])] = sp["type"]
    if sp["type"] in regions_by_spread_type:
        continue
    try:
        regions_doc = load_regions(sp["type"])
        regions_by_spread_type[sp["type"]] = regions_doc["regions"]
    except RegionsNotFoundError:
        pass  # legacy CSS spread; no regions block

prompt = build_storyboard_prompt_v2(
    spec, layers,
    plan=plan,
    scenes_by_slot=scenes_by_slot,
    regions_by_spread_type=regions_by_spread_type,
    spread_type_by_idx=spread_type_by_idx,
)

# Persist the rendered prompt + a run manifest BEFORE the codex call so
# the exact text + template version that produced storyboard.png are
# recoverable from disk later.
from lib.prompt_persistence import save_prompt, save_manifest
issue_dir = pathlib.Path(f"output/{spec['slug']}")
imagegen_spec = {
    "intended_output": str(issue_dir / "storyboard.png"),
    "reference_image": "",
    "size": "1024x1536",
    "quality": "medium",
    "format": "png",
    "background": "auto",
    "moderation": "auto",
}
save_prompt(issue_dir, kind="storyboard", prompt_text=prompt, spec=imagegen_spec)
save_manifest(
    issue_dir,
    spec_slug=spec["slug"],
    pipeline="editorial-16page",
    templates_used={
        "storyboard": "library/templates/storyboard_v2.prompt.md",
        "upscale_portrait": "library/templates/upscale_portrait.prompt.md",
        "upscale_scene": "library/templates/upscale_scene.prompt.md",
        "upscale_environment": "library/templates/upscale_environment.prompt.md",
        "upscale_detail": "library/templates/upscale_detail.prompt.md",
        "upscale_cover_hero": "library/templates/upscale_cover_hero.prompt.md",
        "upscale_back_coda": "library/templates/upscale_back_coda.prompt.md",
    },
)
~~~

Verify the rendered prompt has no unfilled `{{...}}` tokens before the
codex call.

### 2. BEFORE capture

~~~bash
BEFORE=$(ls -t ~/.codex/generated_images/*/ig_*.png 2>/dev/null | head -1)
echo "${BEFORE:-NONE}" > /tmp/imagegen_before.txt
~~~

### 3. Call `image_gen.imagegen` with the rendered prompt

This is a **Codex-level tool call**, not a shell command. Pass the
prompt; ask for 2:3 portrait at 1024×1536. The tool returns a synthetic
response object — don't try to extract the file from it.

### 4. AFTER capture — copy new PNG into the issue dir

~~~bash
sleep 1
AFTER=$(ls -t ~/.codex/generated_images/*/ig_*.png 2>/dev/null | head -1)
if [ -z "$AFTER" ] || [ "$AFTER" = "$(cat /tmp/imagegen_before.txt)" ]; then
  echo "ERROR: no new file. STOP."
  exit 1
fi
cp "$AFTER" output/<slug>/storyboard.png
~~~

### 5. Split the storyboard into per-slot cells

~~~python
from tools.image.pillow_split import split_by_plan

split_by_plan(
    pathlib.Path(f"output/{spec['slug']}/storyboard.png"),
    pathlib.Path(f"output/{spec['slug']}/cells"),
    plan=plan,
)
~~~

This writes 21 PNGs at `output/<slug>/cells/spread-NN/<slot>.png`. The
function emits a stderr warning if the storyboard outer aspect deviates
from 2:3 — treat that as a regeneration trigger (see Failure modes).

### 6. Write the artifact

`output/<slug>/storyboard.json` matches
`schemas/artifacts/storyboard.schema.json`:

~~~json
{
  "png_path": "output/<slug>/storyboard.png",
  "cells_dir": "output/<slug>/cells/",
  "plan": { "grid": {"rows": 6, "cols": 4}, "cells": [...] },
  "slot_count": 21,
  "spec_slug": "<slug>"
}
~~~

## ABSOLUTE STOP RULE

If `image_gen.imagegen` produces no new file (`AFTER == BEFORE`), STOP
IMMEDIATELY. Report to the user and ask for guidance.

DO NOT fall back to PIL / Pillow / `ImageDraw` / any drawing-primitive
library to mock up a storyboard. PIL mockup cells produce flat-shot-scale
4K output downstream (validated failure mode: naigai-fauvist 4-page test,
2026-05-10). A real failed run is recoverable; a faked storyboard wastes
~$5 of Vertex spend on garbage 4K pages.

## Checkpoint behavior

The storyboard stage is **`checkpoint: required`** (per
`pipeline_defs/editorial-16page.yaml`). Before proceeding to upscale,
follow `skills/meta/checkpoint-protocol.md`:

1. Show the user `output/<slug>/storyboard.png` and a summary of the 21
   cell PNG paths.
2. Highlight observable risks: style drift, identical shot scales,
   baked caption boxes, garbled page numbers, cells with the wrong
   aspect for their declared role.
3. Ask: approve / regenerate / abort.
4. On regenerate: re-run from step 1 (rebuild the prompt; never tweak
   cells individually).
5. On abort: STOP without spending any Vertex budget.

## Success criteria

- `output/<slug>/storyboard.png` is 1024×1536 (2:3 portrait), ≥ 200 KB.
- 21 cell PNGs at `output/<slug>/cells/spread-NN/<slot>.png`, each ≥ 30 KB.
- `pillow_split.split_by_plan` did NOT print the "deviates from 2:3"
  aspect warning.
- `storyboard.json` validates against schema.
- User explicit OK recorded in checkpoint sidecar.

## Failure modes

- **No new file produced** (`AFTER == BEFORE`) → STOP per the absolute rule.
- **Storyboard not 2:3** (square / 4:3 / etc.) → STOP. Model failed
  the OUTPUT IMAGE FORMAT constraint. Regenerate.
- **Cell PNGs ≪ 256 px short edge** → storyboard outer was generated at
  small size; regenerate at full 1024×1536.
- **All 21 cells share the same shot scale / pose** → article's
  `image_slot_overrides` were too uniform; bounce back to articulate
  with a note to vary scenes.
- **Page-number markers leaking into cell content** — by default the
  v2 split does not crop tops (the storyboard prompt asks for labels
  in the *gutter*, not inside the cell). If labels still leak, raise
  the storyboard outer size or inspect the model's compliance with the
  prompt's "page numbers labeled top-left of each cell" constraint.
- **Style drifts to illustration** → research-director Tier 1/2/3
  resolution failed earlier; bounce back. Don't try to fix in upscale.
