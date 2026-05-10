# Providers

Backends currently implemented in v0.1, plus the v0.2 roadmap for additional providers.

## Image generation

| Mode | Backend | Provider | Used in stages | Cost |
|---|---|---|---|---|
| storyboard | `tools/image/codex_image_gen.py` | Codex CLI's `image_gen.imagegen` | 3 (storyboard) | varies by Codex plan |
| upscale_4k | `tools/image/vertex_gemini_image.py` | Vertex AI Gemini 3 Pro Image | 4 (upscale), 5 (cover/back) | $0.24 / 4K image |

Both providers are routed through `tools/image/image_selector.py`.

## Image processing

| Backend | Used in stage |
|---|---|
| `tools/image/pillow_split.py` (PIL) | 3 (split storyboard into cells) |

## PDF compose

| Backend | Provider | Used in stage |
|---|---|---|
| `tools/pdf/reportlab_compose.py` | ReportLab | 5 (compose) |

## Validation

| Backend | Purpose |
|---|---|
| `tools/validation/spec_validate.py` | issue-spec yaml + 5-layer reference resolution |
| `tools/validation/verify_4k.py` | post-upscale page image sanity (size, aspect) |
| `tools/validation/reference_photo_check.py` | reference photo long edge ≥ 1024 px |

## Meta

| Backend | Purpose |
|---|---|
| `tools/meta/scaffold_style.py` | placeholder (Tier 2 scaffold-style protocol lives in `skills/meta/scaffold-style.md`) |

## Roadmap

- **v0.2** — `image_selector` routes additional backends:
  - OpenAI `gpt-image-1` (alternative storyboard)
  - Imagen 4 (alternative 4K upscale)
- **v0.2** — `pdf_selector` with optional alternative compose backends (paginated EPUB, web preview)
- **v0.3+** — animation provider (Lottie / Remotion), TTS provider for narration
