# Brands Library

Each `<name>.yaml` is one **publication brand**. v1 brands provide masthead
and persona for image-prompt typography; v2 editorial brands also provide
typography packs, print specs, and visual tokens for WeasyPrint.

Shipped seeds:

| File | Brand | Use case |
|---|---|---|
| `meow-life.yaml` | MEOW LIFE / 主子号 | classic cat magazine (cosmos / shanghai-1930s themes) |
| `naipi-mag.yaml` | NAIPI / 奶啤号 | dog-focused magazine (burberry-uk theme) |

Adding a new brand: copy a seed, edit `masthead` + `display_name` +
`persona`. URL is optional and unused in current full-bleed typography
mode (was a footer-bar artifact).

See `library/SCHEMA.md` for the schema.
