---
name: openmagazine
description: Generate editorial photo magazine PDFs with the openMagazine pipeline. Use when the user asks to make a photo magazine, personalized magazine, photo book, lookbook, editorial issue, Vogue/National Geographic/Kinfolk-style magazine, or similar multi-page image-driven PDF featuring a subject, pet, person, place, product, or concept.
---

# openMagazine

Use this skill to run the openMagazine project as a Codex skill.

## Entry Points

- Read `AGENT_GUIDE.md` before doing openMagazine production work.
- Read `CODEX.md` for Codex-specific runtime constraints, especially image generation capture.
- For vague requests, read `skills/meta/onboarding.md` first.
- For actionable magazine requests, choose a pipeline from `pipeline_defs/`, then follow that pipeline stage by stage.

## Required Workflow

All production must go through a declared pipeline. Choose the smallest pipeline
that matches the request:

| Pipeline | Use when |
|---|---|
| `pipeline_defs/smoke-test-4page.yaml` | Cheap 4-page validation, one 4K image per page, ReportLab PDF. |
| `pipeline_defs/editorial-16page.yaml` | v0.3 editorial issues with article copy, 21 image slots, real PDF text, and WeasyPrint. |

For each stage:

1. Read the pipeline manifest.
2. Read the relevant stage director skill in `skills/pipelines/<pipeline>/`.
3. Discover tool capabilities through `tools/tool_registry.py`.
4. Read any tool-declared `.agents/skills/` references before calling that tool.
5. Respect checkpoints, reviewer guidance, schemas, and budget communication in `AGENT_GUIDE.md`.

Do not bypass the pipeline with ad-hoc asset generation or direct API scripts.

## Runtime Gate

Stage 3 storyboard generation requires the native `image_gen.imagegen` tool.
Run preflight before attempting production. If the runtime does not expose that
tool, stop and ask the user to rerun from Codex CLI or use the predecessor
`only_image_magazine_gen` skill.
