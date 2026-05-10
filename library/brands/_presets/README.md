# Brand Presets

Starting points for `library/brands/<name>.yaml` (schema_version 2).

| Preset | Display family | Body family | Vibe |
|---|---|---|---|
| editorial-classic | Playfair Display | Source Serif 4 | Generic editorial / human-interest |
| humanist-warm | Cormorant Garamond | Lora | Literature / lifestyle |

## Use

```bash
cp library/brands/_presets/editorial-classic.yaml library/brands/my-magazine.yaml
# Edit name, masthead, default_language; leave typography / print_specs / tokens alone unless you know what you're doing
```

The `{{MASTHEAD}}` placeholder must be replaced before the brand is referenced from a spec. `spec_validate` will reject a brand whose masthead still contains literal `{{...}}`.

## Future presets (v0.3.1+)

- architectural — Archivo Black + Manrope (design / business)
- swiss-modernist — Inter Display + Inter (tech / product)
- editorial-asian — Noto Serif CJK + Source Han Sans (Chinese-language)
