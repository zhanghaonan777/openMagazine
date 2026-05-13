# articulate-director — editorial-16page

## Purpose

Stage 3 of editorial-16page (NEW vs v0.2). Produce or load
`library/articles/<slug>.yaml` — the article copy that drives all
spread-level text and per-slot scene descriptions used by storyboard
and upscale.

This is the last text-only stage; the user has one explicit chance here
to read/edit the drafted copy before any image-gen spending begins.

## Inputs

- `output/<slug>/research_brief.json`, `output/<slug>/proposal.json`
- `library/layouts/editorial-16page.yaml` — `spread_plan` +
  `text_slots_required` per spread type.
- `library/themes/<theme>.yaml` — `theme_world` + `page_plan_hints` (used
  as scene scaffolding).
- `library/articles/<slug>.yaml` if `spec.article` resolves to an
  existing file.

## Read first (sub-skills)

- `skills/meta/article-writer.md` — drafting rules (voice, length,
  multi-language, image_slot_overrides).
- `library/articles/README.md` — article schema reference.

## Procedure

1. **Try to load** — if `spec.article` is set and
   `library/articles/<slug>.yaml` exists, load it and skip generation.
   Run `tools/validation/article_validate.py` against it to make sure
   it still matches the layout's text_slots_required.

2. **Otherwise, draft** — follow `skills/meta/article-writer.md`. Each
   spread gets the fields its `text_slots_required` demands. Embed
   `image_slot_overrides` per spread so the storyboard prompt has
   slot-specific scene descriptions.

3. **Persist** — write the drafted copy to
   `library/articles/<slug>.yaml`. Validate via:

   ~~~bash
   uv run python -m tools.validation.article_validate \
     library/articles/<slug>.yaml \
     --layout editorial-16page
   ~~~

   Exit 0 required. If validation fails, refine and retry once; if it
   still fails, STOP and ask the user to write the article manually.

4. **Write artifact** — `output/<slug>/article.json` is a JSON
   projection of the yaml (used by downstream stages for stage chaining
   without re-loading the yaml).

## Design System Resolution

After the article is validated (step 3 above), the articulate director
also resolves and persists a per-issue design-system yaml. This ensures
downstream compose realizers have a fully-specified design contract
before any image-gen budget is spent.

```python
# v0.3.2: also resolve and persist the per-issue design-system
from lib.design_system_loader import resolve_design_system
from tools.validation.design_system_validate import validate_design_system
import yaml, pathlib

design_system = resolve_design_system(spec, layers, profile_name="consumer-retail")
ds_path = pathlib.Path("library/design-systems") / f"{spec['slug']}.yaml"
ds_path.parent.mkdir(parents=True, exist_ok=True)
ds_path.write_text(yaml.safe_dump(design_system, sort_keys=False, allow_unicode=True))

errors = validate_design_system(ds_path)
assert errors == [], f"design-system validation failed: {errors}"

print(f"Resolved design-system → {ds_path}")
print(f"  profile: {design_system['profile']}")
print(f"  output_targets: {[t['format'] for t in design_system['output_targets']]}")
```

The resolved yaml is placed at `library/design-systems/<slug>.yaml`. The
user may edit it at the checkpoint; subsequent stages (storyboard, compose)
read this yaml to drive typography fallback chains, brand authenticity gates,
and output-realizer selection.

## Output artifact

`output/<slug>/article.json` plus the persisted
`library/articles/<slug>.yaml`.

## Checkpoint behavior

**`checkpoint: required`** — the user reviews and edits the drafted
copy before any storyboard image generation. Per
`skills/meta/checkpoint-protocol.md`:

1. Show the user the article yaml path.
2. Print a short structured summary: cover line + first feature title +
   pull-quote text + back coda + total word count.
3. Ask: approve / revise / abort.
4. On revise: collect the user's edits, re-run article_validate, then
   re-show the summary.
5. On abort: STOP without spending any image-gen budget.

## Success criteria

- `library/articles/<slug>.yaml` exists and parses.
- `article_validate` returns 0 (article ↔ layout consistency).
- `article.spread_copy.length == 9` (matches layout's spread_plan).
- All required text_slots are present per spread type.
- Every `image_slot` has a matching scene description in some spread's
  `image_slot_overrides`.
- User explicitly approved at the checkpoint sidecar.

## Failure modes

- **First-draft fails article_validate** → re-prompt the LLM with the
  exact missing-fields list and try ONCE more. Still fails → STOP and
  ask user to write manually.
- **Spec references an article slug that doesn't exist on disk and the
  agent has no LLM available** → STOP. Tell the user the article needs
  to be drafted before this run can proceed.
- **User aborts at checkpoint** → write `output/<slug>/aborted.json`
  with reason; halt the pipeline. No image-gen budget is spent.
