# Project Context

## Architecture

4 conceptual layers + 1 orthogonal Layer 3:

```
Agent layer (codex / claude / cursor)
  └─ reads AGENT_GUIDE.md + pipeline_defs + per-stage director skills

Knowledge layer (skills/)
  ├─ core/       helper usage docs
  ├─ creative/   creative decision skills
  ├─ meta/       cross-pipeline meta capabilities
  └─ pipelines/<name>/  per-pipeline stage directors

Tool layer (tools/)
  ├─ tool_registry.py    auto-discovery + capability catalog
  ├─ base_tool.py
  └─ {image, pdf, validation, meta}/  4 capability families

Data layer (library/ + styles/ + schemas/)

Layer 3 (.agents/skills/)
  └─ generic API knowledge, project-agnostic
```

## Key file locations

| What | Where |
|---|---|
| Agent entry | `AGENT_GUIDE.md` |
| Per-agent adapter | `CODEX.md`, `CLAUDE.md` (CURSOR/COPILOT future) |
| Pipeline manifest | `pipeline_defs/<name>.yaml` |
| Stage director skill | `skills/pipelines/<pipeline>/<stage>-director.md` |
| Tool definition | `tools/<family>/<tool>.py` |
| Generic API knowledge | `.agents/skills/<topic>.md` |
| Style library | `styles/<name>.yaml` |
| Subject / theme / layout / brand library | `library/<layer>/<name>.yaml` |
| One-stop issue spec | `library/issue-specs/<slug>.yaml` |
| Artifact schemas | `schemas/artifacts/<artifact>.schema.json` |
| Generated artifacts | `output/<slug>/` (gitignored) |

## Data flow

Simple path (`schema_version: 1`, `smoke-test-4page`):

```
spec.yaml or free-form
    │
    ▼
research → proposal → storyboard → ⏸ gate → upscale → compose → publish
                          │                     │           │          │
                          ▼                     ▼           ▼          ▼
              storyboard.png       images/page-NN.png   magazine.pdf   publish_report.json
              storyboard.json      upscale_result.json  compose_result.json   contact_sheet.jpg
              cells/cell-NN.png
```

Editorial path (`schema_version: 2`, `editorial-16page`):

```
spec.yaml or free-form
    │
    ▼
research → proposal → articulate → ⏸ gate → storyboard → ⏸ gate → upscale → compose → publish
                             │                       │                    │          │
                             ▼                       ▼                    ▼          ▼
                 library/articles/<slug>.yaml   storyboard.png   images/spread-NN/<slot>.png
                 article.json                   storyboard.json  upscale_result.json
                                                cells/spread-NN/<slot>.png
                                                                  magazine.html
                                                                  magazine.pdf
                                                                  publish_report.json
```

Each stage produces one schema-valid sidecar JSON. The reviewer skill validates between stages.

## Conventions

- Filesystem state. No `state.json`. `output/<slug>/` is the source of truth.
- v1 and v2 schemas coexist. v2 applies to editorial specs, brands, and layouts; article yaml remains `schema_version: 1`.
- Prefer `uv run python -m ...` or an activated venv.
- 3 concurrent Vertex calls maximum. `lib.config_loader.get_parallelism()` clamps higher config or env values back to 3.
- Simple storyboard cells may require top-cropping to remove page-number labels; editorial storyboard splitting uses the planned 21 image-slot bboxes.
