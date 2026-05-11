# Component Registry Reference

Every region with `role: text`, `text_decorative`, or `accent` must
reference a component listed in `library/components/registry.yaml`. This
is a **closed set** — directors and article-writers cannot invent
component names.

This mirrors the PPT skill's 22-locked-layout philosophy applied to
component primitives.

## Current components (v0.3.1)

| Component | Typography slot | Typical use |
|---|---|---|
| `Kicker` | `kicker` | Small uppercase label, mono font |
| `Title` | `display` | Large display headline |
| `Lead` | `body` italic | Intro paragraph |
| `Body` | `body` | Long-form running text |
| `BodyWithDropCap` | `body` + `drop_cap` | Body with raised-initial drop cap |
| `PullQuote` | `pull_quote` | Large inset quote |
| `Caption` | `caption` | Small italic image caption |
| `CaptionedThumbnail` | `caption` | Image + caption pair |
| `AccentRule` | — | Horizontal hairline in accent color |
| `Folio` | `page_number` | Page number + optional footer |
| `Masthead` | `display` | Brand masthead |
| `CoverLine` | `display` | Cover sub-headline |
| `TocList` | `body` | Table-of-contents list |
| `CreditsBlock` | `body` | Multi-line credits stack |
| `VerticalGradient` | — | Decorative top/bottom gradient overlay |

## Adding a new component

1. Add an entry to `library/components/registry.yaml`.
2. Add a rendering branch to `render_text_component` (or
   `render_accent`) in `library/layouts/_components/_macros/region.j2.html`.
3. Update this catalogue.
4. Run `tests/unit/test_regions_validate.py` to confirm the registry
   parses + the validator accepts the new name.
5. Run `tests/contracts/test_v2_pipelines.py` to confirm regions yamls
   that reference the new component validate.
