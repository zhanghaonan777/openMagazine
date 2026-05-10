# Typography Pack Cookbook

How to write `library/brands/<name>.yaml` for v2 editorial layouts.

## Quick start: clone a preset

```bash
cp library/brands/_presets/editorial-classic.yaml library/brands/my-magazine.yaml
# edit `name`, `masthead`, `display_name`; leave the rest unless you have
# a reason to customize
```

Two presets ship with v0.3:

| Preset | Display family | Body family | Vibe |
|---|---|---|---|
| `editorial-classic` | Playfair Display | Source Serif 4 | Generic editorial — didone display + transitional serif body. Safe default. |
| `humanist-warm` | Cormorant Garamond | Lora | Literary, slow-living. Slightly looser leading, warmer paper. |

Three more presets land in v0.3.1+ (`architectural`, `swiss-modernist`, `editorial-asian`).

## What lives in each section

A v2 brand has three blocks: `typography`, `print_specs`, `visual_tokens`. Plus the v1 metadata: `name`, `masthead`, `display_name`, `default_language`.

### `typography`

7 font slots, each with a `family` + slot-specific options:

| Slot | Purpose | Tunable fields |
|---|---|---|
| `display` | Big titles, masthead, cover line | `family`, `weights`, `source` |
| `body` | Long-form paragraphs | `family`, `weights`, `source`, `size_pt`, `leading`, `align`, `hyphenate` |
| `kicker` | Section labels, "CHAPTER 01" | `family`, `weight`, `transform: uppercase`, `letter_spacing`, `size_pt` |
| `caption` | Image captions, footnotes | `family`, `weight`, `style: italic`, `size_pt` |
| `pull_quote` | Big inset quotes | `family`, `weight`, `style`, `size_pt` |
| `drop_cap` | First letter of body | `enabled`, `family`, `weight`, `lines`, `color_token` |
| `page_number` | `@bottom-center` page numbers | `family`, `weight`, `size_pt` |

The `pairing_notes` field is a free-form 1-2 sentence note explaining the type pairing — surfaced in prompts via `{{TYPOGRAPHY_PAIRING_HINT}}`.

### `print_specs`

Page geometry. Defaults are A4 saddle-stitch with 18-22mm margins, 3mm bleed, 8mm gutter.

```yaml
print_specs:
  page_size: A4                # A4 | Letter | custom
  bleed_mm: 3
  trim_marks: true
  registration_marks: false
  binding: saddle-stitch       # saddle-stitch | perfect-bound | spiral
  binding_gutter_mm: 8
  margin_top_mm: 20
  margin_bottom_mm: 22
  margin_outer_mm: 18
  margin_inner_mm: 22
  baseline_grid_mm: 4
  paper_stock_note: "80gsm uncoated"
  color_mode: rgb              # rgb | cmyk (cmyk = v0.4+)
```

### `visual_tokens`

CSS custom properties. Paper color, ink colors, accent (drives accent rules + drop cap), quote-bg/fg, rule thickness.

```yaml
visual_tokens:
  color_bg_paper: "#f5efe6"          # warm cream
  color_ink_primary: "#1a1a1a"
  color_ink_secondary: "#6b6b6b"
  color_accent: "#c2272d"            # used for accent rules + drop cap
  color_quote_bg: "#1a1a1a"
  color_quote_fg: "#f5efe6"
  rule_thickness_pt: 1.5
  margin_note_indent_mm: 4
```

## Picking fonts

### Pairing principles

1. **Display + body should contrast in voice.** Display is loud; body is calm.
2. **Avoid two fonts of the same flavor.** Two slab serifs = mushy. One didone + one humanist = harmony.
3. **Use one family for meta.** Kicker + caption + page number all shipped on the same family (often a mono — IBM Plex Mono, JetBrains Mono) reads as intentional.

### Sources

| `source` | Pros | Cons |
|---|---|---|
| `google-fonts` | Free, ~1500 families, WeasyPrint resolves automatically via HTTP fetch | Needs internet at render time |
| `local` | Offline, deterministic, privacy-preserving. Drop TTF/OTF in `library/fonts/<family>/`, `_base.html.j2` emits `@font-face` | Must license commercially if shipping |
| `system` | Declare family name only; use the OS font cache | Brittle across deploy environments |

## Anti-AI-slop checklist

(Adapted from the `frontend-slides` STYLE_PRESETS reference.)

- ❌ Avoid Inter / Roboto / system fonts as `display`
- ❌ Avoid purple gradients on white
- ❌ Avoid generic "modern minimalist" (sans + thin weight + lots of whitespace)
- ✅ Pick distinctive choices: didone display, humanist body, mono meta
- ✅ Commit to one paper color (warm cream / cool gray / black) and one accent (red / oxblood / mustard)
- ✅ Use the kicker style as visual anchor — if removed, the spread should look broken

## Validation

`tools/validation/spec_validate.py` rejects `schema_version: 2` brands that lack `typography` / `print_specs` / `visual_tokens`. The auto-migration script handles v1 brands:

```bash
python tools/meta/migrate_brand_v1_to_v2.py library/brands/<name>.yaml --preset editorial-classic
```

See [`SCHEMA_V2_MIGRATION.md`](SCHEMA_V2_MIGRATION.md) for the full migration flow.
