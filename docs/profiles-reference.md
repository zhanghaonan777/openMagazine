# Profiles Reference

Closed registry of publication types. Pick one per design-system.

See [`docs/superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md`](superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md)
for rationale.

## Profiles shipped in v0.3.2

| Profile | When to use | File |
|---|---|---|
| `consumer-retail` | animal / person / product / lookbook / lifestyle / editorial | `library/profiles/consumer-retail.yaml` |

## Future profiles (v0.3.3+)

| Profile | When to use |
|---|---|
| `finance-ir` | earnings / investor reviews / financial analysis |
| `product-platform` | SaaS / product narratives |
| `gtm-growth` | growth / marketing / cohort stories |
| `engineering-platform` | developer / AI / infrastructure |
| `strategy-leadership` | investor-day / board / strategy |
| `appendix-heavy` | tables / disclosures |

Each future profile follows the same shape: extract structural rules
from Codex Presentations skill's `profiles/<name>.md` into yaml.

## Profile fields

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | const 1 | |
| `name` | string | lowercase-kebab |
| `display_name.{en,zh}` | string | shown to users |
| `presentations_profile` | enum | maps to Codex Presentations profile |
| `hard_gates` | list | rules realizers must respect |
| `required_proof_objects` | list | every spread must include one |
| `visual_preferences` | object | aesthetic hints, not enforced |
| `banned_motifs` | list | image-prompt negatives |
| `spread_types_required` / `spread_types_optional` | list | layout constraints |

## Adding a new profile

See [`library/profiles/README.md`](../library/profiles/README.md).
