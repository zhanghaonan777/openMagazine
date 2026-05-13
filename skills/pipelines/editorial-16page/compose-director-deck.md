# compose-director-deck — editorial-16page

## Purpose

Realize a `deck-pptx` output target via the Codex Presentations skill.
This director is invoked when `design_system.output_targets` contains
a `deck-pptx` entry. The PDF output (`a4-magazine`) is handled by the
sibling compose-director.md.

## Inputs

- `output/<slug>/compose_result.json` (in-progress, may contain other
  realizer results)
- All standard upstream artifacts (research_brief, proposal, article,
  storyboard, upscale_result, design-system).
- `output/<slug>/images/spread-NN/<slot>.png` × 21 — the 4K image
  slots are reused; PPTX uses crops/thumbs of the same source PNGs.

## Read first

- `skills/meta/design-system-author.md` for what's in design_system
- `~/.codex/plugins/cache/openai-primary-runtime/presentations/.../skills/presentations/SKILL.md` for the skill's mandatory workflow

## Procedure

### 1. Build the input bundle

~~~python
from tools.output.presentations_adapter import PresentationsAdapter
import pathlib, yaml, json

adapter = PresentationsAdapter()
issue_dir = pathlib.Path(f"output/{spec['slug']}")
design_system = layers["design_system"]

bundle = adapter.build_input_bundle(
    design_system=design_system,
    brand=layers["brand"],
    article=article,
    regions_by_spread_type=layers.get("regions_by_spread_type"),
)
~~~

### 2. Compose the Presentations prompt

The agent invokes Presentations with this prompt structure. The
`task-slug` is critical — it determines where Presentations writes:

~~~text
Use the Presentations skill to build a {slide_count}-slide editorial deck
that mirrors my openMagazine v0.3.2 issue.

WORKSPACE: outputs/$CODEX_THREAD_ID/presentations/{task_slug}

PRE-RESOLVED INPUTS (do not redecide these):
- presentations_profile: {bundle["presentations_profile"]}
- typography (with resolved fallback chain): {bundle["typography"]}
- text-safe rules: {bundle["text_safe_rules"]}
- brand authenticity gates: {bundle["brand_authenticity"]}
- brand masthead: {bundle["brand_masthead"]}
- accent color: {bundle["brand_color_accent"]}

ARTICLE TITLES PER SPREAD:
{json.dumps(bundle["article_titles"], indent=2)}

REGIONS (for layout intent reuse):
{json.dumps(bundle["regions_summary"], indent=2)}

CONSTRAINTS:
- Task mode: create (no reference deck supplied)
- Preserve all intermediate artifacts under $WORKSPACE
- Final .pptx → $WORKSPACE/output/{spec_slug}.pptx
- Do not approximate logos / mascots / app icons per brand
  authenticity gate above
- Match openMagazine's spread types one-to-one when possible (cover,
  toc, 3 features, pull-quote, portrait-wall, colophon, back-cover)

REPORT BACK with:
- $CODEX_THREAD_ID so I can find the artifacts
- profile-plan.txt content
- font-substitutions.txt content
- qa/layout-quality.txt output
- final .pptx path + size
~~~

### 3. Read back artifacts

After the Presentations skill reports completion:

~~~python
artifacts = adapter.read_artifacts(
    thread_id=codex_thread_id,
    task_slug=bundle["task_slug"],
    issue_dir=issue_dir,
)

# Copy the final .pptx into our issue's deck/ subdir
final_pptx = adapter.copy_final_to_issue_deck(
    pptx_source=artifacts["pptx_path"],
    issue_dir=issue_dir,
    slug=spec["slug"],
)
print(f"PPTX → {final_pptx}")
print(f"Slides: {artifacts['slide_count']}")
print(f"Font substitutions: {artifacts['font_substitutions'][:200]}")
~~~

### 4. Validate

Run `check_layout_quality.mjs` on each Presentations layout JSON
(this was empirically validated standalone in the smoke test):

~~~bash
PRES=~/.codex/plugins/cache/openai-primary-runtime/presentations/26.506.11943/skills/presentations
for layout in $(ls outputs/$CODEX_THREAD_ID/presentations/<task_slug>/layout/slide-*.layout.json); do
    node $PRES/scripts/check_layout_quality.mjs --layout $layout
done
~~~

If any layout reports errors, log them but don't fail compose — they're
informational for the user.

### 5. Append to compose_result.json

~~~python
compose_result_path = issue_dir / "compose_result.json"
existing = json.loads(compose_result_path.read_text()) if compose_result_path.is_file() else {"outputs": []}
existing["outputs"].append({
    "format": "deck-pptx",
    "realizer": "presentations",
    "path": str(final_pptx),
    "slide_count": artifacts["slide_count"],
    "thread_id": codex_thread_id,
})
compose_result_path.write_text(json.dumps(existing, indent=2))
~~~

## Checkpoint behavior

`checkpoint: off` — deck output is parallel to PDF, no separate gate.

## Success criteria

- `output/<slug>/deck/<slug>.pptx` exists and is ≥ 100 KB
- `compose_result.json` has a `deck-pptx` entry
- `check_layout_quality.mjs` ran on all layouts (output captured)

## Failure modes

- **Presentations skill not available** → STOP and ask user to verify
  Codex CLI version (need bundled artifact-tool ≥ 2.7.3)
- **Artifact dir doesn't exist after Presentations reports done** →
  Presentations chose a different `task_slug`; ask user for actual
  thread_id and confirm
- **Final .pptx empty** → layout error inside Presentations; user
  should inspect $WORKSPACE/qa/comeback-scorecard.txt
