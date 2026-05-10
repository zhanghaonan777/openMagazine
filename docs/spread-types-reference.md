# Spread Types Reference

The 6 (technically 7, with cover + back-cover counted separately) spread types implemented in `editorial-16page`. Each is a Jinja2 component at `library/layouts/_components/<type>.html.j2` and consumes a corresponding article copy block.

Image slot ids on this page use the short form (no `spread-NN.` prefix); the storyboard / upscale pipeline composes the full id at runtime.

## cover

Single page (page 1). Full-bleed hero image with the brand masthead and cover line painted on top via WeasyPrint (NOT inside the photograph — that's the v0.1/v0.2 mode).

| | |
|---|---|
| **Pages** | 1 |
| **Image slots** | `cover_hero` (3:4 portrait, role: `cover_hero`) |
| **Article fields** | `article.cover_line`, `article.cover_kicker`, `article.issue_label`, optional `article.masthead_override` |
| **spread_copy entry** | `{idx: 1, type: cover, notes: ...}` — no required text fields (cover text is article-level) |
| **Typography** | Display family for masthead + cover line; kicker family for issue label |

## toc

Two-page spread (pages 2-3). Left page: section heading + brand masthead echo + decorative accent rule. Right page: contents list with page numbers.

| | |
|---|---|
| **Pages** | 2-3 |
| **Image slots** | none |
| **Article fields** | `spread_copy[1].table_of_contents` (list of `{page, en, zh}`) |
| **Typography** | Display family for the heading; kicker family for the page-number column |

## feature-spread

Two-page spread. Left page: full-bleed hero portrait. Right page: kicker + accent rule + title + lead + body (with drop cap on the first paragraph) + 3 captioned thumbnails in a 3-column row.

| | |
|---|---|
| **Pages** | 2-page (multiple instances per issue: spreads 3, 4, 6) |
| **Image slots** | `feature_hero` (3:4 portrait, role: `portrait`); `feature_captioned.1/2/3` (3:2 scenes, role: `scene`) |
| **Article fields** | `title`, `kicker`, `lead`, `body`, `image_slot_overrides` (per-slot scene descriptions) |
| **Typography** | Display family for title; kicker family for the chapter label; body family with drop cap on first paragraph; caption family italic for thumbnail captions |

## pull-quote

Two-page spread. Full-bleed environmental landscape darkened with a vertical gradient overlay. Quote + attribution centered, large pull-quote typography in the brand's accent color.

| | |
|---|---|
| **Pages** | 2-page (typically mid-issue, e.g. spread 5) |
| **Image slots** | `pullquote_environment` (16:10, role: `environment`) |
| **Article fields** | `quote`, `quote_attribution` |
| **Typography** | Pull-quote family at brand-defined size (typically 32pt italic display) |

## portrait-wall

Two-page spread. Title + accent rule top. 3×2 grid of 6 square portraits with short captions below each.

| | |
|---|---|
| **Pages** | 2-page (typically spread 7) |
| **Image slots** | `portrait_wall.1` … `portrait_wall.6` (1:1 square, role: `portrait`) |
| **Article fields** | `title`, `captions` (list of `{slot, en, zh}`, length 6) |
| **Typography** | Kicker family for the title; caption family italic for portrait captions |

## colophon

Two-page spread (typically spread 8). Two-column layout: left credits block (photographer / art direction / printing / copyright / contact), right copy or whitespace.

| | |
|---|---|
| **Pages** | 2-page |
| **Image slots** | none |
| **Article fields** | `credits` (object with `photographer`, `art_direction`, `printing`, `copyright`, `contact` — string or `{en, zh}` map per field) |
| **Typography** | Kicker family for "COLOPHON"; body family for the credits block |

## back-cover

Single page (last page). Full-bleed quiet coda image with optional closing quote in lower-third, painted onto the photo via WeasyPrint.

| | |
|---|---|
| **Pages** | 1 (last) |
| **Image slots** | `back_coda` (2:3 portrait, role: `back_coda`) |
| **Article fields** | `quote`, `quote_attribution` |
| **Typography** | Pull-quote family small italic in lower-third; bottom-page-number suppressed via `@page back-cover` rule in `_base.html.j2` |

---

## Adding a new spread type (v0.3.1+)

1. Create `library/layouts/_components/<type>.html.j2` (full-bleed div with `position: relative; height: var(--content-h);`).
2. Add `text_slots_required.<type>: [field, field, ...]` to your layout yaml.
3. Add an `image_slots` entry per slot (or reuse role-by-aspect from existing slots).
4. Add a `<type>` branch to `editorial-*.html.j2`'s `{% if sc.type == "..." %}` chain.
5. Update `spread_plan` in any layout that uses it.
6. Add a row to this reference page.
7. Run `tests/contracts/test_v2_pipelines.py` to confirm `article_validate` covers the new type.
