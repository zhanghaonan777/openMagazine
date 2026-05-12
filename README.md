# openMagazine

Agentic photo magazine generation skill, adapted from the OpenMontage
pipeline pattern for editorial photo magazines.

openMagazine turns a subject, reference photo, style, theme, layout, and brand
into an A4 portrait PDF magazine. It is designed for agent runtimes: the agent
reads a declared pipeline, follows stage director skills, records checkpoints,
tracks cost, and writes schema-valid artifacts under `output/<slug>/`.

## What It Makes

- **Photo-book issues**: one full-bleed 4K image per page, with cover/back
  typography integrated into the generated photograph.
- **Editorial issues**: multi-image spreads with real PDF text, typography
  packs, articles, captions, drop caps, page numbers, and Jinja2/WeasyPrint
  layout components.

## Status

Current branch: `feat/v0.3-editorial-engine`.

| Pipeline | Status | Output | Compose Engine |
|---|---|---|---|
| `smoke-test-4page` | production MVP | 4-page photo magazine | ReportLab |
| `editorial-16page` | experimental v0.3.1 | 16-page editorial magazine, 21 image slots, regions-driven | WeasyPrint |

**v0.3.1 update (2026-05-12):** the editorial path is now driven by a shared
"regions" data layer — per-spread yamls declare every bounding box (image
slots, text components, accent rules) and the same data is read by image
generation prompts, WeasyPrint render, and article validation. See
[`docs/superpowers/specs/2026-05-11-regions-as-shared-contract-design.md`](docs/superpowers/specs/2026-05-11-regions-as-shared-contract-design.md)
for the rationale.

The v0.3 editorial pipeline is implemented and has dry-run tests, but live
image generation still requires a Codex CLI session with `image_gen.imagegen`
available for the storyboard stage.

## Runtime Requirement

Stage 3 / 4 storyboard generation depends on Codex CLI's native
`image_gen.imagegen` tool. If that tool is not available, do not attempt a
production run; use a Codex CLI session or a different pipeline.

Vertex Gemini 3 Pro Image is used for 4K slot/page generation.

## Quick Start

```bash
git clone https://github.com/zhanghaonan777/openMagazine.git ~/github/openMagazine
cd ~/github/openMagazine

uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# macOS native deps for v0.3 WeasyPrint compose
brew install weasyprint

# Vertex auth, one time
gcloud auth application-default login --no-launch-browser
gcloud config set project <your-gcp-project-id>

# Install as a Codex skill
ln -s "$PWD" ~/.codex/skills/openmagazine
```

## Try It

In a Codex CLI session:

```text
Make me a 4-page magazine of my cat in National Geographic style.
```

For the v0.3 editorial run:

```text
Run the editorial-16page pipeline with library/issue-specs/<slug>.yaml.
Stop at the articulate gate and storyboard gate for approval.
```

See [docs/SMOKE_TEST_v0.3.md](docs/SMOKE_TEST_v0.3.md) for the first live
editorial runbook.

## Pipelines

All production work goes through `pipeline_defs/<name>.yaml`.

### `smoke-test-4page`

Six stages:

```text
research -> proposal -> storyboard -> upscale -> compose -> publish
```

This path uses:

- `library/layouts/plain-4.yaml`
- `library/templates/storyboard.prompt.md`
- `library/templates/upscale_{cover,inner,back}.prompt.md`
- `tools/pdf/reportlab_compose.py`

### `editorial-16page`

Seven stages:

```text
research -> proposal -> articulate -> storyboard -> upscale -> compose -> publish
```

This path adds:

- `library/articles/<slug>.yaml` — per-issue editorial copy
- `library/layouts/editorial-16page.yaml` + `.html.j2` — layout shell
- `library/layouts/_components/*.j2` — 7 spread components (cover, toc,
  feature-spread, pull-quote, portrait-wall, colophon, back-cover)
- `library/layouts/_components/*.regions.yaml` — ★ regions data layer
  (v0.3.1): per-spread bounding boxes that image gen + render + validation
  all read
- `library/layouts/_components/_macros/region.j2.html` — `render_region`
  dispatch macros
- `library/components/registry.yaml` — closed component vocabulary
  (15 components: Kicker, Title, BodyWithDropCap, PullQuote, AccentRule, …)
- `lib/storyboard_planner.py` — multi-aspect grid packer
- `lib/prompt_builder_v2.py` — role-driven upscale prompts (accepts
  `regions_context` to tell the model which rects to keep calm)
- `lib/regions_loader.py` — load + walk regions yamls
- `lib/prompt_persistence.py` — save every prompt + a run manifest to
  `output/<slug>/prompts/` so issues are reproducible / auditable
- `tools/pdf/weasyprint_compose.py` — WeasyPrint backend
- `tools/pdf/pdf_selector.py` — routes by `layout.schema_version`
- `tools/validation/regions_validate.py` — JSON-schema + overlap +
  component-registry check for regions yamls

## Verify Locally

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

Useful targeted checks:

```bash
python -m tools.validation.article_validate \
  library/articles/cosmos-luna-may-2026.yaml \
  --layout library/layouts/editorial-16page.yaml

python -m pytest tests/integration/test_render_dry_run.py -v
```

If WeasyPrint fails with a missing `libpango`, `cairo`, or `harfbuzz`
library, install the native dependencies first (`brew install weasyprint` on
macOS), then rerun the dry-run test.

## Architecture

See:

- [AGENT_GUIDE.md](AGENT_GUIDE.md) for the production rules.
- [CODEX.md](CODEX.md) for Codex-specific image generation capture.
- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for the original architecture map.
- [docs/v0.3-ARCHITECTURE.md](docs/v0.3-ARCHITECTURE.md) for the editorial
  layout engine.
- [docs/regions-reference.md](docs/regions-reference.md) — every spread's
  regions yaml + region field schema (v0.3.1).
- [docs/component-registry-reference.md](docs/component-registry-reference.md)
  — the 15 components a region can name (v0.3.1).
- [docs/typography-pack-cookbook.md](docs/typography-pack-cookbook.md) for
  authoring v2 brand typography packs.
- [docs/SCHEMA_V2_MIGRATION.md](docs/SCHEMA_V2_MIGRATION.md) for v1 -> v2
  migration notes.
- [docs/superpowers/specs/2026-05-11-regions-as-shared-contract-design.md](docs/superpowers/specs/2026-05-11-regions-as-shared-contract-design.md)
  — the v0.3.1 regions design rationale.

## Known Gaps (as of v0.3.1)

- **Live smoke test pending.** The editorial pipeline is implementation-
  complete with 137/137 tests green and dry-run integration passing, but
  no end-to-end Codex CLI run has been performed yet. See
  [docs/SMOKE_TEST_v0.3.md](docs/SMOKE_TEST_v0.3.md) for the runbook.
- **TOC + colophon literal headings lost.** During the regions migration,
  fixed strings like "CONTENTS" and "COLOPHON" became empty `text_decorative`
  divs. Fix path: add a `component_props.literal_text` field.
- **`Verify4K` still validates v1 paths.** It expects
  `images/page-NN.png`; v0.3 uses nested `images/spread-NN/<slot>.png`.
  Publish stage will fail until this is extended.
- **Some artifact schemas still v1-shaped.** `upscale_result.schema.json`
  and a few others assume the v1 flat path layout.
- **WeasyPrint requires native system libraries** in addition to Python
  packages (`brew install weasyprint` on macOS).

## License

AGPLv3
