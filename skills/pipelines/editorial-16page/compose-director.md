# compose-director — editorial-16page

## Purpose

Stage 6 of editorial-16page. Render `output/<slug>/magazine.pdf` via
**WeasyPrint** from the layout's Jinja2 component templates + article
copy + brand typography pack + 21 × 4K image slots. The compose stage is
deterministic and free (no paid APIs); its main risks are missing input
files, font loading failures, and CSS Paged Media surprises.

## Inputs

- `output/<slug>/upscale_result.json` (21 image paths).
- `output/<slug>/images/spread-NN/<slot>.png` × 21.
- `library/articles/<slug>.yaml` (text copy).
- `library/layouts/editorial-16page.yaml` + `.html.j2` + `_components/*.j2`.
- `library/brands/<brand>.yaml` (schema v2 with `typography` +
  `print_specs` + `visual_tokens`).

Validate before proceeding:
- All 21 PNGs resolve and are ≥ 5 MB (already enforced upstream, but
  recheck defensively here).
- `upscale_result.json` validates against schema.
- Brand yaml is `schema_version: 2` (so `typography` block exists).

## Read first (sub-skills)

Layer 2:
- `library/SCHEMA.md` — typography section + brand v2 schema.
- v0.3 layout components live at `library/layouts/_components/*.j2`.

Layer 3:
- `.agents/skills/weasyprint-cookbook.md` (if present, otherwise refer
  to `tools/pdf/weasyprint_compose.py` docstring).

## Procedure

Use `OutputSelector` with the multi-realizer loop so one spec can produce
multiple output targets (e.g. A4 magazine PDF + PPTX deck) from the same
pipeline. For editorial-16page, the default target dispatches to
`WeasyprintCompose` because `layout.schema_version == 2`.

~~~python
import pathlib, yaml, json
from lib.spec_loader import load_spec, resolve_layers
from tools.output.output_selector import OutputSelector

spec, _ = load_spec(pathlib.Path("library/issue-specs/<slug>.yaml"))
layers = resolve_layers(spec)
article = yaml.safe_load(
    open(f"library/articles/{spec['article']}.yaml", "r", encoding="utf-8")
)
issue_dir = pathlib.Path(f"output/{spec['slug']}")
design_system = layers.get("design_system") or {}

selector = OutputSelector()
results = []
presentations_targets = []
for target in design_system.get("output_targets", [{"format": "a4-magazine", "realizer": "weasyprint"}]):
    if target["realizer"] == "presentations":
        presentations_targets.append(target)
        continue
    backend = selector.choose_backend(target=target)
    result = backend.run(
        issue_dir=issue_dir,
        layout=layers["layout"],
        brand=layers["brand"],
        article=article,
        spec=spec,
        design_system=design_system,
        target=target,
    )
    results.append({"target": target, "result": result})

(issue_dir / "compose_result.json").write_text(json.dumps({
    "outputs": results,
    "pending_presentations_targets": presentations_targets,
    "spec_slug": spec["slug"],
}, indent=2))
~~~

The intermediate `magazine.html` is gitignored but kept on disk —
priceless for debugging when a spread renders blank or wrong.

## Output artifact

`output/<slug>/compose_result.json`, plus `output/<slug>/magazine.pdf`
and `output/<slug>/magazine.html`.

## Checkpoint behavior

`checkpoint: off`. The PDF is shown to the user only at publish-director
time alongside the contact sheet and verify report.

## Success criteria

- `magazine.pdf` exists at `output/<slug>/`.
- `page_count == 16`.
- `size_mb` between 30 and 150 (full editorial with 21 4K embedded
  PNGs typically lands ~40–80 MB).
- `compose_result.json` validates against schema.

## Failure modes

- **WeasyPrint native dep error** (cairo / pango / harfbuzz) → user
  must install via `brew install weasyprint` (macOS) or distro
  equivalent. Document the exact missing dep in the error.
- **Image not found** at expected `images/spread-NN/<slot>.png` path →
  upscale stage incomplete; halt and re-run upscale.
- **Page count != 16** → layout `.html.j2` component fault. Inspect
  `magazine.html` to find the broken spread; common causes:
  - full-bleed div height too tall → forces a page-break splitting one
    spread across two pages
  - unsupported CSS property (e.g., `aspect-ratio`, `mix-blend-mode`,
    `filter: brightness()`) → see fix history at commit `c532656`
- **PDF size > 150 MB** → unusually large; one or more PNGs are over
  4K. Downsample the offending image to 4K (4096px long edge) and
  recompose.
- **PDF size < 30 MB** → likely blank or near-blank pages. Inspect each
  `images/spread-NN/<slot>.png` and `magazine.html` to find the broken
  spread. Don't auto-recompose without isolating the failure.

## Multi-Realizer Orchestration (v0.3.2)

`design_system.output_targets` may list multiple realizers. PDF realizers
run directly above; for each Presentations realizer, invoke the appropriate
director skill:

~~~python
for target in presentations_targets:
    if target["realizer"] == "presentations":
        # → see compose-director-deck.md
        # Agent should now read that file and follow it for this target.
        pass
~~~

Each Presentations realizer appends its final result to
`compose_result.json.outputs` and may remove itself from
`pending_presentations_targets`.
Final structure:

~~~json
{
  "outputs": [
    {"format": "a4-magazine", "realizer": "weasyprint",
     "path": "output/<slug>/magazine.pdf", "page_count": 16, "size_mb": 42.1},
    {"format": "magazine-pptx", "realizer": "presentations",
     "path": "output/<slug>/magazine-pptx/<slug>.pptx", "slide_count": 16,
     "thread_id": "..."}
  ],
  "spec_slug": "<slug>"
}
~~~
