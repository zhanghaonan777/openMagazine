# Design System Reference

Per-issue design decisions live in `library/design-systems/<slug>.yaml`.
This catalogue documents every field.

See [`docs/superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md`](superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md)
for the design rationale.

## File shape

| Field | Type | Owner |
|---|---|---|
| `schema_version` | const 1 | bump on breaking change |
| `slug` | string | issue id |
| `profile` | string | references `library/profiles/<name>.yaml` |
| `brand` | string | references `library/brands/<name>.yaml` |
| `inheritance` | object | which brand fields to inherit |
| `typography_resolution.<slot>.desired_family` | string | what we ask for |
| `typography_resolution.<slot>.fallback_chain` | list | walked at render time |
| `typography_resolution.<slot>.resolved_at_render` | string\|null | filled at compose stage |
| `text_safe_contracts.default_rule` | string | image-overlay negative-space rule |
| `text_safe_contracts.per_spread_overrides` | object | rare; usually empty |
| `brand_authenticity.do_not_generate` | list | image-gen prompts get these as negatives |
| `brand_authenticity.do_not_approximate` | list | same, with exact wordmarks |
| `brand_authenticity.asset_provenance_required` | list | regions that require user-supplied / verified assets |
| `layout_quality.min_gap_px` | int | for check_layout_quality.mjs |
| `layout_quality.max_text_image_overlap_px` | int | same |
| `layout_quality.max_text_text_overlap_px` | int | same |
| `output_targets` | list | which realizers to invoke at compose |
| `contact_sheet_rubric.distinct_layouts_required` | int | minimum unique layouts in deck |

## Lifecycle

1. **Auto-resolved at Stage 3 articulate** via `lib.design_system_loader.resolve_design_system()`
2. **Persisted to disk** at `library/design-systems/<slug>.yaml`
3. **Shown to user** at articulate checkpoint; user can edit yaml directly
4. **Validated** via `tools/validation/design_system_validate.py`
5. **Consumed** at Stage 6 compose by all realizers in `output_targets`

## Authoring

Most fields auto-derive; edit only when you want to:
- Add an `output_targets` entry (e.g. add `magazine-pptx` for an editable
  2:3 portrait magazine, or `deck-pptx` for a 16:9 derivative pitch deck)
- Tighten brand authenticity for a specific issue
- Override typography for one issue without changing brand.yaml
- Adjust `layout_quality` thresholds

## See also

- `library/profiles/<name>.yaml` — the profile being inherited
- `docs/profiles-reference.md` — profile catalogue
- `skills/meta/design-system-author.md` — drafting protocol for the agent
