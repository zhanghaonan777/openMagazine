# Articles

The `articles/` layer holds per-issue editorial copy: titles, kickers, leads, body paragraphs, pull quotes, captions, credits.

This layer is **new in schema v2**. v0.3 specs reference an article via the `article` field.

## Relationship to other layers

- `subjects/` — character traits (reusable across issues)
- `themes/` — visual world (lighting, palette, page_plan_hints; reusable)
- `articles/` — **per-issue copy** (this layer)
- `layouts/` — page geometry (image_slots, spread_plan; reusable)
- `brands/` — typography + print specs + visual tokens (reusable)
- `styles/` — image-gen prompt anchor (reusable)

A theme like `cosmos` can serve many issues (May 2026, June 2026, ...) — each gets its own `articles/<slug>.yaml`.

## Schema (v1)

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | always 1 (this is a new layer at v0.3, no migration) |
| `slug` | string | matches the spec's slug; usually identical |
| `display_title` | `{lang: string}` | human-readable title |
| `masthead_override` | string \| null | overrides brand.masthead for this issue |
| `issue_label` | `{lang: string}` | "ISSUE 03 / MAY 2026" |
| `cover_line` | `{lang: string}` | front-cover headline |
| `cover_kicker` | `{lang: string}` | "FEATURE STORY" / "VOL 03" / etc |
| `spread_copy` | list | one entry per layout.spread_plan item, by `idx` |

Each `spread_copy` entry MUST match the corresponding `layout.spread_plan[idx]` by `idx` and `type`.

## Auto-draft

If the spec references an `article` that doesn't exist on disk, or omits
`article` during research, the `articulate-director` skill drafts a complete
article and persists it to `library/articles/<slug>.yaml`. The user reviews
and edits the file before storyboard generation.

## Validation

Run `uv run python -m tools.validation.article_validate library/articles/<slug>.yaml --layout editorial-16page` to verify schema + cross-references.
