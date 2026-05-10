# photo-realism-prompts

Avoiding the AI-illustration look in image-generation pipelines.

## The drift problem

Image models trained on diverse internet data drift toward illustration / poster / painting medium when:
- Style anchor names a painter (Matisse, Hopper, Klimt) without rewriting
- Prompt uses words like "illustration", "poster", "drawing"
- Negative prompt doesn't include illustration-medium phrases

## Anti-drift recipe

### 1. Style anchor MUST include camera + film

Bad:
> "Matisse-inspired interior, vibrant colors, bold shapes"

Good:
> "Matisse-inspired set design / interior, photographed by Tim Walker, shot on Pentax 67 with Kodak Ektachrome, raw uncorrected, no LUTs. Treats Matisse vocabulary as physical scene props, NOT rendering medium."

### 2. Always include in negative prompt

- `cartoonish, plastic skin/fur, AI-looking`
- `illustrative style, poster art, painted look`
- `garbled typography, watermarks`

### 3. For painter-derived styles

Treat the painter as a set designer, not a renderer:
- "Hopper-inspired diner interior at dusk, photographed by ..." — Hopper sets the scene; the photographer captures it.
- "Hokusai-inspired wave crest, photographed by Hiroshi Sugimoto, raw uncorrected, no LUTs" — Hokusai is the visual reference; Sugimoto is the medium.

### 4. Specify film stock for color cast

- Kodak Portra 800 → warm skin tones, slight cyan shadows
- Fujifilm Provia 100 → neutral, crisp
- Cinestill 800T → tungsten-balanced, halated highlights
- Kodak Ektachrome → vibrant blues / saturated reds
- Ilford HP5 → black-and-white, gritty grain

### 5. Light and grain language

- "directional natural daylight from window-left, soft falloff"
- "tungsten practicals plus bounce, shadow detail preserved"
- "fine 35mm grain, no digital noise reduction"
- "skin pores visible, subsurface scattering"

These cues push the output toward photographic medium.
