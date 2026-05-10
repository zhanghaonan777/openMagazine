# creative-intake

Parse free-form user input into spec parameters (subject + style + theme + page count).

## When to run

Stage 1 (research) when the user gave a one-liner like "make a 16-page magazine of my dog in cosmos style". Skip if user provided a spec yaml path.

## Extract these fields

| Field | How to extract | Default if missing |
|---|---|---|
| subject | named entity (pet name, person name, product) | ASK user |
| species/category | "cat" / "dog" / "person" / "place" / etc | infer from photo or ASK |
| style | adjective phrase or named style ("cosmos", "burberry") | photoreal default |
| theme | thematic angle implicit in the request | infer from style |
| page count | "16-page" / "4-page" mentions | 16 (full) or 4 (smoke test) |
| reference photo | attached or path provided | ASK |

## Resolution flow

1. **Style anchor**: try `styles/<name>.yaml` lookup first (Tier 1). If miss, scaffold via `skills/meta/scaffold-style.md` (Tier 2). Tier 3 inline only if scaffold fails.
2. **Subject card**: try `library/subjects/<name>.yaml`. If miss, derive traits from the reference photo via `skills/meta/reference-photo-analyst.md`.
3. **Theme**: try `library/themes/<name>.yaml`. If miss, infer a 16-page narrative arc from the subject + style.
4. **Layout**: default `plain-16` (or `plain-4` for smoke test).
5. **Brand**: default `meow-life` for cats, generic otherwise.

## Auto-persist

After Stage 3 (storyboard) approval, write `library/issue-specs/<slug>.yaml` so the run is reproducible from spec input.

## See also

- `library/SCHEMA.md` — 5-layer composition
- `skills/meta/reference-photo-analyst.md`
- `skills/meta/scaffold-style.md`
