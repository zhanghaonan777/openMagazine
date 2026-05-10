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
- protagonist-1.jpg exists and is ≥ 200 KB.
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

### 1. Per-page prompt construction

Substitute `{{TRAITS}}`, `{{STYLE_ANCHOR}}`, `{{THEME_WORLD}}`,
`{{MAGAZINE_NAME}}`, `{{COVER_LINE}}`, `{{SCENE_NN}}`, `{{ACTION_VERB_NN}}`
verbatim from `research_brief.json` and `storyboard.page_plan[*]`. Never
paraphrase between stages; the storyboard locked these strings.

References per call (order matters — first ref dominates composition):

| Page | Refs (in order) | Output path |
|---|---|---|
| 01 cover | `cells/cell-01.png`, `refs/protagonist-1.jpg` | `images/page-01.png` |
| 02 inner | `cells/cell-02.png`, `refs/protagonist-1.jpg` | `images/page-02.png` |
| 03 inner | `cells/cell-03.png`, `refs/protagonist-1.jpg` | `images/page-03.png` |
| 04 back | `cells/cell-04.png`, `refs/protagonist-1.jpg` | `images/page-04.png` |

#### Page 01 — Cover prompt template (Phase 4 cover, adapted from predecessor)

~~~text
Subject: {{TRAITS}}, in a hero pose appropriate to {{THEME_WORLD}}.

Scene: cover hero composition. The subject occupies the upper two-thirds
of the frame, looking off-frame slightly to the right (eyeline gives the
masthead room to breathe).

Composition: maintain framing and lighting direction from the FIRST
reference image (cell-01). Character identity from SUBSEQUENT reference
images (protagonist photos).

Lighting: dramatic single key light, deep shadow side. No rim light.

Camera: shot on Hasselblad H6D-100c with 80mm f/2.8 prime. Raw uncorrected,
no color grading.

Typography (rendered as if hand-painted / printed lettering integrated
INTO the photograph itself, NOT as a separate footer bar overlaying the
photo, NOT a clip-art-style barcode strip):
- Masthead at top: "{{MAGAZINE_NAME}}" extra-large serif, all caps,
  dominant; treat as a true title block painted onto the wall surface
  or printed into a real banner element of the scene.
- Cover line stacked lower-left: "{{COVER_LINE}}" — large serif, all
  caps, 2-3 stacked lines maximum, integrated against the actual
  photo background (e.g., painted on the same wall as the masthead, or
  printed onto a fabric banner in the scene).
- NO bottom-strip footer bar with VOL/DATE numerals. NO barcode. NO
  ISSN. NO PDF-mockup-like horizontal band cutting across the bottom
  of the image. The cover should feel a full-bleed editorial
  photograph, not a photo-plus-UI-footer composite.

Style: {{STYLE_ANCHOR}}, with high-end editorial photography finish — slight
paper grain and ink density visible.

Negative prompt: lorem ipsum, gibberish letterforms, garbled type, broken
serifs, watermarks, logos that aren't the masthead, AI-looking type, deformed
anatomy, anime cute, oversized eyes, plastic skin/fur, oily highlights, rim
lighting, footer bar / footer strip / horizontal band of solid color across
the bottom of the image, barcode, ISSN, version numerals, date strip,
"VOL." text, no visible page numbers, no cell labels, no annotation
overlays, no scratch tracing of storyboard guides.
~~~

#### Pages 02 & 03 — Inner page prompt template (Phase 3 inner)

~~~text
Subject: {{TRAITS}}.

Scene: {{SCENE_NN}}. {{ACTION_VERB_NN}}.

Composition: maintain the layout, character placement, and lighting
direction from the FIRST reference image (the storyboard cell). Maintain
character identity (face, markings, build, expression) from the SUBSEQUENT
reference images (the protagonist photos).

Camera: shot on Sony Alpha 7R V with Sigma 35mm f/1.4 Art lens. ISO 200,
1/500s shutter. Raw uncorrected file, no color grading, no LUTs, no
post-processing.

Texture detail: surface imperfections visible — individual fur strands,
skin pores, fabric weave; micro-shadows; natural light falloff; subtle
motion blur on action elements.

Style: {{STYLE_ANCHOR}}

Negative prompt: cartoonish, AI-looking, plastic skin/fur, over-smoothed,
glossy CGI rendering, anime cute, oversized eyes, perfect grooming,
beauty-filter aesthetic, plush show appearance, 3D render look, oily
highlights, rim lighting, painted whiskers, mournful expression, droopy
eyes, sad/sick face, extra limbs, deformed anatomy, garbled typography,
watermarks, logos, no visible page numbers, no cell labels, no annotation
overlays, no scratch tracing of storyboard guides.
~~~

#### Page 04 — Back cover prompt template (Phase 4 back-cover)

~~~text
Subject: {{TRAITS}}, quiet coda pose appropriate to {{THEME_WORLD}}.

Scene: a single small element of the subject in mostly empty space. Calm,
quiet, restrained. Bottom 30% of frame is negative space.

Composition: maintain framing from the FIRST reference image (cell-04).
Character identity from SUBSEQUENT reference images.

Lighting: soft, diffused, low-contrast. Late-day or pre-dawn quality.

Camera: shot on Leica M11 with Summicron 50mm. Raw uncorrected.

Typography (rendered as if hand-painted / printed lettering integrated
INTO the photograph itself, NOT as a separate footer bar):
- Optional lower-third: a single short quote in small italic serif, 1-2
  lines, painted onto a wall surface or fabric in the scene. If
  photographically awkward to integrate, prefer NO typography at all
  on the back cover — full-bleed quiet coda photo is the goal.
- NO masthead. NO cover line. NO bottom-strip footer bar with VOL/DATE
  numerals. NO barcode. NO ISSN. NO horizontal solid-color band across
  the bottom. NO colophon footer band.

Style: {{STYLE_ANCHOR}}.

Negative prompt: same as cover prompt above. Especially important here:
no visible page numbers, no cell labels, no annotation overlays, no
scratch tracing of storyboard guides — the back-cover storyboard cell
often has "04" or "back" page-number markers that leak into 4K output if
not explicitly negated (validated failure mode: naigai-fauvist 4-page
test, 2026-05-10 — page-04 retained the cell-04 top-left "04" marker).
~~~

### 2. Run all 4 calls

Driver call (parallelism gated by `config.yaml` → `defaults.parallelism: 3`):

~~~python
from tools.image.vertex_gemini_image import VertexGeminiImage
import pathlib

tool = VertexGeminiImage()
issue_dir = pathlib.Path("output/<slug>")
for page_idx, prompt in [(1, cover_prompt), (2, inner_02), (3, inner_03), (4, back_prompt)]:
    tool.run(
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
~~~

`skip_existing=True` makes regeneration cheap — if a single page comes back
broken, delete just `images/page-NN.png` and re-run; the other 3 are skipped.

### 3. Cost announcement

Per `skills/meta/cost-budget-enforcer.md`, announce each call before issuing
it: `"Vertex page-NN: $0.24 (cumulative $X.XX of $0.96)"`. Hard-stop if
cumulative exceeds the proposal's `cost_estimate_usd` by more than 10%.

### 4. Write the artifact

Schema: `schemas/artifacts/upscale_result.schema.json`. Path:
`output/<slug>/upscale.json`.

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

`output/<slug>/upscale.json` (above) plus 4 PNGs at
`output/<slug>/images/page-0{1..4}.png`.

## Checkpoint behavior

Default `checkpoint: off` in `pipeline_defs/smoke-test-4page.yaml`. The 4
pages flow straight into compose-director. (User would have caught style
drift at the storyboard checkpoint already.)

## Success criteria

- 4 PNGs at `images/page-0{1..4}.png`, each 5–30 MB.
- Each is 2:3 portrait at ≥ 2048 × 3072 (validated downstream by `Verify4K`).
- `upscale.json` validates against schema; `vertex_calls_made == 4` and
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
