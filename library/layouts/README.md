# Layouts Library

Each `<name>.yaml` defines the **page count + aspect + storyboard grid +
typography mode** for an issue. Storyboard grid rows×cols must equal page
count.

Shipped seeds:

| File | Pages | Grid | Use case |
|---|---|---|---|
| `plain-16.yaml` | 16 | 4×4 | full-issue simple mode (default) |
| `plain-4.yaml` | 4 | 2×2 | smoke test (~$0.96, ~10 min) |

Adding a new layout: copy a seed, change `page_count` + `storyboard_grid`
to match (e.g., `8x1=8`, `3x4=12`). The split-storyboard helper accepts
arbitrary `--rows --cols`, so any factorization works.

`typography_mode`:
- `full-bleed` — cover/back masthead+colophon integrated INTO photo (no
  separate footer bar). This is the current default after the cover
  full-bleed fix (commit a0550ff).
- `footer-bar` — legacy: cover/back have a separate cream footer strip
  with VOL/DATE/barcode. Retained for nostalgia; not recommended.

See `templates/SCHEMA.md` for the full schema.
