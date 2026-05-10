# reference-photo-analyst

Infer subject traits from a reference photo (one-shot, before any generation).

## When to run

Stage 1 (research) when the user gave a photo but no `library/subjects/<name>.yaml`. The agent passes the photo path; this skill instructs the agent's vision-capable model to inspect the photo and produce a `subject` yaml stub.

## What to extract

For pets:
- species (cat / dog / etc)
- breed (best guess + confidence)
- coat color & pattern
- eye color
- distinctive markings
- body type (e.g., "lean", "stocky")
- estimated age range
- pose / mood in the reference

For people / objects: analogous fields (clothing, hair, expression, materials, etc).

## Output format

Write a candidate `library/subjects/<slug>.yaml`:

~~~yaml
schema_version: 1
name: <slug>
species: cat
reference_image: ../../examples/<example-folder>/refs/<photo-filename>
traits: |
  Tabby cat, charcoal gray with white chest blaze. Round amber eyes.
  Distinctive M-mark on forehead. Adult, ~4kg, lean build.
  Photo shows curious expression, ears slightly forward.
~~~

## Constraints

- ALWAYS include the photo's relative path in `reference_image`.
- traits string should be 3-5 sentences, declarative, no first-person.
- DO NOT invent details not visible in the photo. Confidence-flag uncertain attributes.

## See also

- `library/subjects/luna.yaml`, `library/subjects/naipi.yaml` for examples
- `skills/meta/creative-intake.md`
