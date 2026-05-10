# publish-director — smoke-test-4page

## Purpose

Stage 6 (final) of smoke-test-4page. Verify the 4K page outputs, generate a
2×2 contact sheet thumbnail, optionally auto-persist a reusable issue spec
yaml (only if the run was free-form), and write the closing
`publish_report.json` artifact that the user receives as the run summary.

## Inputs

- `output/<slug>/compose.json` (and transitively all prior artifacts:
  research_brief, proposal, storyboard, upscale).
- `output/<slug>/magazine.pdf`.
- `output/<slug>/images/page-0{1..4}.png`.

Validate before proceeding:
- All prior artifacts validate against their schemas.
- `magazine.pdf` exists.

## Read first (sub-skills)

No new sub-skills required. This stage uses already-imported tools:
- `tools/validation/verify_4k.py` — `Verify4K().run(issue_dir)`.
- `tools/image/pillow_split.py` — for combining via PIL (or use raw PIL).

## Procedure

1. **Verify 4K** — must return 0 (= all pages pass resolution + aspect
   checks):

   ~~~python
   from tools.validation.verify_4k import Verify4K
   import pathlib

   issue_dir = pathlib.Path("output/<slug>")
   rc = Verify4K().run(issue_dir)
   assert rc == 0, f"verify_4k failed with rc={rc}"
   ~~~

2. **Contact sheet** — 2×2 grid of the 4 pages thumbnailed to ~1024 px
   long edge. Write to `output/<slug>/contact_sheet.jpg`:

   ~~~python
   from PIL import Image
   thumbs = [Image.open(issue_dir / f"images/page-{i:02d}.png") for i in range(1, 5)]
   tw, th = 512, 768  # each thumb 2:3
   for t in thumbs:
       t.thumbnail((tw, th))
   sheet = Image.new("RGB", (tw * 2, th * 2), "white")
   for idx, t in enumerate(thumbs):
       r, c = divmod(idx, 2)
       sheet.paste(t, (c * tw, r * th))
   sheet.save(issue_dir / "contact_sheet.jpg", quality=88)
   ~~~

3. **Auto-persist spec** (free-form runs only) — if the run started from a
   free-form user message (i.e. there was no input
   `library/issue-specs/<slug>.yaml`), synthesize one now from
   `research_brief.json` + `proposal.json` and write it to
   `library/issue-specs/<slug>.yaml`. Capture the path for the report.
   If the run started from an existing spec, set
   `auto_persisted_spec_path: null`.

4. **Write the artifact** — `output/<slug>/publish_report.json`, matching
   `schemas/artifacts/publish_report.schema.json`:

   ~~~json
   {
     "pdf_path": "output/<slug>/magazine.pdf",
     "contact_sheet_path": "output/<slug>/contact_sheet.jpg",
     "total_cost_usd": 1.00,
     "wall_time_min": 11.5,
     "auto_persisted_spec_path": "library/issue-specs/<slug>.yaml",
     "spec_slug": "<slug>"
   }
   ~~~

## Output artifact

`output/<slug>/publish_report.json` (above) plus
`output/<slug>/contact_sheet.jpg` and (optionally)
`library/issue-specs/<slug>.yaml`.

## Checkpoint behavior

Default `checkpoint: off`. The publish stage hands the report to the user
as the run's final message — no approval gate, since at this point all
spending has already happened.

## Success criteria

- `Verify4K().run(issue_dir)` returns 0.
- `contact_sheet.jpg` exists and is 100 KB – 5 MB.
- `publish_report.json` validates against schema.
- If free-form run: `library/issue-specs/<slug>.yaml` exists and parses.

## Failure modes

- **`verify_4k` returns non-zero** → STOP. Inspect the report to identify
  the offending page (resolution / aspect / file-size). Fix that page in
  upscale-director (delete + regenerate with `skip_existing=True`), then
  recompose, then rerun publish.
- **Contact sheet save fails** → likely a PNG is corrupt; same fix as
  above.
- **Auto-persist spec yaml fails schema** → log the failure into
  `publish_report.auto_persisted_spec_path: null` but do NOT block the
  report; the user still gets the magazine PDF.
