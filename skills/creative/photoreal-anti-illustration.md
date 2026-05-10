# photoreal-anti-illustration

How to keep Vertex Gemini 3 Pro Image output as photo, not illustration.

## Failure mode

The model can drift toward illustration / poster / painting medium when:
- Style anchor names a painter (Matisse / Hopper / Klimt) without rewriting
- Prompt uses words like "illustration", "poster", "drawing"
- Negative prompt doesn't include illustration-medium phrases

## Recipe

1. **Style anchor MUST include**:
   - "photographed by [photographer name]"
   - "shot on [camera] with [lens]"
   - "[film stock] grain"
   - "raw uncorrected file, no LUTs"
   - One explicit "NOT a painting / NOT illustration / NOT poster" clause

2. **Always include in negative prompt**:
   - "cartoonish, plastic skin/fur, AI-looking"
   - "illustrative style, poster art, painted look"
   - "garbled typography, watermarks"

3. **For painter-derived styles** (e.g., Matisse / Hopper):
   - Rewrite to "<painter>-inspired set design / interior, photographed by..."
   - Treat the painter's vocabulary as scene props, NOT as rendering medium

## See also

- `skills/creative/style-anchor-resolution.md` for the 3-tier resolution flow
- `skills/creative/prompt-style-guide.md` for prompt structure
- `.agents/skills/photo-realism-prompts.md` (Layer 3) — generic photo-realism patterns
