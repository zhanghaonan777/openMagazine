# checkpoint-protocol

How to handle stage checkpoints — pause for user approval at high-impact / costly stages.

## Three modes

| Mode | Behavior |
|---|---|
| `required` | STOP after stage. Write checkpoint sidecar. Wait for user approval before next stage. |
| `optional` | Write checkpoint sidecar. Proceed unless user has set `--checkpoint-all` or similar. |
| `off` | No sidecar; proceed immediately. |

Per-stage default modes are in `pipeline_defs/<name>.yaml`. The default magazine pipeline has only Stage 3 (storyboard) `required` — others off.

## Sidecar format

`output/<slug>/<stage>.checkpoint.json`:

~~~json
{
  "stage": "storyboard",
  "artifact_path": "output/<slug>/storyboard.json",
  "preview_paths": ["output/<slug>/storyboard.png", "output/<slug>/cells/"],
  "decision_required": "approve | retry | abort",
  "user_decision": null,
  "user_notes": null
}
~~~

## Asking the user

Display:
1. The artifact (e.g., open the storyboard PNG, list cells).
2. Page plan summary (scene title + shot scale per cell).
3. Cost so far / budget remaining.
4. Three options: APPROVE / RETRY (with reason) / ABORT.

Do NOT proceed until user picks one. Update `user_decision` / `user_notes` in the sidecar JSON. Commit progression in the artifact directory.

## Rejection handling

- `retry`: re-run the stage with user's reason as additional context. Increment a retry counter; cap at 3.
- `abort`: STOP the pipeline. Write `output/<slug>/aborted.json` with the reason.

## See also

- `pipeline_defs/<name>.yaml` — per-stage checkpoint mode
- `skills/meta/cost-budget-enforcer.md` — cumulative cost tracking
