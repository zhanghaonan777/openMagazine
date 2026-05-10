# shot-scale-variety

Page plans must vary shot scale and camera angle. Without this, every page
collapses to the same flat centered subject — validated failure mode in the
naigai-fauvist 4-page test (2026-05-10), where 4 same-scale centered-cat
cells were produced from a generic page plan.

## Author obligation

User input ("做一本 X 号 of <subject>") rarely specifies per-page composition.
The agent MUST design the page plan itself, **never reuse a generic plan**.
Every page in the plan MUST satisfy:

- **Each page** declares three things explicitly: shot scale + camera angle
  + subject screen-fraction.
  Examples:
  - "wide overhead, subject occupies bottom-third"
  - "low-angle hero, subject fills upper two-thirds"
  - "close-up profile, subject fills frame edge-to-edge"
  - "long-shot silhouette, subject occupies 1/8 of frame"
- **At least 4 distinct shot scales** appear across the issue
  (wide / medium / close-up / overhead).
- **No two adjacent pages** share the same shot scale.
- **page-01 (cover)** is hero / dramatic — low-angle or strong asymmetric
  composition. NEVER a flat centered subject.
- **page-NN (back cover, last page)** is quiet / coda — distant silhouette,
  overhead, or large negative space. NEVER mirror the cover composition.
- **Middle pages** follow the arc: opening (entering world) → exploration
  (mixed scales) → tension (one quiet/uncertain beat near 60% point) →
  climax (most spectacular pages, varied scales) → reflection → coda.

For 4-page mini tests, compress to: cover (hero) / action / quiet / back
(coda). The "no adjacent same scale" rule still applies.

## Embedding shot scale into scene strings

When writing per-cell scene strings inside the storyboard prompt, embed the
shot scale / angle directly into the scene text — don't leave it to the
model to guess. Example:

```
✗ "03 — kitchen scene"
✓ "03 — kitchen, low-angle close-up from floor level looking up at subject
        on counter, subject fills upper-third of frame, shallow DOF"
```

## See also

- `skills/creative/style-anchor-resolution.md` for the companion obligation
- `skills/creative/prompt-style-guide.md` for full prompt structure
- `skills/creative/typography-integrated.md` for cover composition rules
