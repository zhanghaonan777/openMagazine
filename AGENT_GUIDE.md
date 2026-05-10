# openMagazine — Agent Guide

> **v0.1 MVP status:** Some files this guide references (`skills/`, `pipeline_defs/`, `CODEX.md`, `CLAUDE.md`, `.agents/skills/`) land in later MVP tasks. If you hit a missing path, see [`README.md`](README.md) for current status before improvising.

## First Interaction

If user input is vague (e.g., "what can you do", "make me something"), read [`skills/meta/onboarding.md`](skills/meta/onboarding.md) before doing anything else. Skip onboarding if user gave an actionable request (e.g., "make a 4-page magazine of my cat in cosmos style").

## Rule Zero — All production goes through a pipeline

Every magazine production request MUST go through a pipeline declared in `pipeline_defs/<name>.yaml`.

1. **Identify the pipeline.** Match user's request to one of the pipelines. If unclear, ask.
2. **Read the pipeline manifest.** `pipeline_defs/<name>.yaml` — know the stages, tools, checkpoints, and cost budget.
3. **Run preflight.** Discover available tools via `python -c "from tools.tool_registry import registry; registry.discover(); print(registry.capability_catalog())"`.
4. **Execute stage by stage.** For each stage, read the stage director skill (`skills/pipelines/<pipeline>/<stage>-director.md`) BEFORE doing any work.
5. **Read Layer 3 skills before calling tools.** Tools declare `agent_skills = [...]`; for each, read the corresponding `.agents/skills/<name>.md`.

DO NOT:
- Write ad-hoc Python scripts to call tools directly
- Skip the pipeline and go straight to API calls
- Generate assets without reading the stage director skill first
- Bypass checkpoints or reviewer

## Two input sources

- **Free-form** — user one-liner + photo. Agent infers traits, looks up styles via Author Obligation 2, defaults theme/layout/brand. Auto-persists a spec yaml after Stage 3.
- **Spec input** — user references `library/issue-specs/<slug>.yaml`. Agent reads the spec and resolves 5 layer references.

Both feed the same 6-stage pipeline.

## Decision Communication Contract

Before any paid generation call, announce:
- exact tool name
- provider
- model variant
- estimated cost
- cumulative cost vs budget

Wait for explicit user OK only when the stage's `checkpoint: required` (default: only Stage 3 storyboard).

## Six stages of the magazine pipeline

| # | Stage | Director skill | Default checkpoint |
|---|---|---|---|
| 1 | research | `skills/pipelines/<pipe>/research-director.md` | off |
| 2 | proposal | `skills/pipelines/<pipe>/proposal-director.md` | off |
| 3 | storyboard | `skills/pipelines/<pipe>/storyboard-director.md` | required |
| 4 | upscale | `skills/pipelines/<pipe>/upscale-director.md` | off |
| 5 | compose | `skills/pipelines/<pipe>/compose-director.md` | off |
| 6 | publish | `skills/pipelines/<pipe>/publish-director.md` | off |

For runtime-specific concerns:
- Codex CLI: see [`CODEX.md`](CODEX.md)
- Claude Code: see [`CLAUDE.md`](CLAUDE.md) — Stage 3 unsupported; STOP and ask user to switch to codex CLI
