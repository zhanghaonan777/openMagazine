# vertex-gemini-image-prompt-tips

Prompt construction for Vertex AI Gemini 3 Pro Image (`gemini-3-pro-image-preview`).

## Model metadata

- Endpoint: `gemini-3-pro-image-preview` @ `location=global` (do not change location)
- Cost: ~$0.24 per 4K image generation
- Aspect: 2:3 (portrait), 3:2 (landscape), 1:1 (square) — explicitly set in `image_config.aspect_ratio`
- Size: "4K", "1K" — explicitly set in `image_config.image_size`
- Reference images: passed via `Part.from_bytes(data=..., mime_type="image/png")` BEFORE the text prompt; first ref dominates composition.

## Prompt structure (3-block pattern)

1. **Style anchor** (1-2 sentences): photographer name + camera + film stock + "raw uncorrected, no LUTs"
2. **Scene description**: subject behavior, lighting, composition, shot scale
3. **Negative prompt** (compact): "no garbled typography, no plastic skin/fur, no AI-look, no illustration"

## Multi-reference (dual-ref)

When passing 2+ reference images:
- 1st ref: composition / layout anchor (e.g., a low-res storyboard cell)
- 2nd+ ref: character / subject anchor (real photo of the subject)

The model treats first ref as composition skeleton; subsequent refs anchor identity.

## Concurrency

≤3 concurrent calls in practice. 4+ → 503 UNAVAILABLE storms. Empirical, retry-with-exponential-backoff helps but does not eliminate.

## Failure modes

- Output <5 MB → likely a degraded generation; regenerate.
- Output >40 MB → unusual but not necessarily wrong; check aspect.
- Aspect drift (the model returns slightly different aspect than requested) — explicitly set `image_config.aspect_ratio` instead of relying on prompt text.

## Auth

- ADC required: `gcloud auth application-default login`
- Project must have Vertex AI API enabled.
- Set `vertexai=True` in `genai.Client(project=..., location="global")`.
