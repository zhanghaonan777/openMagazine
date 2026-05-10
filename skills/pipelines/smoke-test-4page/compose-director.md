# compose-director — smoke-test-4page

## Purpose

Stage 5 of smoke-test-4page. Assemble the 4 4K page PNGs into a single
print-ready PDF at `output/<slug>/magazine.pdf`. The compose stage is
deterministic and free (no paid APIs); its main risks are missing input
files and PDF size out-of-band.

## Inputs

- `output/<slug>/upscale_result.json` — must list exactly 4 image paths.
- `output/<slug>/images/page-0{1..4}.png` — must all exist.

Validate before proceeding:
- All 4 PNGs resolve and are ≥ 5 MB (already enforced at upscale-director,
  but recheck here as a defensive guard).
- `upscale_result.json` validates against
  `schemas/artifacts/upscale_result.schema.json`.

## Read first (sub-skills)

Layer 2:
- `skills/core/reportlab.md` — `ReportlabCompose` API surface.

Layer 3:
- `.agents/skills/reportlab-typography.md` — page-size + bleed conventions
  (irrelevant to typography in this pipeline because everything is full
  bleed image, but the doc covers PDF page sizing pitfalls).

## Procedure

1. **Run the composer** — 4 portrait pages → 4 PDF pages, no spread merging:

   ~~~python
   from tools.pdf.reportlab_compose import ReportlabCompose
   import pathlib

   ReportlabCompose().run(
       issue_dir=pathlib.Path("output/<slug>"),
       spread_mode="split",
   )
   ~~~

   The composer reads `images/page-0{1..4}.png` in order and writes
   `magazine.pdf` to the issue dir.

2. **Write the artifact** — `output/<slug>/compose_result.json`, matching
   `schemas/artifacts/compose_result.schema.json`:

   ~~~json
   {
     "pdf_path": "output/<slug>/magazine.pdf",
     "page_count": 4,
     "image_count": 4,
     "size_mb": 18.4,
     "spec_slug": "<slug>"
   }
   ~~~

   (`size_mb` is computed via `pathlib.Path(pdf_path).stat().st_size / 1024 / 1024`.)

## Output artifact

`output/<slug>/compose_result.json` (above) plus `output/<slug>/magazine.pdf`.

## Checkpoint behavior

Default `checkpoint: off`. The PDF is shown to the user only at
publish-director time, alongside the contact sheet and verify report.

## Success criteria

- `magazine.pdf` exists and is 50-250 MB (4 × 4K full-bleed PNG embedded;
  ReportLab inflates beyond raw image size).
- `compose_result.json` validates against schema with `page_count == 4` and
  `image_count == 4`.

## Failure modes

- **Missing image at a `page-NN.png` path** → STOP. The upscale stage
  failed silently; bounce back to upscale-director and regenerate that
  single page (delete and rerun with `skip_existing=True`).
- **PDF size > 250 MB** → unusually large; likely a PNG was produced at
  oversized resolution. Re-run the composer with `spread_mode="split"`
  unchanged; if still >250 MB, downsample the offending PNG to 4K (4096px
  long edge) and recompose.
- **PDF size < 50 MB** → likely a near-empty PNG slipped through, or one
  or more pages are far below 4K. Inspect each `images/page-NN.png` for
  blank / corrupt / low-res content; regenerate the bad page.
