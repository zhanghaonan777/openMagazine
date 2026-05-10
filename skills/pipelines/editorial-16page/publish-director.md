# publish-director — editorial-16page

## Purpose

Stage 7 (final) of editorial-16page. Verify the 21 4K page outputs,
generate a contact-sheet thumbnail, optionally auto-persist a reusable
issue spec yaml (only if the run was free-form), and write the closing
`publish_report.json` artifact that the user receives as the run summary.

## Inputs

- `output/<slug>/compose_result.json` (and transitively all upstream
  artifacts: research_brief, proposal, article, storyboard,
  upscale_result).
- `output/<slug>/magazine.pdf`, `magazine.html`.
- `output/<slug>/images/spread-NN/<slot>.png` × 21.
- `output/<slug>/costs.json` (cumulative cost ledger from
  `cost-budget-enforcer`).

Validate before proceeding:
- All prior artifacts validate against their schemas.
- `magazine.pdf` exists.

## Read first (sub-skills)

No new sub-skills required. This stage uses already-imported tools:
- `tools/validation/verify_4k.py` — `Verify4K().run(issue_dir)`.
- `tools/image/pillow_split.py` — for combining via PIL (or use raw PIL
  directly).

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

2. **Contact sheet** — 4×6 grid of the 21 4K page images thumbnailed to
   ~240×240 each. Write to `output/<slug>/contact_sheet.jpg`:

   ~~~python
   from PIL import Image
   import itertools

   tw, th, gutter = 240, 240, 16
   cols, rows = 6, 4
   W = cols * tw + (cols + 1) * gutter
   H = rows * th + (rows + 1) * gutter
   sheet = Image.new("RGB", (W, H), "white")

   image_paths = sorted((issue_dir / "images").rglob("*.png"))[:21]
   for idx, p in enumerate(image_paths):
       r, c = divmod(idx, cols)
       thumb = Image.open(p)
       thumb.thumbnail((tw, th))
       x = gutter + c * (tw + gutter) + (tw - thumb.width) // 2
       y = gutter + r * (th + gutter) + (th - thumb.height) // 2
       sheet.paste(thumb, (x, y))
   sheet.save(issue_dir / "contact_sheet.jpg", quality=88)
   ~~~

3. **Auto-persist spec** (free-form runs only) — if the run started
   from a free-form user message (no input
   `library/issue-specs/<slug>.yaml`), synthesize one now from
   `research_brief.json` + `proposal.json` + the resolved
   `article` reference, and write it to
   `library/issue-specs/<slug>.yaml`. Capture the path for the report.
   If the run started from an existing spec, set
   `auto_persisted_spec_path: null`.

4. **Compute final stats** — read `output/<slug>/costs.json` for
   `total_cost_usd`; subtract pipeline start time (recorded in
   research_brief or a dedicated start file) for `wall_time_min`.

5. **Write artifact** — `output/<slug>/publish_report.json` matches
   `schemas/artifacts/publish_report.schema.json`:

   ~~~json
   {
     "spec_slug": "<slug>",
     "pdf_path": "output/<slug>/magazine.pdf",
     "html_path": "output/<slug>/magazine.html",
     "contact_sheet_path": "output/<slug>/contact_sheet.jpg",
     "page_count": 16,
     "image_count": 21,
     "total_cost_usd": 5.04,
     "wall_time_min": 14.3,
     "auto_persisted_spec_path": null,
     "schema_version": 2
   }
   ~~~

## Output artifact

`output/<slug>/publish_report.json` plus `contact_sheet.jpg` and
(optionally) `library/issue-specs/<slug>.yaml`.

## Checkpoint behavior

`checkpoint: off`. The publish stage hands the report to the user as the
run's final message — no approval gate, since at this point all spending
has already happened.

## Success criteria

- `Verify4K().run(issue_dir)` returns 0.
- `contact_sheet.jpg` exists; size between 100 KB and 5 MB.
- `publish_report.json` validates against schema.
- If free-form run: `library/issue-specs/<slug>.yaml` exists and parses.

## Failure modes

- **`verify_4k` returns non-zero** → STOP. Inspect the report to
  identify the offending page (resolution / aspect / file-size). Fix
  that page in upscale-director (delete + regenerate with
  `skip_existing=True`), then recompose, then rerun publish.
- **Contact sheet save fails** → likely a PNG is corrupt; same fix as
  above.
- **Auto-persist spec yaml fails schema** → log the failure into
  `publish_report.auto_persisted_spec_path: null` but do NOT block the
  report; the user still gets the magazine PDF.
