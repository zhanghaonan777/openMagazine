# Architecture

See [`PROJECT_CONTEXT.md`](../PROJECT_CONTEXT.md) at the repo root for the canonical architecture overview. This file expands on three topics.

## 1. Layer-by-layer responsibilities

### Layer 1 — `tools/`

Python tool implementations grouped into 4 capability families:

| Family | Modules | Capability declaration |
|---|---|---|
| `tools/image/` | `codex_image_gen`, `vertex_gemini_image`, `image_selector`, `pillow_split` | `image_generation`, `image_processing` |
| `tools/pdf/` | `reportlab_compose` | `pdf_compose` |
| `tools/validation/` | `verify_4k`, `spec_validate`, `reference_photo_check` | `validation` |
| `tools/meta/` | `scaffold_style` (stub) | `meta` |

Each tool subclasses `BaseTool` from `tools/base_tool.py` and auto-registers on import via `tools.tool_registry.registry`. Discovery is triggered by `tools.tool_registry.discover()` which imports every capability-family package.

### Layer 2 — `skills/`

Project-specific knowledge, organized by purpose:

| Folder | Purpose |
|---|---|
| `skills/core/` | Helper-usage docs (one .md per tool family) |
| `skills/creative/` | Creative decision skills (prompt construction, photo realism, shot scale variety) |
| `skills/meta/` | Cross-pipeline meta capabilities (onboarding, reviewer, checkpoint, cost-budget-enforcer, etc.) |
| `skills/pipelines/<name>/` | Per-pipeline stage director skills (one .md per stage) |

The agent reads `skills/INDEX.md` first, then per-stage director skills as it traverses a pipeline.

### Layer 3 — `.agents/skills/`

Project-agnostic API knowledge. These docs are reusable across projects and contain no openMagazine-specific terminology. Each tool's `agent_skills` attribute names a Layer 3 doc; the agent reads the relevant doc before calling the tool.

### Data layer — `library/`, `styles/`, `schemas/`, `pipeline_defs/`, `examples/`

- `library/` — 4 reference layers: subjects, themes, layouts, brands, plus issue-specs
- `styles/` — top-level (not under library/), 9 style yamls
- `schemas/` — JSON Schemas for artifacts and pipeline manifests
- `pipeline_defs/` — pipeline manifests
- `examples/` — reference photos for the included issue-specs

## 2. Schema-first data flow

Each pipeline stage produces a schema-validated JSON sidecar. The next stage's reviewer skill validates that sidecar before reading any other input.

```
research → research_brief.json (schemas/artifacts/research_brief.schema.json)
proposal → proposal.json
storyboard → storyboard.json + storyboard.png + cells/cell-NN.png × N
upscale → upscale_result.json + images/page-NN.png × N
compose → compose_result.json + magazine.pdf
publish → publish_report.json + contact_sheet.jpg
```

The `tests/contracts/test_pipeline_contracts.py` test asserts that every artifact name declared in `pipeline_defs/*.yaml` has a corresponding schema file in `schemas/artifacts/`.

## 3. Selector pattern

Selectors route requests to specific backend tools based on a `mode` parameter. The MVP ships one:

`tools/image/image_selector.py`:
~~~python
class ImageSelector(BaseTool):
    capability = "image_generation"

    def choose_backend(self, *, mode: str) -> BaseTool:
        if mode == "storyboard":
            return self._codex   # CodexImageGen
        elif mode == "upscale_4k":
            return self._vertex  # VertexGeminiImage
        else:
            raise ValueError(f"unknown mode {mode!r}")
~~~

Why selectors: they decouple the agent's stage director (which says "I need an upscale_4k call") from the specific backend (Vertex today, Imagen 4 tomorrow). Adding a new backend is one new tool module + one branch in the selector — no churn in stage directors.

Future: a `pdf_selector` would route between `reportlab_compose` and a future alternative (e.g., a paginated-EPUB backend).
