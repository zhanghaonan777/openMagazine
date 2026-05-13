# library/design-systems/

Per-issue resolved design decisions. One yaml per issue slug,
auto-persisted at the articulate checkpoint (Stage 3 of
editorial-16page pipeline) but committable / editable.

Each design-system carries:
- the chosen `profile` (e.g. `consumer-retail`)
- per-slot typography resolution chains (desired family + fallbacks)
- text-safe contract rules
- brand authenticity gates (which generations are forbidden)
- layout quality thresholds
- output targets (which realizers to invoke at compose stage)

This file is parallel to `library/articles/<slug>.yaml`: same per-issue
granularity, both auto-drafted at Stage 3 articulate.

## Authoring

Most users never edit these by hand — they're written by
`lib.design_system_loader.resolve_design_system()` at articulate time.
But editing them is fully supported: any field you set here overrides
the auto-derivation.

## Validation

```bash
python tools/validation/design_system_validate.py \
  library/design-systems/<slug>.yaml
```
