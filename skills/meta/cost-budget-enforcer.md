# cost-budget-enforcer

Track cumulative cost across pipeline stages and enforce the issue budget.

## Announce-decision contract

Before ANY paid call:
1. Print: "About to call <tool> (provider=<provider>, model=<model>). Estimated cost: $<X>. Cumulative: $<Y> / $<budget>."
2. If `pipeline_defs/<name>.yaml.stages[*].checkpoint = required`, wait for user approval.
3. If `cumulative_after / budget >= 0.80`: WARN.
4. If `cumulative_after / budget >= 1.10`: HARD STOP. Tell the user the budget is exceeded.

## Cost ledger

Maintain `output/<slug>/costs.json`:

~~~json
{
  "spec_slug": "naipi-burberry-4page-01",
  "budget_usd": 0.96,
  "calls": [
    {"stage": "storyboard", "tool": "CodexImageGen", "provider": "codex", "cost_usd": 0.04, "ts": "2026-05-10T15:00Z"},
    {"stage": "upscale", "tool": "VertexGeminiImage", "provider": "vertex", "cost_usd": 0.24, "ts": "..."}
  ],
  "cumulative_usd": 0.28
}
~~~

Append one entry per call. Update `cumulative_usd` after each.

## Per-tool defaults

Pulled from each tool's `cost_per_call_usd` BaseTool attribute. Use the tool's value, NOT a hardcoded constant. The tool registry is the source of truth.

## Smoke test budget

- 4-page run: storyboard ($0.04) + 4 upscales × $0.24 = $1.00. Default budget $1.20.
- 16-page run: storyboard ($0.04) + 16 upscales × $0.24 = $3.88. Default budget $3.84 (per `config.yaml`).

## See also

- `config.yaml` — `defaults.budget_per_issue_usd`, `cost_warning_pct`, `cost_hard_stop_pct`
- `skills/meta/checkpoint-protocol.md` — gate paid calls on user approval
