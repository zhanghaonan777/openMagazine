# reviewer

Validate stage artifacts against their JSON schemas before declaring a stage done.

## When to run

Between stages, per `pipeline_defs/<name>.yaml.stages[*].reviewer = enabled`. The reviewer skill is invoked by the next stage director before reading the prior stage's output.

## Procedure

1. **Locate the artifact** at `output/<slug>/<stage>.json`.
2. **Locate the schema** at `schemas/artifacts/<stage>.schema.json`.
3. **Validate**:
   ~~~python
   import json
   from jsonschema import Draft7Validator
   schema = json.load(open("schemas/artifacts/storyboard.schema.json"))
   data = json.load(open("output/<slug>/storyboard.json"))
   errors = list(Draft7Validator(schema).iter_errors(data))
   ~~~
4. **Image-specific extras** (where applicable):
   - Storyboard PNG must exist at `data["png_path"]` and be ≥500 KB.
   - Cells dir must exist at `data["cells_dir"]` with `cell_count` PNGs.
   - Upscale images: each ≥5 MB, ≤40 MB; aspect within 5% of expected.

5. **On failure**: STOP. Print error list. Do NOT proceed to next stage. Tell the user.

## Failure handling

- Schema mismatch is a hard stop, not a warning.
- Image-specific extras: <5 MB → likely a generation failure, regenerate. Aspect mismatch → regenerate with explicit aspect parameter.
- Do NOT auto-fix. Ask the user.

## See also

- `schemas/artifacts/<stage>.schema.json` — per-stage schemas
- `skills/meta/checkpoint-protocol.md` — when reviewer is mandatory vs optional
