# typography-integrated

For cover and back-cover full-bleed pages, typography (masthead, cover line,
optional quote) must be **integrated INTO the photograph** — painted on
real surfaces in the scene, printed onto fabric banners, or rendered as if
hand-lettered onto a wall. Never as a separate footer bar overlaying the
photo, never as a clip-art barcode strip, never as a horizontal solid-color
band cutting across the bottom of the image.

The cover should read as a full-bleed editorial photograph, not a
photo-plus-UI-footer composite.

## Cover (page-01) typography rules

```
Typography (rendered as if hand-painted / printed lettering integrated
INTO the photograph itself, NOT as a separate footer bar overlaying the
photo, NOT a clip-art-style barcode strip):
- Masthead at top: "{{MAGAZINE_NAME}}" extra-large serif, all caps,
  dominant; treat as a true title block painted onto the wall surface
  or printed into a real banner element of the scene.
- Cover line stacked lower-left: "{{COVER_LINE}}" — large serif, all
  caps, 2-3 stacked lines maximum, integrated against the actual
  photo background (e.g., painted on the same wall as the masthead, or
  printed onto a fabric banner in the scene).
- NO bottom-strip footer bar with VOL/DATE numerals. NO barcode. NO
  ISSN. NO PDF-mockup-like horizontal band cutting across the bottom
  of the image. The cover should feel a full-bleed editorial
  photograph, not a photo-plus-UI-footer composite.
```

### Cover negative-prompt additions

```
lorem ipsum, gibberish letterforms, garbled type, broken serifs, watermarks,
logos that aren't the masthead, AI-looking type, footer bar / footer strip
/ horizontal band of solid color across the bottom of the image, barcode,
ISSN, version numerals, date strip, "VOL." text.
```

## Back cover (last page) typography rules

The back cover is a quiet coda. Most of the time, NO typography is the
right choice — full-bleed quiet coda photo is the goal.

```
Typography (rendered as if hand-painted / printed lettering integrated
INTO the photograph itself, NOT as a separate footer bar):
- Optional lower-third: a single short quote in small italic serif, 1-2
  lines, painted onto a wall surface or fabric in the scene. If
  photographically awkward to integrate, prefer NO typography at all
  on the back cover — full-bleed quiet coda photo is the goal.
- NO masthead. NO cover line. NO bottom-strip footer bar with VOL/DATE
  numerals. NO barcode. NO ISSN. NO horizontal solid-color band across
  the bottom. NO colophon footer band.
```

### Back-cover-specific negation

The back-cover storyboard cell often has "16" or "back" page-number markers
that leak into 4K output if not explicitly negated (validated failure mode
in naigai-fauvist 4-page test, 2026-05-10: page-04 retained the cell-04
top-left "04" marker). Always include in the negative prompt:

```
no visible page numbers, no cell labels, no annotation overlays, no
scratch tracing of storyboard guides.
```

## Why integrated, not overlaid

Editorial covers from Vogue / Kinfolk / National Geographic do place
masthead text as a flat overlay — but those are produced in InDesign as a
post-processing step on a clean photograph. When the image generator is
asked to render BOTH the photo AND the chrome in one pass, the chrome
collapses into low-quality clip-art (garbled barcode, fake ISSN, broken
footer band).

By instructing the model to treat type as a real object in the scene
(painted on a wall, printed on a banner, lettered onto signage), the type
becomes part of the photograph's content — properly lit, shadowed, and
integrated. This is what high-end editorial photography actually does
when masthead text is part of the shot.

## See also

- `skills/creative/prompt-style-guide.md` for full prompt structure
- `skills/creative/photoreal-anti-illustration.md` for medium-drift recipe
- `skills/creative/shot-scale-variety.md` for cover composition rules
