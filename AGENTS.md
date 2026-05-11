# Codex adapter — openMagazine

**Runtime-gated compatibility.** Stage 3 (storyboard) requires a Codex
runtime that exposes the native `image_gen.imagegen` tool. Codex CLI is the
recommended runtime for production openMagazine runs.

## When you encounter a magazine request

1. Read `AGENT_GUIDE.md` (rule Zero).
2. Identify the pipeline — see `pipeline_defs/`.
3. **Run preflight to detect runtime:** check if `image_gen.imagegen` is callable.
4. If NOT available:
   - **STOP.** Do not attempt the pipeline.
   - Tell the user: "openMagazine requires Codex CLI for Stage 3 (storyboard generation). Please re-run this from a Codex CLI session, or use the predecessor `only_image_magazine_gen` skill which has a different pipeline."

## Rationale

The storyboard-first design is the core consistency anchor for openMagazine.
Falling back to alternative image generation tools (e.g., DALL-E 3 via OpenAI
API) is technically possible but breaks the "one inference locks the full
storyboard" guarantee and would require redesigning Stage 3 + Stage 4 dual-ref.
Out of scope for v0.3.
