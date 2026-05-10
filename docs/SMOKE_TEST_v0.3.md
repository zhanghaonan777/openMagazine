# Smoke Test v0.3 — `cosmos-luna-may-2026` (editorial-16page)

This is a runbook for the first live `editorial-16page` end-to-end run.
Filled in once a real Codex CLI session has produced the artifacts.

## Status

⏳ Pending live run from a Codex CLI session. (v0.3 implementation
landed; live run requires `image_gen.imagegen` which only Codex CLI
provides.)

## Steps to run

### 0. One-time setup

WeasyPrint native deps (macOS):

```bash
brew install weasyprint
```

Vertex AI ADC + project config:

```bash
gcloud auth application-default login
gcloud config set project <your-gcp-project-id>
```

Local probe:

```bash
cd ~/github/openMagazine && source .venv/bin/activate
make probe
```

### 1. Verify the dry-run renders (no Vertex spend)

```bash
python -m pytest tests/integration/test_render_dry_run.py -v
```

This builds a placeholder-PNG version of the full 16-page PDF using
WeasyPrint. If it fails, fix `_components/*.j2` or `_base.html.j2`
before spending real money on Vertex calls.

### 2. (One-time) Author the spec yaml

If `library/issue-specs/cosmos-luna-may-2026.yaml` doesn't yet exist,
either write it by hand referencing the 6 layers, or let the agent
generate it from a free-form one-liner ("做一本太空号 of Luna").

### 3. In a fresh Codex CLI session, paste

```
Run the editorial-16page pipeline with
library/issue-specs/cosmos-luna-may-2026.yaml as the spec input.
Stop at the articulate gate so I can review the article copy, then again
at the storyboard gate.
```

### 4. Approve articulate gate

After the agent drafts `library/articles/cosmos-luna-may-2026.yaml`,
review:
- All 9 spreads have all `text_slots_required` fields.
- Voice is editorial / restrained (no AI fillers).
- `image_slot_overrides` are slot-specific (not generic).

Edit the yaml in place if needed. Re-run `article_validate`:

```bash
python tools/validation/article_validate.py \
  library/articles/cosmos-luna-may-2026.yaml \
  --layout editorial-16page
```

Approve the gate.

### 5. Approve storyboard gate

After ~4 min, the agent produces `output/cosmos-luna-may-2026/storyboard.png`
(1024×1536, 6×4 grid) and 21 cell PNGs at
`output/cosmos-luna-may-2026/cells/spread-NN/<slot>.png`.

Review:
- Outer aspect is 2:3 portrait (no aspect-warning fired by `pillow_split`).
- Same character recognizable across all 21 cells.
- Style is photographic, not illustration.
- Cells with `role: cover_hero` / `back_coda` have the right framing.

Approve. (Or regenerate if off-style. Don't try to salvage individual cells.)

### 6. Wait for upscale

21 Vertex calls at parallelism 3 → ~7 batches × ~1.5 min ≈ 10 min.

### 7. Inspect outputs

```
output/cosmos-luna-may-2026/
├── refs/protagonist-1.jpg
├── research_brief.json
├── proposal.json
├── article.json
├── storyboard.png                   # 1024×1536
├── storyboard.json
├── cells/spread-NN/<slot>.png × 21
├── images/spread-NN/<slot>.png × 21 # each 5–30 MB
├── upscale_result.json
├── magazine.pdf                     # 16 pages, 30–150 MB
├── magazine.html                    # intermediate; useful for debugging
├── compose_result.json
├── contact_sheet.jpg                # 4×6 grid of 21 thumbnails on 1600×1200
└── publish_report.json
```

Open `magazine.pdf` in any viewer; check page count, drop caps, accent
rules, page numbers visible at bottom-center, captions readable.

## Expected results

- Page count: **16**
- Image slots rendered: **21 / 21**
- All schemas valid: ✓ (verify_4k returns 0)
- Editorial spreads render correctly: feature spreads have hero + 3
  thumbnails + body text with drop cap; pull-quote has full-bleed env +
  large quote in accent color; portrait wall has 6 captioned squares.

## Result

(Fill in after the first live run.)

| | |
|---|---|
| Date | |
| Pipeline | `editorial-16page` |
| Spec | `cosmos-luna-may-2026` |
| Total cost | $ |
| Wall time | ___ min |
| Page count | ☐ 16 |
| Image slots | ☐ 21 / 21 |
| All schemas valid | ☐ |
| Editorial spreads render correctly | ☐ |
| Drop caps + accent rules + page numbers visible | ☐ |
| Cover masthead readable, no garbled type | ☐ |

## Issues encountered

(Fill in after the live run. Use commit hashes for any fixes.)

- … 

## Notes for v0.3.1+

(Fill in after the live run. Things the smoke test exposed that
deserve a follow-up.)

- …
