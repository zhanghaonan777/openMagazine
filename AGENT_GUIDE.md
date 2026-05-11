# openMagazine — Agent Guide

> **v0.3 status:** Two production paths coexist. `smoke-test-4page` keeps the
> legacy simple image-per-page path; `editorial-16page` adds article copy,
> multi-image spreads, and WeasyPrint composition.

## First Interaction

If user input is vague (e.g., "what can you do", "make me something"), read [`skills/meta/onboarding.md`](skills/meta/onboarding.md) before doing anything else. Skip onboarding if user gave an actionable request (e.g., "make a 4-page magazine of my cat in cosmos style").

## Rule Zero — All production goes through a pipeline

Every magazine production request MUST go through a pipeline declared in `pipeline_defs/<name>.yaml`.

1. **Identify the pipeline.** Match user's request to one of the pipelines. If unclear, ask.
2. **Read the pipeline manifest.** `pipeline_defs/<name>.yaml` — know the stages, tools, checkpoints, and cost budget.
3. **Run preflight.** Discover available tools via `uv run python -c "from tools.tool_registry import registry; registry.discover(); print(registry.capability_catalog())"`, then verify the runtime exposes `image_gen.imagegen` before Stage 3.
4. **Execute stage by stage.** For each stage, read the stage director skill (`skills/pipelines/<pipeline>/<stage>-director.md`) BEFORE doing any work.
5. **Read Layer 3 skills before calling tools.** Tools declare `agent_skills = [...]`; for each, read the corresponding `.agents/skills/<name>.md`.

DO NOT:
- Write ad-hoc Python scripts to call tools directly
- Skip the pipeline and go straight to API calls
- Generate assets without reading the stage director skill first
- Bypass checkpoints or reviewer

## Two input sources

- **Free-form** — user one-liner + photo. Agent infers traits, looks up styles, defaults theme/layout/brand, and persists a spec yaml.
- **Spec input** — user references `library/issue-specs/<slug>.yaml`. Agent reads the spec and resolves v1's 5 references or v2's 5 required references plus optional `article`.

Both feed a declared pipeline. v1 specs use the simple 6-stage path; v2 editorial specs use a 7-stage path with `articulate`.

## Decision Communication Contract

Before any paid generation call, announce:
- exact tool name
- provider
- model variant
- estimated cost
- cumulative cost vs budget

Wait for explicit user OK only when the stage's `checkpoint: required` (default: only Stage 3 storyboard).

## Pipeline stages

| # | Stage | Simple path | Editorial path | Default checkpoint |
|---|---|---|---|
| 1 | research | yes | yes | off |
| 2 | proposal | yes | yes | off |
| 3 | articulate | no | yes | required |
| 4 | storyboard | yes | yes | required |
| 5 | upscale | yes | yes | off |
| 6 | compose | yes | yes | off |
| 7 | publish | yes | yes | off |

For runtime-specific concerns:
- Codex CLI: see [`CODEX.md`](CODEX.md)
- Claude Code / Codex desktop without `image_gen.imagegen`: Stage 3 unsupported; STOP and ask user to switch to Codex CLI or use the predecessor skill.
