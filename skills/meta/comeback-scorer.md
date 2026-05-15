# comeback-scorer

Post-render quality scoring borrowed from the Codex Presentations skill's Phase 5 (Comeback Rubric). Score the rendered magazine on 10 dimensions, surface profile-gate failures and blocking anti-patterns, and refuse to publish unless the gate passes. We absorb the DNA, not the surface area: this skill is image-led where Presentations is chart-led.

## When to invoke

Between `compose` and `publish` in any pipeline whose profile demands editorial finish — currently `pipelines/editorial-16page`. The publish stage director MUST refuse to ship until `output/<slug>/qa/scorecard.json` exists, schema-validates, and `gate_result.pass == true`. The numbers themselves come from this skill; the validation is mechanical (see `tools/validation/scorecard_validate.py`).

## The 10 dimensions

Each scored 0–5. See `schemas/artifacts/scorecard.schema.json#/properties/dimensions` for the canonical descriptions — these one-liners summarize what a `5` looks like.

- **story** — titles are claims (not topics); spread sequence has a real arc.
- **specificity** — would fail the noun-swap test; replace the subject and the issue stops working.
- **rhythm** — contact-sheet shapes vary; no three consecutive spreads share the same macro layout.
- **whitespace** — spreads breathe; boxed prose has visible top/bottom padding; nothing pinned to the edge.
- **image_clarity** — image-led equivalent of `chart_clarity`. Each image proves one thing; crops are intentional; subjects are sharp; identity assets have verified provenance.
- **typography** — type feels chosen, not defaulted; the design-system fallback chain is used deliberately.
- **restraint** — no filler boxes, badges, or decorative clutter; rounded cards never as default scaffolding.
- **precision** — metrics, dates, source notes, captions are exact. No invented facts.
- **coherence** — one visual system across all 9 spreads; margins/kicker/accent rule/page numbers consistent.
- **reference_delta** — visibly better than the supplied reference. Score `n/a` when no reference is supplied; do not claim reference-beating.

## Thresholds

- Total `>= 40 / 45` when no reference is supplied; `>= 44 / 50` when a reference is supplied.
- No dimension below `4`.
- No `profile_gates[i].result == "fail"`.
- No `anti_patterns_detected[i].severity == "block"`.

The validator recomputes all four checks from the raw data, so an agent cannot claim `pass=true` while the dimensions say otherwise.

## How to score

1. Open `output/<slug>/magazine.pdf` and (when present) `output/<slug>/magazine.html`.
2. Inspect TWICE: thumbnail / contact-sheet scale (rhythm, coherence, restraint), then full size (image_clarity, typography, precision, whitespace).
3. For every dimension, write a concrete `evidence` string. Cite spread `idx` (e.g. "spread 3 cover crop loses the subject's eyes"). No vague praise.
4. For any dimension below 5, also write `what_would_make_it_5`.
5. Pull `profile_gates` from `library/profiles/<profile>.yaml.hard_gates` — every rule there becomes an entry with `pass | fail | n/a` and evidence.
6. Walk the anti-patterns catalogue below; record each one actually seen with spread idx and severity.

## Anti-patterns catalogue

Adapted from the Presentations skill's "Blocking Anti-Patterns" section, ported for an image-led editorial pipeline. Use these stable kebab-case keys verbatim in `anti_patterns_detected[i].pattern`:

- `title-states-topic-not-conclusion`
- `multiple-dominant-evidence-objects`
- `image-does-not-prove-the-claim`
- `proof-object-too-thin-for-claim`
- `label-detached-from-its-subject`
- `marker-or-glyph-overlaps-readable-copy`
- `value-lost-to-insufficient-contrast`
- `equal-role-boxes-misaligned-or-inconsistently-padded`
- `box-system-implies-grouping-content-does-not-support`
- `visible-containers-louder-than-content`
- `rounded-cards-as-default`
- `three-spreads-in-a-row-share-composition`
- `contact-sheet-reads-as-template-pack`
- `contact-sheet-clean-but-weak-information-architecture`
- `body-copy-only-fills-space`
- `boxed-prose-pinned-to-edge-without-breathing-room`
- `kicker-icon-and-label-not-optically-centered`
- `typography-falls-back-to-default-without-intent`
- `footer-or-page-marker-changes-style`
- `low-resolution-or-rough-image-crop`
- `stock-photo-feel-on-primary-subject`
- `fabricated-official-logo-or-mascot-or-app-icon`
- `unprovenanced-partner-or-customer-logo`
- `brand-like-icon-used-only-to-fill-whitespace`
- `unsupported-metric-or-vague-source-label`
- `output-only-matches-reference-not-beats-it`

Severity `block` fails the gate even if the numeric rubric passes. Use `warn` when the pattern is present but localized to one spread and the rest of the issue carries the claim.

## Iteration rule

If the gate fails, do NOT cosmetic-nudge. Name the weakest 2–4 spreads in `iteration_targets[i]` with `spread_idx`, `reason`, and `weakest_dimension`, regenerate those spreads (back to the appropriate upstream stage — usually `compose` or `storyboard`), and rescore. Prefer a bold rebuild of a weak spread over patching it. Cap iterations at 3; on the 3rd failed scorecard, STOP and report the remaining weak spots to the user honestly. Do not call the issue done because a PDF exists.

## Output

Write `output/<slug>/qa/scorecard.json` matching `schemas/artifacts/scorecard.schema.json`. The publish-stage `reviewer` skill runs `tools.validation.scorecard_validate.validate_scorecard` against it; any returned errors are a hard stop.

## See also

- `schemas/artifacts/scorecard.schema.json` — canonical shape
- `tools/validation/scorecard_validate.py` — mechanical recompute + anti-spoof check
- `skills/meta/reviewer.md` — generic per-stage validator that calls this one
- `skills/meta/checkpoint-protocol.md` — how the failed gate surfaces to the user
- `library/profiles/<name>.yaml.hard_gates` — source for `scorecard.profile_gates`
