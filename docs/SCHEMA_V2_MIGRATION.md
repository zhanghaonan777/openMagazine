# Schema v1 → v2 Migration

v0.3 introduces `schema_version: 2` for `spec`, `brand`, and `layout` files. v0.1 / v0.2 `schema_version: 1` files keep working — both are supported in parallel via `tools/pdf/pdf_selector.py`.

## When to migrate

Migrate when you want any of:
- Editorial layouts (real PDF text, multi-image spreads).
- Named typography packs (Playfair / Source Serif / IBM Plex Mono).
- CSS Paged Media features (bleed, gutters, page numbers, drop caps, accent rules).

If you're happy with `plain-4` / `plain-16` (one 4K image per page, typography painted into the photograph), don't migrate — v1 still works.

## What changes

### spec yaml

Schema v2 adds an editorial `article` reference for final production. Draft
specs may omit it during research; the `articulate` stage then creates the
article yaml and the agent persists the reference before storyboard.

```diff
-schema_version: 1
+schema_version: 2
 slug: cosmos-luna-may-2026
 subject: luna
 style: kinfolk
 theme: cosmos
-layout: plain-16
+layout: editorial-16page
 brand: meow-life
+article: cosmos-luna-may-2026  # editorial article reference
 overrides: {}
```

`article` references `library/articles/<slug>.yaml`. The articulate stage drafts it if the spec does not already resolve to an existing article.

### brand yaml

Run the auto-migration script:

```bash
uv run python -m tools.meta.migrate_brand_v1_to_v2 \
  library/brands/<name>.yaml \
  --preset editorial-classic
```

This adds `typography`, `print_specs`, `visual_tokens` from the chosen preset (`editorial-classic` or `humanist-warm`) while preserving existing `name`, `masthead`, `display_name`. Replace the `{{MASTHEAD}}` placeholder if it appears.

### layout yaml

v2 layouts have a different shape (`spread_plan`, `image_slots` with `role` + `aspect`, `text_slots_required`). The simplest path is to use the shipped `editorial-16page` instead of migrating a v1 layout — they describe fundamentally different things.

If you need a custom v2 layout:
1. Copy `library/layouts/editorial-16page.yaml` → `library/layouts/<your-name>.yaml`.
2. Adjust `spread_plan` (must sum to total `page_count`).
3. Adjust `image_slots` (each entry needs `id`, `role`, `aspect`, `min_long_edge_px`, `spread_idx`).
4. Adjust `text_slots_required` per spread type (must match `library/articles/*.yaml` field names actually written by `skills/meta/article-writer.md`).
5. Copy + adjust `library/layouts/editorial-16page.html.j2`.
6. Add a row to `docs/spread-types-reference.md`.

### article yaml (NEW)

An editorial production run should end with a spec that references an article. Two options:

- **Write by hand** — see `library/articles/cosmos-luna-may-2026.yaml` as template.
- **Let the agent draft it** — set `article: <slug>` in spec; the `articulate` stage drafts copy from research_brief + layout's `text_slots_required`. User reviews + edits at the articulate checkpoint before storyboard.

## Pipeline routing

| Spec | Pipeline manifest | Compose engine |
|---|---|---|
| `schema_version: 1`, `layout: plain-4` | `pipeline_defs/smoke-test-4page.yaml` | ReportlabCompose |
| `schema_version: 2`, `layout: editorial-16page` | `pipeline_defs/editorial-16page.yaml` | WeasyprintCompose (via PdfSelector) |

`tools/validation/spec_validate.py` reads `spec.layout`'s schema_version and routes to the correct codepath. Director skills declare "dispatch pdf_compose" — `tools/pdf/pdf_selector.choose_backend()` picks the engine based on the resolved layout.

## Coexistence

Tests cover both paths:
- v1: `tests/unit/test_pillow_split.py`, `tests/unit/test_reportlab_compose.py`, the smoke-test-4page contract test.
- v2: `tests/integration/test_render_dry_run.py` (full WeasyPrint render with placeholder PNGs), `tests/contracts/test_v2_pipelines.py`.

Both test buckets run on every change; CI fails if either path regresses.
