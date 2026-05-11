# Regions Reference

Every editorial spread is composed of **regions** — named, coordinate-
positioned bounding boxes that all three consumers (image gen, HTML
render, article copy validation) read from one file.

See [`docs/superpowers/specs/2026-05-11-regions-as-shared-contract-design.md`](superpowers/specs/2026-05-11-regions-as-shared-contract-design.md)
for the design rationale. This page is the catalogue.

## Where each spread's regions live

| Spread type | Regions file |
|---|---|
| `cover` | `library/layouts/_components/cover.regions.yaml` |
| `toc` | `library/layouts/_components/toc.regions.yaml` |
| `feature-spread` | `library/layouts/_components/feature-spread.regions.yaml` |
| `pull-quote` | `library/layouts/_components/pull-quote.regions.yaml` |
| `portrait-wall` | `library/layouts/_components/portrait-wall.regions.yaml` |
| `colophon` | `library/layouts/_components/colophon.regions.yaml` |
| `back-cover` | `library/layouts/_components/back-cover.regions.yaml` |

## Region shape

| Field | Type | Role |
|---|---|---|
| `id` | string | Stable identifier, used in CSS class + sidecar JSON |
| `rect_norm` | `[x1, y1, x2, y2]` in `[0,1]` | Bounding box relative to spread |
| `role` | enum | `image` / `image_grid` / `text` / `text_decorative` / `accent` / `negative_space` |
| `image_slot` | string | (image role) name from `layout.image_slots[*].id` |
| `image_slots` | list | (image_grid role) ordered list of slot names |
| `component` | string | (text/accent role) name from `library/components/registry.yaml` |
| `text_field` | string | (text role) field name from article `spread_copy` |
| `component_props` | object | per-component customization |
| `image_prompt_hint` | string | free text passed to the image gen prompt |
| `z_index` | int | stacking when regions overlap (default 0) |

## Adding a new spread type

1. Write `library/layouts/_components/<type>.regions.yaml`.
2. Run `python tools/validation/regions_validate.py library/layouts/_components/<type>.regions.yaml`.
3. Write `library/layouts/_components/<type>.html.j2` using the regions
   render macro (see `_macros/region.j2.html`).
4. Add a `{% elif sc.type == "<type>" %}` branch in `editorial-*.html.j2`.
5. Update this catalogue.
6. Run `tests/contracts/test_v2_pipelines.py` — the new yaml is auto-
   discovered and validated.
