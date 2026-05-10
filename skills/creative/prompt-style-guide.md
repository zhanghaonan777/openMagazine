# Prompt Style Guide

How to write prompts that produce magazine-grade photoreal output from Gemini 3 Pro Image. This is the playbook distilled from production iterations — not a generic best-practices doc.

## The Three-Block Structure

Every prompt has exactly three blocks. Same order every time.

```
1. SUBJECT       — who, what they look like, how they behave
2. SCENE + LIGHT — where, what's happening, how it's lit, camera
3. NEGATIVE      — what NOT to render
```

Anything else (`Mood:`, `Style:`, etc.) is optional and goes inside block 2.

---

## Block 1 — Subject

### Lead with real-proportion language

Gemini's training data is heavy on "cute British Shorthair" memes. Default output is anime-eyed, plush, glossy. **The first defense is to tell the model the subject is a real animal:**

```
Subject: Luna, a healthy adult British Shorthair cat. Real cat proportions —
realistic eye-to-face ratio, real cat body geometry, normal-sized pupils.
```

Words like `real`, `normal`, `realistic` are anti-cute signals. Use them up front.

### Identity: 5-8 specific traits, repeated verbatim across all pages

Vague descriptions drift. Over-specified descriptions hold. One concrete example:

> *"silver-golden coat with beige-gray tabby markings on forehead and back, round face, clear bright eyes, upright ears, white tuft on the chin, slightly chubby build, age roughly four years."*

Each detail is one more anchor vector. Copy-paste this string verbatim into every page's prompt — never paraphrase.

### Behavior verbs: alert, exploring, observing

Use active, healthy verbs for a magazine-quality subject:

✅ alert, curious, exploring, observing, walking, attentive, watching
❌ tired, lived-in, worn, sad, mournful, droopy, weary, sick

The "matte / lived-in" angle goes too far → mournful "sick cat" output. Stay on the alert/curious side and rely on Block 2 lighting + Block 3 negatives to kill the gloss.

---

## Block 2 — Scene, Lighting, Camera

### Scene: action verb + 3-4 specifics + spatial layout

Verbs produce reportage; nouns produce postcards.

❌ "A cat in a deep-sea environment with bioluminescent jellyfish."
✅ "Luna swims past a cluster of bioluminescent jellyfish at 600m depth.
   The blue-green glow lights the right side of her face. Bubbles trail
   from her whiskers."

Spell out where things are: "Earth visible upper-right horizon", "long shadow stretching to lower-right". Concrete spatial cues remove ambiguity.

### Lighting: direction + hardness + color, in that order

```
Single hard sun from front-left. No fill, no rim light. Sky pure black with
crisp pinhole stars. Long sharp shadow stretches to the lower-right.
```

- **Direction** ("front-left") drives composition
- **Hardness** ("hard sun" / "soft diffused") drives mood
- **No rim light** is the single most reliable anti-AI-plastic trick — rim light is what creates oily edge highlights

### Camera: specific equipment, not adjectives

Gemini reads EXIF-style camera specs as a denser signal than "cinematic":

```
Camera: shot on Sony Alpha 7R V with Sigma 35mm f/1.4 Art lens.
ISO 200, 1/500s shutter. Raw uncorrected file, no color grading,
no LUTs, no post-processing.
```

The specific bodies that work well in production:
- **Sony Alpha 7R V + Sigma 35mm Art** — natural realism, mild contrast
- **Leica M11 + Summicron 50mm** — documentary, slight warmth
- **Canon EOS R5 + RF 35mm f/1.8** — neutral editorial
- **iPhone 15 Pro / 16 Pro** — candid feel, kills "cinematic AI gloss" by association

The "Raw uncorrected" + "no LUTs" line is critical — Gemini will otherwise auto-apply a teal-orange grade that screams AI.

---

## Block 3 — Negative Prompt

End every prompt with one consolidated `Negative prompt:` line. The model's compliance with negatives is high — use the slot.

The default negative for our magazine work:

```
Negative prompt: cartoonish, AI-looking, plastic fur, over-smoothed, glossy
CGI rendering, anime cute, oversized eyes, perfect grooming, beauty-filter
aesthetic, plush show-cat appearance, 3D render look, oily highlights, rim
lighting, painted whiskers, mournful expression, droopy eyes, sad/sick face,
extra limbs, deformed paws, garbled typography.
```

Tune by domain:
- **Cosmos / sci-fi** — add `cluttered HUD, fictional spacecraft, garbled astronaut helmet logos`
- **1930s / period Shanghai** — add `modern logos, smartphones, plastic items, anachronistic clothing, simplified Chinese characters, modern Pudong skyline`
- **Deep sea** — add `surface light artifacts, scuba gear that floats, freshwater lighting`

---

## Words to Drop From Old Templates

These were standard in GPT-Image-2 era prompts but **actively hurt** Gemini 3 Pro output. Remove from your default style anchor:

| Word | Why it hurts |
|---|---|
| `plush` | Encodes show-cat fluffiness → cartoon look |
| `glossy` | Pushes toward oily fur |
| `crisp catchlights` | Makes eyes look CGI-perfect |
| `Dense plush fur` | Same as plush |
| `sharp highlights along the rim` | Direct request for oily edge light |
| `macro-level detail` | Pushes hyperreal / over-rendered |
| `tack-sharp` | Same |
| `8K, ultra-detailed, premium` | Generic "AI render" cue, not editorial |
| `cinematic color grading` | Triggers teal-orange LUT default |

## Words to Keep / Add

| Word | What it does |
|---|---|
| `matte fur, no specular highlights` | Kills oily fur |
| `single ambient sun`, `no fill, no rim light` | Kills studio lighting |
| `natural fur sheen with subtle outdoor reflectance` | Allows healthy look without gloss |
| `Raw uncorrected file, no color grading, no LUTs` | Stops auto-grading |
| `documentary realism, hand-held feel` | Loosens stiffness |
| `real cat proportions, normal-sized pupils` | Counters anime defaults |
| `well-kept but not show-groomed` | The "alive but not pageant" middle |

---

## Style Anchors (Reusable Strings)

Anchors are 1-3 sentences attached to every page in an issue. Pick one per issue and **copy verbatim** into every prompt.

### Vogue Italia / High Fashion
```
High-end editorial photography in the Vogue Italia tradition. Calm desaturated
palette, dramatic single-source lighting, Steven Meisel composition discipline.
Fabric textures and skin micro-shadows visible. No retouching gloss.
```

### National Geographic / Documentary
```
National Geographic photojournalism. Hand-held feel, single ambient sun,
authentic environmental context, slight ISO 400 grain, deep blacks. Realistic
fur and skin texture, no atmospheric softening on the subject.
```

### Kinfolk / Quiet Lifestyle
```
Kinfolk magazine aesthetic. Diffused window light, muted palette of warm
neutrals, shallow but honest depth of field, gentle film grain. Composed but
unposed — subject doing something quiet with hands or paws.
```

### Time Magazine / Annie Leibovitz Portrait
```
Time magazine cover style — Annie Leibovitz tradition. Single dramatic key
light, deep shadow side, subject occupies upper two-thirds of frame, neutral
backdrop. Serious, weighty, slight contrast push. No glamor lighting.
```

### Wes Anderson / Symmetric
```
Wes Anderson editorial — strict symmetry, centered subject, pastel accent on
neutral wall, flat front-on perspective. Mid-format film grain. Single soft
overhead source. Composed, deadpan mood.
```

---

## Reference Image Behavior

Gemini 3 Pro Image obeys references with this priority hierarchy:

```
Reference image > Prompt text — for: composition, character identity,
                                      lighting style, sharpness/grain
Prompt text > Reference image — for: scene/environment, action, mood
```

### Implications

1. **Use the cover (4K, sharp, hero-lit) as the reference for all subsequent pages.** Pages will inherit the cover's character + lighting + grade for free, and the prompt drives the new scene.

2. **Don't use a low-res storyboard cell as a 4K reference.** The output inherits the cell's softness. Confirmed in production: 360×240 cell → 4K output reads soft.

3. **Skip references for the first hero shot.** Pure prompt gives the model maximum room to render at top quality. Then use that hero as the anchor.

4. **One reference is usually enough.** The system supports up to 14, but adding more rarely helps and increases inference time. Use 2-3 only when locking multiple distinct elements (e.g. main character + style reference + product to insert).

---

## Worked Example

A complete production prompt for Issue #001 P5 (Luna on the lunar surface):

```
A cinematic editorial photograph for a magazine spread.

Subject: Luna, a healthy adult British Shorthair cat. Real cat proportions —
realistic eye-to-face ratio, real cat body geometry, normal-sized pupils.
Silver-golden tabby coat with beige-gray markings on forehead and back, round
face, clear bright eyes, upright ears, slightly chubby build. Alert and
exploring. Matte fur with no specular highlights, no oily sheen, no rim light.
Whiskers natural and translucent.

Scene: Luna walks across the dusty lunar regolith, leaving a clear trail of
small paw prints behind her. Earth visible as a small blue marble on the
upper-right horizon. A few moon rocks scatter the foreground.

Lighting: Single hard sun from front-left lighting her face and chest cleanly.
No fill, no rim light. Sky pure black with crisp pinhole stars. Long sharp
shadow stretches to the lower-right.

Camera: Sony Alpha 7R V with Sigma 35mm f/1.4 Art lens. ISO 200, 1/500s.
Raw uncorrected file, no color grading, no LUTs, no post-processing.

Mood: calm, curious, real. The cat is exploring, not posing.

Style: National Geographic photojournalism. Hand-held feel, slight ISO 400
grain, deep blacks. Documentary realism.

Negative prompt: cartoonish, AI-looking, plastic fur, over-smoothed, glossy
CGI rendering, anime cute, oversized eyes, perfect grooming, beauty-filter
aesthetic, plush show-cat appearance, 3D render look, oily highlights, rim
lighting, painted whiskers, mournful expression, droopy eyes, sad/sick face.
```

Result: 5056×3392 4K, character recognizable, hard light + shadow rendered, footprint trail visible, no anime eyes, no oil. Generation time ~95s, cost $0.24.

---

## Iteration Discipline

When a prompt fails, change **one block at a time**:

1. **Subject feels wrong** (off-character, wrong proportions) → adjust Block 1 only
2. **Scene wrong / lighting off** → adjust Block 2 only
3. **Still has AI plastic feel** → adjust Block 3 negatives + check Block 2 hasn't reintroduced rim light

Don't rewrite the whole prompt at every retry. You'll never know which change moved the result.

The full iteration log for the lunar walk scene (5 versions) is preserved in the project skill output history if you need a worked example of this discipline in action.
