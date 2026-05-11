# library/components/

Closed registry of every visual component a region can name. Adding a
new component is a small explicit PR — directors can't invent component
names. This mirrors the PPT skill's 22-locked-layouts philosophy applied
to component primitives.

See `registry.yaml` for the canonical list; `../layouts/_components/*.j2`
for how each is rendered; `docs/component-registry-reference.md` for
prose docs.

## Adding a new component

1. Add an entry to `registry.yaml` with `description`, `typography_slot`,
   `accepts_props`.
2. Add a corresponding rendering rule to the `render_component` macro
   (see `library/layouts/_components/_macros/region.j2.html`).
3. Update `docs/component-registry-reference.md`.
4. Run `tests/contracts/test_v2_pipelines.py` to confirm validation still
   passes.
