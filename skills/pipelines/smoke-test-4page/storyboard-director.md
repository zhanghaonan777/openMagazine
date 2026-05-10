# storyboard-director — smoke-test-4page

## Purpose

Stage 3 of smoke-test-4page and the heart of the pipeline. ONE inference of a
2×2 storyboard grid (4 cells, one per planned page) emitted by Codex's native
`image_gen.imagegen` tool. The storyboard locks character identity, color
palette, lighting language, and overall composition vocabulary across all 4
downstream 4K upscales. Every later stage inherits the consistency that lands
here — if the storyboard is off-style, regenerate the whole grid (do not
salvage individual cells).

## Inputs

- `output/<slug>/research_brief.json` (from research-director).
- `output/<slug>/proposal.json` (from proposal-director, with the 4-row
  page_plan).
- `output/<slug>/refs/protagonist-1.jpg` (already on disk from intake).

Validate before proceeding:
- Both JSON artifacts validate against their schemas.
- `proposal.page_plan.length == 4`.
- The Codex CLI runtime is active (`echo $CODEX_HOME` resolves) — see CODEX.md.

## Read first (sub-skills)

Layer 2 — project conventions:
- `skills/core/codex-image-gen.md` — wrapper + capture protocol.
- `skills/creative/prompt-style-guide.md` — verbatim trait/style rules.
- `skills/creative/shot-scale-variety.md` — adjacency rule for the 4 cells.

Layer 3 — technology details:
- `.agents/skills/codex-image-gen-plumbing.md` — full BEFORE/AFTER capture
  contract.
- `CODEX.md` — runtime adapter (Codex CLI is the ONLY backend with native
  `image_gen.imagegen`).

## Procedure

### 1. Construct the storyboard prompt

Adapted from the predecessor's Phase 1 template, **2×2 (4 cells) variant**.
Substitute `{{TRAITS}}`, `{{STYLE_ANCHOR}}`, `{{THEME_WORLD}}`, and the
per-cell `{{SCENE_NN}}` / `{{ACTION_VERB_NN}}` from `research_brief.json` and
`proposal.page_plan[*]` verbatim — **never paraphrase** between stages.

~~~text
Generate a single image: a 2×2 grid storyboard for a 4-page photo magazine.

Layout: 2 columns × 2 rows. Thin white gutters between cells. Each cell is
a vertical 2:3 frame. Top-left of each cell shows a small page number 01-04.

Subject in EVERY cell (locked, identical across all 4):
{{TRAITS}}

Theme world: {{THEME_WORLD}}

Style locked across all cells: {{STYLE_ANCHOR}}

Page plan (each scene must be visually distinct; mix wide / medium / close-up
/ overhead; no two adjacent pages should share the same shot scale):

01 — Cover: hero composition appropriate to {{THEME_WORLD}}, dramatic
            framing, character occupies upper two-thirds. Low-angle or
            strong asymmetric composition. NEVER a flat centered subject.
02 — Action: {{ACTION_VERB_02}} — {{SCENE_02}}.
03 — Quiet beat: {{SCENE_03}}, contrasting shot scale from page 02.
04 — Back cover: a quiet coda. Single small element, mostly negative space,
            distant silhouette OR overhead OR large empty frame. NEVER
            mirror the cover composition.

Constraints:
- SAME character across all cells (face / markings / build / baseline
  expression all identical).
- SAME color palette across all cells.
- SAME lighting language across all cells.
- Each cell is low-detail but composition and mood must read clearly.
- No text inside cells except the page number.
- No watermarks, no logos, no caption boxes.
~~~

Embed shot scale + camera angle + subject screen-fraction directly into each
`{{SCENE_NN}}` string. Don't leave them implicit. Example:

~~~text
✗  "03 — kitchen scene"
✓  "03 — kitchen, low-angle close-up from floor level looking up at subject
        on counter, subject fills upper-third of frame, shallow DOF"
~~~

### 2. BEFORE capture (record latest existing PNG)

The `image_gen.imagegen` tool response does NOT expose bytes / url / path.
The Codex CLI persists every generated PNG to
`~/.codex/generated_images/<session-uuid>/ig_<hash>.png`. We diff
BEFORE/AFTER to detect the new file.

~~~bash
BEFORE=$(ls -t ~/.codex/generated_images/*/ig_*.png 2>/dev/null | head -1)
echo "BEFORE=$BEFORE"
~~~

Equivalently, the wrapper exposes this via Python:

~~~python
from tools.image.codex_image_gen import CodexImageGen
tool = CodexImageGen()
state = tool.run(mode="storyboard")   # {"before_path": ..., "ts": ...}
~~~

### 3. Call image_gen.imagegen with the constructed prompt

This is a **Codex-level tool call**, not a shell command. The agent invokes
`image_gen.imagegen` with the prompt text built in step 1, asking for 2:3
portrait aspect at 1024+ px short edge (1536+ ideal).

The tool returns a synthetic response object (no path). Don't try to extract
the file from the response.

### 4. AFTER capture (copy new PNG into the issue dir)

~~~bash
sleep 1
AFTER=$(ls -t ~/.codex/generated_images/*/ig_*.png 2>/dev/null | head -1)
test "$AFTER" != "$BEFORE" && cp "$AFTER" output/<slug>/storyboard.png
~~~

Or via the wrapper:

~~~python
import pathlib
tool.capture_new_png(
    state,
    out_path=pathlib.Path("output/<slug>/storyboard.png"),
    timeout_seconds=5,
)
~~~

### 5. Split the storyboard into 4 cells

~~~bash
python -c "from tools.image.pillow_split import split_storyboard; \
  split_storyboard('output/<slug>/storyboard.png', \
                   'output/<slug>/cells/', \
                   rows=2, cols=2, top_crop_px=60)"
~~~

This writes `output/<slug>/cells/cell-01.png` ... `cell-04.png`. The
`top_crop_px=60` value comes from `library/layouts/plain-4.yaml`'s
`top_crop_px_default` and removes the row of page-number markers Codex tends
to bake along the top edge of each cell.

### 6. Write the artifact

Schema: `schemas/artifacts/storyboard.schema.json`. Path:
`output/<slug>/storyboard.json`.

~~~json
{
  "png_path": "output/<slug>/storyboard.png",
  "cells_dir": "output/<slug>/cells/",
  "rows": 2,
  "cols": 2,
  "cell_count": 4,
  "top_crop_px_used": 60,
  "page_plan": [
    {"page": 1, "scene_summary": "...", "shot_scale": "wide-hero"},
    {"page": 2, "scene_summary": "...", "shot_scale": "medium"},
    {"page": 3, "scene_summary": "...", "shot_scale": "close-up"},
    {"page": 4, "scene_summary": "...", "shot_scale": "overhead-coda"}
  ],
  "spec_slug": "<slug>"
}
~~~

## ABSOLUTE STOP RULE

If `image_gen.imagegen` produces no new file (i.e. `AFTER == BEFORE` or
`capture_new_png` raises), STOP IMMEDIATELY. Report to the user and ask for
guidance.

DO NOT fall back to PIL / Pillow / `ImageDraw` / any drawing-primitive library
to mock up a storyboard. PIL mockup cells produce flat-shot-scale 4K output
downstream (validated failure mode: naigai-fauvist 4-page test, 2026-05-10).
A real failed run is recoverable; a faked storyboard wastes ~$1.00 of Vertex
spend on garbage 4K pages.

This rule is also stated in `skills/core/codex-image-gen.md` and `CODEX.md`.

## Output artifact

`output/<slug>/storyboard.json` per the schema above, plus
`output/<slug>/storyboard.png` and `output/<slug>/cells/cell-0{1..4}.png`.

## Checkpoint behavior

The storyboard stage is the **default checkpoint** for smoke-test-4page (per
`pipeline_defs/smoke-test-4page.yaml`: `checkpoint: required`). Before
proceeding to upscale-director, follow `skills/meta/checkpoint-protocol.md`:

1. Show the user the storyboard PNG path AND the 4 cell PNG paths.
2. Highlight observable risks (style drift, identical shot scales, baked
   caption boxes, garbled page numbers).
3. Ask: approve / regenerate / abort.
4. On regenerate: re-run from step 1 (rebuild the prompt; never tweak cells
   individually). On abort: STOP without spending Vertex budget.

## Success criteria

- `output/<slug>/storyboard.png` exists and is ≥ 200 KB.
- `output/<slug>/cells/cell-0{1..4}.png` all exist; each ≥ 30 KB.
- `storyboard.json` validates against schema.
- Visual: 4 distinct cells, recognizable same character across all 4, no
  flat-centered cover.

## Failure modes

- **No new file produced** (`AFTER == BEFORE`) → STOP per the absolute rule.
- **Cell PNGs < 30 KB each** → likely a near-blank generation; regenerate the
  whole storyboard (don't salvage individual cells).
- **All 4 cells share the same shot scale / pose** → page_plan was too
  uniform; bounce back to proposal-director to rewrite scene strings with
  explicit shot-scale + camera-angle + screen-fraction.
- **Baked page-number markers leaking into cell content** → increase
  `top_crop_px` (try 80 or 100) and re-split; do NOT regenerate.
- **Style is illustration-like rather than photographic** → research-director
  Tier 1/2/3 style normalization failed; bounce back, do not try to fix in
  the upscale stage.
