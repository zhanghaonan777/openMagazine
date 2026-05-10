# Smoke test — naipi-burberry-spec-test-01

This is a placeholder. Fill in after running the live smoke test (see `docs/superpowers/plans/2026-05-10-openmagazine-from-scratch.md` Task 25 in the predecessor `only_image_magazine_gen` repo).

## Status

⏳ Pending live run from Codex CLI session.

## Steps to run

1. **Symlink** (one-time):
   ~~~bash
   ln -sfn ~/github/openMagazine ~/.codex/skills/openmagazine
   ~~~

2. **Verify ADC + probe** (one-time):
   ~~~bash
   gcloud auth application-default login
   cd ~/github/openMagazine
   source .venv/bin/activate
   make probe
   ~~~

3. **In a fresh Codex session, paste**:
   ~~~
   Run the smoke-test-4page pipeline using
   library/issue-specs/naipi-burberry-spec-test-01.yaml as the spec input.
   Stop at the storyboard gate and show me the storyboard + cells.
   ~~~

4. **Approve the storyboard gate** when the agent presents it.

5. **Wait** for upscale (4 × $0.24 ≈ 5 minutes), compose, publish.

## Expected output

After completion, `output/naipi-burberry-spec-test-01/` should contain:

- `refs/protagonist-1.jpg` (carried over from the spec)
- `research_brief.json`
- `proposal.json`
- `storyboard.png` + `cells/cell-01.png` … `cell-04.png`
- `prompts/page-NN.txt` (4 files)
- `images/page-01.png` … `page-04.png` (each 5–30 MB)
- `checkpoints/storyboard-<ts>.json` (with `decision: approved`)
- `cost.json` (cumulative ≤ $1.10)
- `magazine.pdf` (4 pages, ≥ 50 MB)
- `contact_sheet.jpg`
- `publish_report.json` (schema-valid)

## Verification

~~~bash
ls output/naipi-burberry-spec-test-01/
python tools/validation/verify_4k.py output/naipi-burberry-spec-test-01
~~~

## Result

(Fill in after run)

- Date:
- 6 stages completed: ☐
- Cost: $
- Wall time: ___ minutes
- All schemas validated: ☐
- Storyboard gate fired and was approved: ☐
- magazine.pdf: ___ pages, ___ MB

## Issues encountered

(Fill in after run)
