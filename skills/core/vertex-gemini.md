# vertex-gemini

`tools/image/vertex_gemini_image.py` — Vertex AI Gemini 3 Pro Image, 4K dual-ref upscaling.

## When to use

Stage 4 (upscale) and Stage 5 cover/back generation. Always 4K, always Vertex Gemini 3 Pro Image (no other model is supported in v0.1).

## How to use

~~~python
from tools.image.vertex_gemini_image import VertexGeminiImage

tool = VertexGeminiImage()
tool.run(
    prompt="...",  # full text prompt with placeholders already substituted
    out_path=pathlib.Path("output/<slug>/images/page-NN.png"),
    refs=[
        pathlib.Path("output/<slug>/cells/cell-NN.png"),       # FIRST: composition anchor
        pathlib.Path("output/<slug>/refs/protagonist-1.jpg"),  # SECOND: character anchor
    ],
    aspect="2:3",
    size="4K",
    skip_existing=True,
)
~~~

## Key constraints

- Cost: $0.24 per call (4K Gemini 3 Pro Image)
- Concurrency: ≤3 parallel calls (4+ → 503 storms; empirical from predecessor)
- File size sanity: success file should be 15-30 MB; <5 MB likely a failure
- Aspect: tested with 2:3 portrait

## Environment

- `OPEN_ZAZHI_GCP_PROJECT` overrides default project
- `OPEN_ZAZHI_PROXY` overrides default proxy ("none" disables)
- ADC required: `gcloud auth application-default login`

## See also

- Layer 3 doc: `.agents/skills/vertex-gemini-image-prompt-tips.md` — prompt construction patterns
- Configured in `config.yaml` under `vertex.model` and `vertex.location`
- Probe connectivity: `python -c "from tools.image.vertex_gemini_image import VertexGeminiImage; VertexGeminiImage().probe()"`
