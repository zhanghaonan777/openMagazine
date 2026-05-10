# Brands Library

Each `<name>.yaml` is one **publication brand** — the masthead text,
website URL, and editorial persona. Used to fill `{{MAGAZINE_NAME}}`
and (via persona) inform cover-line tone.

Shipped seeds:

| File | Brand | Use case |
|---|---|---|
| `meow-life.yaml` | MEOW LIFE / 主子号 | classic cat magazine (cosmos / shanghai-1930s themes) |
| `naipi-mag.yaml` | NAIPI / 奶啤号 | dog-focused magazine (burberry-uk theme) |

Adding a new brand: copy a seed, edit `masthead` + `display_name` +
`persona`. URL is optional and unused in current full-bleed typography
mode (was a footer-bar artifact).

See `templates/SCHEMA.md` for the schema.
