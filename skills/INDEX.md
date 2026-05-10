# openMagazine — Skill Index

3-layer knowledge architecture borrowed from OpenMontage:

~~~
Layer 1: tools/tool_registry.py        "What tools exist and what they can do"
Layer 2: skills/                       "How openMagazine uses these tools"
         {core,creative,meta,pipelines}/  Project-specific conventions
Layer 3: .agents/skills/               "How the technology works (project-agnostic)"
~~~

## Layer 2 directory map

| Folder | Purpose |
|---|---|
| `core/` | helper-usage knowledge (one .md per tool family) |
| `creative/` | creative decision skills (prompt construction, photo realism, etc.) |
| `meta/` | cross-pipeline meta capabilities (onboarding, reviewer, scaffold-style, etc.) |
| `pipelines/<name>/` | per-pipeline stage director skills |

## Capability families & tool discovery

Run at session start:

~~~bash
python -c "from tools.tool_registry import registry, discover; discover(); import json; print(json.dumps(registry.capability_catalog(), indent=2))"
~~~

Currently shipped capabilities:
| Capability | Selector | Default backend |
|---|---|---|
| `image_generation` | `image_selector` | `codex` for storyboard, `vertex` for upscale_4k |
| `image_processing` | — | `pillow_split` |
| `pdf_compose` | — | `reportlab_compose` (only backend) |
| `validation` | — | local Python |
| `meta` | — | `scaffold_style` (agent-driven) |
