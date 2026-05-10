# Roadmap

## v0.1 (MVP — current)

- ✅ Single pipeline: `pipeline_defs/smoke-test-4page.yaml`
- ✅ 4 capability families: image_generation, image_processing, pdf_compose, validation, meta
- ✅ Single-provider backends per capability:
  - storyboard: Codex CLI `image_gen.imagegen`
  - upscale_4k: Vertex AI Gemini 3 Pro Image
  - pdf_compose: ReportLab
- ✅ Codex + Claude adapters; Cursor / Copilot stubs deferred
- ✅ 5-layer composition (subject × style × theme × layout × brand) + spec input + free-form input
- ✅ Schema-first artifacts (6 artifact + 1 pipeline schema)
- ✅ End-to-end smoke validated (see `docs/SMOKE_TEST.md`)

## v0.2 (Batch 2)

- Additional pipelines:
  - `editorial-magazine` (16 pages, full bleed)
  - `photo-monograph` (16 pages, no caption strips)
- Adapter docs: `CURSOR.md`, `COPILOT.md`
- Layer 3 expansion: ~12 docs (vs 6 in v0.1)
- Image selector v2: routes to OpenAI `gpt-image-1`, Imagen 4 as alternates
- `pdf_selector` implementation
- Cost tracker integration into stage directors (currently in `lib/cost_tracker.py` but not wired to all directors)

## v0.3+ (Future)

- Animated cover (Lottie / Remotion provider)
- Voice-over narration (TTS provider, generates `audio.mp3` alongside `magazine.pdf`)
- Web preview / pagination tools (HTML output target)
- Multi-issue subscription publication (RSS-feeded magazine series)
- Internationalization: per-issue language selector pulling from `subject.display_name.<lang>`, `theme.default_cover_line.<lang>`
