# overlay-safe-layout

Design image prompts and HTML/PDF overlays from the same page-level layout
contract so text, cards, rules, and decorative lines do not cover the subject.

## When to use

Use whenever a page will receive HTML/PDF overlay components after image
generation: evidence cards, captions, pinboards, folios, title bands,
telemetry rails, quote strips, product labels, or decorative connector lines.

## Contract shape

Add optional `page_overlay_contracts` to the theme yaml or issue-local theme:

~~~yaml
page_overlay_contracts:
  - page: 3
    subject_zone: right-center
    protected_zones:
      - {name: face, rect: [0.52, 0.14, 0.92, 0.58]}
    reserved_overlay_zones: [left-rail, bottom-strip]
    negative_space: ["left 32%", "bottom 18%"]
    html_components: [EvidenceRail, BottomPinboard, Folio]
    forbidden: [cards-over-face, cross-face-lines]
    image_prompt_notes: "Keep the left rail dark and calm; keep bottom calm."
~~~

`rect` values are normalized `[x1, y1, x2, y2]` coordinates.

## Rules

1. Proposal decides the contract before paid generation.
2. Storyboard prompt includes the contract so composition starts with the
   right protected zones and reserved overlay zones.
3. Upscale prompts repeat the page's contract with explicit instructions:
   protected zones must stay clear; reserved overlay zones must stay calm.
4. HTML/PDF compose must place components only in reserved overlay zones.
5. Decorative lines may connect cards inside an overlay zone, but must never
   cross the subject's face, eyes, primary product, or hero prop.
6. Render and inspect the final PDF. If a component overlaps a protected zone,
   reflow the HTML; do not regenerate the image unless the prompt contract was
   missing or ignored.

## Safe Slots

Prefer named slots over ad hoc absolute positioning:

- `left-rail`
- `right-rail`
- `top-band`
- `bottom-strip`
- `bottom-left`
- `bottom-right`
- `negative-space-block`

## Failure Mode

If a page looks good as an image but overlays cover the face, the prompt was
underspecified or compose ignored the contract. Fix the contract first, then
adjust the HTML components to stay inside safe slots.
