# style-anchor-resolution

The agent MUST normalize any user-supplied style input through a 3-tier
resolution before substituting `{{STYLE_ANCHOR}}` into prompts. Tier 1 is
preferred (data-driven, fast, predictable); Tier 2 lands new data; Tier 3
is degraded fallback only.

This obligation comes from the naigai-fauvist 4-page test (2026-05-10): a
"Matisse-style cat magazine" input produced illustration-style 4K output
instead of editorial photography because the style anchor was passed
through unrewritten.

## 3-tier flow

```
              user style input
                    │
                    ▼
   ┌──────────────────────────────────────────┐
   │ TIER 1 — lookup templates/styles/*.yaml  │
   │   substring match against trigger_keywords│
   │   matched → use yaml's style_anchor      │
   │           verbatim. DONE.                 │
   └──────────────────┬───────────────────────┘
                      │ no match
                      ▼
   ┌──────────────────────────────────────────┐
   │ TIER 2 — scaffold-style meta-protocol     │
   │   references/scaffold-style.md            │
   │     S0 type → S1 web search 5-8           │
   │     → S2 synthesize yaml → S3 validate    │
   │     → S4 user-approve → S5 land file      │
   │   Result: new templates/styles/<name>.yaml│
   │   then re-enter TIER 1 (will hit now).    │
   └──────────────────┬───────────────────────┘
                      │ scaffold skipped or impossible
                      ▼
   ┌──────────────────────────────────────────┐
   │ TIER 3 — inline 3-class rewrite (fallback)│
   │   A class — painter/movement/illustration │
   │   B class — magazine/photographer (expand)│
   │   C class — abstract mood (augment)       │
   │   Result NOT persisted to library.        │
   └──────────────────────────────────────────┘
```

## Tier 1 — library lookup (default path)

Pseudocode for the agent to follow:

```python
import yaml, pathlib

user_style = "<the user-supplied style anchor or theme phrase>"
matched = None
for ypath in sorted(pathlib.Path("templates/styles").glob("*.yaml")):
    if ypath.name == "README.md":
        continue
    style = yaml.safe_load(ypath.read_text())
    for kw in style["trigger_keywords"]:
        if kw.lower() in user_style.lower():
            matched = style
            break
    if matched:
        break

if matched:
    # use matched["style_anchor"] verbatim as {{STYLE_ANCHOR}}
    ...
```

Tier 1 hit means the agent is DONE with normalization — the matched yaml
already has the photo-medium-enforced `style_anchor`. No further rewriting.

## Tier 2 — scaffold meta-protocol

If Tier 1 misses, follow `references/scaffold-style.md` step-by-step:
S0 (decide type) → S1 (web research) → S2 (synthesize yaml) → S3 (validate)
→ S4 (user approve) → S5 (land file). Then re-enter Tier 1 (will hit now).

The scaffold is an **investment** — once landed, the new style is reusable
for all future issues. Don't skip Tier 2 unless time-constrained.

## Tier 3 — inline rewrite (degraded fallback)

Use ONLY when Tier 2 isn't viable (offline, fast iteration, user preference
to skip scaffold). The rewritten string is NOT persisted; same input next
time will go through normalization again.

### 3-class logic for tier 3

**Class A — painter / movement / illustration / animation reference**
(Trigger: painter names, movement words, drawing-medium words, anime/pixar.)
Apply photo-medium rewrite — see "Class A rewrite" below.

**Class B — magazine / photographer / photo-movement reference**
(Trigger: NatGeo, Vogue, Kinfolk, Time, Avedon, Leiter, "street photography".)
Apply photo-anchor expansion — see "Class B expansion" below.

**Class C — mood / adjective / atmosphere**
(Trigger: dreamy, vintage, melancholy, ethereal, gritty.)
Apply mood augmentation — see "Class C augmentation" below.

When the user-supplied input is plain enough to enforce photo medium
without rewriting (e.g., already says "shot on Leica with Portra"), pass
through with light camera/film augmentation only.

### Tier 3 trigger words by class

| Class | Trigger examples |
|---|---|
| **A**  painter / movement / illustration / animation | Matisse / Hopper / Klimt / Van Gogh / Monet / Hokusai / Mucha / Picasso / O'Keeffe / fauvism / impressionism / cubism / pop art / ukiyo-e / art nouveau / surrealism / illustration / 插画 / poster / 海报 / cartoon / 卡通 / oil painting / 油画 / watercolor / 水彩 / line art / 线描 / anime / pixar / studio ghibli / disney |
| **B**  magazine / photographer / photo-movement | National Geographic / Vogue / Vogue Italia / Kinfolk / Time / The New Yorker / i-D / Wallpaper / Apartamento / Annie Leibovitz / Saul Leiter / Steve McCurry / Nan Goldin / William Eggleston / Hiroshi Sugimoto / "street photography" / "new topographics" |
| **C**  abstract mood / adjective | dreamy / 梦幻 / vintage / 复古 / melancholy / ethereal / gritty / cinematic / cozy / 温暖 / 安静 / nostalgic |

### Class A — painter / movement → photo-rewrite template

```
"<original-style>-inspired interior / set design,
 photographed by <photographer> for <magazine>;
 <original-style> shows up as: color palette / set props / lighting
 language / fabric and surface treatment — NOT as drawing or painting
 medium.
 Shot on <camera> with <lens>, <film stock> grain, raw uncorrected file,
 no LUTs, editorial photojournalism finish.
 NOT a painting, NOT illustration; a photograph of a <style>-styled
 interior / scene."
```

Worked example — user input *"马蒂斯风格的奶盖猫猫杂志"*:

```
✗ Raw style anchor (NEVER use directly):
  "Matisse fauvism style, bold flat color blocks, simplified contours"

✓ Rewritten style anchor (what actually goes into prompts):
  "Matisse-fauvism-inspired interior, photographed by Annie Leibovitz for
  Vogue Italia. Matisse fauvism shows up as: bold flat color blocks as
  set-design walls, simplified contour lines as natural lighting edges,
  decorative pattern in textiles — NOT as drawing or painting medium.
  Shot on Sony Alpha 7R V with Sigma 35mm f/1.4, Kodak Portra 400 grain,
  raw uncorrected file, no LUTs, editorial photojournalism finish.
  NOT a painting; a photograph of a Matisse-styled interior."
```

### Class B — magazine / photographer → photo-anchor expansion template

```
"<magazine-or-photographer-name> <core characteristics — grain + lighting +
 composition discipline + camera tradition>;
 shot on <matching camera> + <matching lens> + <matching film stock>,
 raw uncorrected file, no LUTs, editorial photojournalism finish."
```

Worked example — user input *"国家地理风格的奶盖号"*:

```
✗ Raw style anchor (way too sparse):
  "National Geographic style"

✓ Expanded style anchor:
  "National Geographic photojournalism. Hand-held documentary feel,
  authentic environmental context, single ambient sun as primary light, no
  fill, no rim. Slight ISO 400 grain, deep blacks, muted desaturated
  palette except for one anchored saturated accent. Natural fur / skin
  texture visible. Shot on Leica M11 with Summicron 50mm f/2, Tri-X 400
  grain, raw uncorrected file, no LUTs, no post-processing."
```

### Class C — abstract mood → photo-augmentation template

```
"<original-mood> editorial photography.
 <lighting characterization — direction + hardness + temperature>,
 <atmospheric details — haze / grain / bokeh quality>;
 shot on <matching camera> + <matching lens> + <matching film stock>,
 raw uncorrected file, no aggressive LUT."
```

Worked example — user input *"梦幻温暖的奶盖号"*:

```
✗ Raw style anchor:
  "dreamy warm"

✓ Augmented style anchor:
  "Dreamy warm editorial photography. Golden-hour low-side light, sun one
  hour before sunset — long warm shadows, amber rim on window-side
  surfaces. Slight atmospheric haze (dust, pollen) catching the light;
  painterly bokeh from wide aperture; warm-tone roll-off in highlights
  WITHOUT teal-orange LUT. Shot on Leica M11 with Summicron 50mm f/2,
  Kodak Portra 400 grain, raw uncorrected file, no aggressive LUT."
```

### Photographer + magazine reference pool (for Tier 3 class A and B)

| User-style cue | Photographer | Magazine vibe |
|---|---|---|
| Bold color / fauvism / pop art | Annie Leibovitz / Tim Walker | Vogue Italia |
| Quiet domestic / Hopper / minimalism | Saul Leiter / William Eggleston | Kinfolk |
| Cultural / exotic / period | Steve McCurry / Sebastião Salgado | National Geographic |
| Intimate / private / casual | Nan Goldin / Wolfgang Tillmans | i-D |
| Dramatic / fashion / surreal | Steven Meisel / Tim Walker | Vogue / W |
| Architectural / formal / quiet | Hiroshi Sugimoto / Candida Höfer | Apartamento |

### Camera + film pool (for all 3 tier-3 classes)

- Sony Alpha 7R V + Sigma 35mm f/1.4 + Kodak Portra 400 — natural realism
- Leica M11 + Summicron 50mm + Tri-X 400 — documentary, slight warmth
- Hasselblad H6D-100c + 80mm f/2.8 — formal, large-format detail
- Canon EOS R5 + RF 35mm f/1.8 — neutral editorial
- Mamiya 7 II + 80mm f/4 + Fujifilm Pro 400H — calm medium-format film
- iPhone 15 / 16 Pro — candid, anti-cinematic-AI-gloss

Apply the 3-tier resolution BEFORE substituting `{{STYLE_ANCHOR}}` into any
prompt. The resolved string is what becomes verbatim across all 16 prompts.

## When this conflicts with user intent

If the user *explicitly* says "I want a Matisse-painted picture book, not a
photo magazine" — that's outside this skill's scope (see `## Scope` in
SKILL.md: "Out: animated / illustrated / picture-book"). Redirect to a
different tool. Don't bend simple mode toward illustration.

## See also

- `skills/creative/shot-scale-variety.md` for the companion obligation
- `skills/creative/photoreal-anti-illustration.md` for medium-drift recipe
- `skills/creative/prompt-style-guide.md` for full prompt structure
- `references/scaffold-style.md` for the Tier 2 meta-protocol
