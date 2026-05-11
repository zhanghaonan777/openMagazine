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
| `editorial-16page` | experimental v0.3 | 16-page editorial magazine, 21 image slots | WeasyPrint |

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

- `library/articles/<slug>.yaml`
- `library/layouts/editorial-16page.yaml`
- `library/layouts/editorial-16page.html.j2`
- `library/layouts/_components/*.j2`
- `lib/storyboard_planner.py`
- `lib/prompt_builder_v2.py`
- `tools/pdf/weasyprint_compose.py`

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
- [docs/SCHEMA_V2_MIGRATION.md](docs/SCHEMA_V2_MIGRATION.md) for v1 -> v2
  migration notes.

## Known v0.3 Gaps

- The repository currently ships a v0.3 article example, but still needs a
  matching v2 issue spec for one-command editorial smoke runs.
- Some artifact schemas are still v1-shaped and need v2-compatible fields.
- `Verify4K` currently validates v1 `images/page-*.png` outputs and should be
  extended for v0.3 nested `images/spread-NN/<slot>.png` outputs.
- WeasyPrint requires native system libraries in addition to Python packages.

## License

AGPLv3
