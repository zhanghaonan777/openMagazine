# Scaffold Style Protocol

How to generate a new `templates/styles/<name>.yaml` from scratch when the
user requests a style not yet shipped.

**When this fires:** Simple-mode Phase 0 takes the user's style anchor →
substring-matches against `trigger_keywords` in `templates/styles/*.yaml`
→ no match → trigger this protocol → produce yaml → continue Phase 0 with
the new yaml's `style_anchor`.

**Why it exists:** The shipped style library is intentionally small (8
seeds: 3 magazines, 2 moods, 3 painter/movement). Writing a high-quality
style anchor is ~15 minutes of careful research-anchored work. Scaffolding
lets us extend the library on demand without that becoming the user's
burden — the agent does the research and writing, the user reviews.

**Output:** One new yaml in `templates/styles/`, validated, persistent
(reusable for future issues).

This protocol mirrors the design pattern of an "agent web-searches +
synthesizes a yaml + user approves" meta-capability — the library grows
through use rather than being hand-curated upfront.

---

## Step S0 — Determine `type`

Before researching, decide which type the user input falls into:

| User input pattern | `type` | `needs_rewrite` |
|---|---|---|
| Painter name (Klimt, Van Gogh, O'Keeffe…) | `painter` | true |
| Painting movement (cubism, art-nouveau, surrealism…) | `movement` | true |
| Drawing medium (illustration, watercolor, ink…) | `movement` | true |
| Animation reference (anime, ghibli, pixar…) | `movement` | true |
| Magazine name (Time, i-D, Wallpaper, Apartamento…) | `magazine` | false |
| Photographer name (Avedon, Goldin, Eggleston…) | `photographer` | false |
| Photo movement (street photography, new topographics…) | `movement` | false |
| Mood / adjective (gritty, ethereal, vintage…) | `mood` | false |

`needs_rewrite=true` types require the painter→photo rewrite at synthesis
time. The final `style_anchor` field MUST already be the rewritten form;
runtime does NOT re-apply rewriting.

**If unclear:** ask the user one question. Don't guess between painter
and photographer just because both are proper nouns.

---

## Step S1 — Web research (5-8 searches)

Use `WebSearch` to ground the style in real-world visual references.
Do NOT let the agent invent palette / camera / film stock from imagination
— that produces vague style anchors that Gemini renders as generic.

### Target query templates by type

Adapt these for the specific style. Aim for **5-8 searches**, diverse
sources.

**For `magazine`** (e.g., "Apartamento"):
1. `<magazine> photography style characteristics`
2. `<magazine> typical lighting palette grain`
3. `<magazine> signature photographers`
4. `<magazine> camera and film stock`
5. `<magazine> editorial recipe analysis`

**For `photographer`** (e.g., "Saul Leiter"):
1. `<photographer> signature style techniques`
2. `<photographer> camera lens film stock`
3. `<photographer> color palette lighting approach`
4. `<photographer> contemporary editorial influence`
5. `<photographer> visual recipe for editorial work`

**For `painter` / `movement`** (e.g., "Hopper", "ukiyo-e"):
1. `<painter/movement> visual vocabulary core elements`
2. `<painter/movement> color palette signature`
3. `<painter/movement> composition rules conventions`
4. `<painter/movement> lighting language atmosphere`
5. `<painter/movement> contemporary photographers reference inspired by`
6. `<painter/movement> editorial photography homage`

**For `mood`** (e.g., "ethereal cold"):
1. `<mood adjective> editorial photography examples`
2. `<mood adjective> lighting palette grain typical`
3. `<mood adjective> photographers known for this`
4. `<mood adjective> camera and film stock conventions`

### Search discipline

- Read snippets; only `WebFetch` if a source seems essential (saves tokens)
- Capture **3-5 concrete details per area** (real photographer names,
  real palette hex if found, real period equipment names)
- Note 3-5 source URLs to cite at the end (`source_notes` field)

---

## Step S2 — Synthesis rules

Write the new `templates/styles/<name>.yaml` using the closest existing
yaml as structural exemplar:

| Type | Use as exemplar |
|---|---|
| `magazine` | `national-geographic.yaml` |
| `photographer` | (no shipped seed; follow `magazine` shape, list 1 photographer in pool) |
| `painter` | `matisse-fauve.yaml` or `hopper-quiet.yaml` |
| `movement` | `hokusai-ukiyo.yaml` |
| `mood` | `dreamy-warm.yaml` or `wes-anderson.yaml` |

### Required fields (per `templates/styles/README.md` Schema)

- `schema_version: 1`
- `name: <slug>` (must match filename without `.yaml`)
- `type: <one of taxonomy>`
- `display_name: {en, zh}`
- `trigger_keywords: [...]` — 4-8 entries, mix English / Chinese /
  alternative spellings. Specific enough to avoid false positives.
- `needs_rewrite: <bool>` — descriptive metadata
- `style_anchor: |` — 50-150 words. **For `painter` / `movement` types,
  this MUST already be the photo-medium-rewritten form** — do NOT leave
  raw painter words.
- `photographer_pool` — 2-3 names
- `camera_pool` — 2-3 camera + lens + film combinations
- `source_notes: |` — 3-5 sentences citing where the recipe came from

### Discipline rules — non-negotiable

1. **Anchor to real, specific references.** Real photographer names, real
   camera bodies (Leica M11 / Sony A7R V / Hasselblad H6D-100c), real
   film stocks (Kodak Portra 400 / Tri-X 400 / Fujifilm Pro 400H). NOT
   generic "vintage 35mm camera" — actual model names.

2. **No living-artist style theft.** "Annie Leibovitz tradition" OK
   (technique reference); "by Annie Leibovitz" OK as photographer pool
   name. Avoid copying contemporary brand-protected content directly.

3. **For painter / movement types, the rewrite must be explicit.** The
   `style_anchor` text must include all three:
   - "shows up as <set design / palette / lighting language>"
   - "shot on <real camera> + <real lens> + <real film>"
   - "NOT a <painting / drawing / illustration>; a photograph of..."

4. **Concrete over generic.** "Single warm side light at 30° off-camera-
   left, deep matte shadow on opposite side" beats "dramatic lighting".
   "Slight cyan-shadow / yellow-highlight pull (NOT teal-orange LUT)"
   beats "color graded".

5. **No `{{...}}` placeholders inside `style_anchor`.** Unlike content
   yamls, style anchors are post-substitution finals — they get
   copy-pasted verbatim into all 16 prompts.

6. **`trigger_keywords` must be specific.** Avoid `"vintage"` alone —
   it'll match too many things. `"vintage 70s warmth"` better.

---

## Step S3 — Validation

After writing, run this Bash check before showing to the user:

```bash
.venv/bin/python -c "
import yaml, pathlib, re
NAME = '<slug>'  # fill in
d = yaml.safe_load(pathlib.Path(f'templates/styles/{NAME}.yaml').read_text())
assert d['schema_version'] == 1
assert d['name'] == NAME
assert d['type'] in ('painter', 'movement', 'magazine', 'photographer', 'mood')
assert isinstance(d['needs_rewrite'], bool)
assert 'display_name' in d and 'en' in d['display_name'] and 'zh' in d['display_name']
assert isinstance(d['trigger_keywords'], list) and 4 <= len(d['trigger_keywords']) <= 12
assert 'style_anchor' in d
sa = d['style_anchor']
assert 50 <= len(sa.split()) <= 200, f'style_anchor word count {len(sa.split())} not in 50-200'
assert '{{' not in sa, 'style_anchor must have no {{...}} placeholders'
if d['needs_rewrite']:
    # Painter / movement / drawing types: rewrite must be explicit
    assert 'shot on' in sa.lower() or 'photographed' in sa.lower(), \
        'painter/movement type missing photo medium enforcement'
    assert 'not a' in sa.lower() or 'not an' in sa.lower(), \
        'painter/movement type missing explicit NOT-a-painting clause'
print('ok')
"
```

If validation fails, edit the yaml and re-run. Don't proceed past `ok`.

---

## Step S4 — Show user (the scaffold gate)

Don't dump the entire yaml. Show a structured summary:

```
Scaffolded templates/styles/<name>.yaml

Type: <type>  (needs_rewrite=<bool>)
Display: <en> / <zh>

Trigger keywords:
  - <kw1>
  - <kw2>
  - ...

Style anchor (50-150 words, will be {{STYLE_ANCHOR}} verbatim):
  <full text>

Photographer pool:
  - <p1>
  - <p2>

Camera pool:
  - <c1>
  - <c2>

Web sources cited:
  - <url 1>
  - <url 2>
  - ...

OK to land at templates/styles/<name>.yaml and proceed to Phase 1?
Or adjust:
  · style anchor wording (e.g., shift photographer reference)
  · palette / lighting (more / less specific)
  · trigger keywords (add user's exact phrasing)
```

User responds:
- "OK" → land yaml, continue Phase 0
- "Use Tim Walker instead of Annie Leibovitz" → swap in `style_anchor`
- "Trigger should also catch '复古暖色'" → add keyword

Iteration at this gate is **cheap** (no API calls). Iterate freely.

---

## Step S5 — Persistence

The yaml lands at `templates/styles/<name>.yaml`. Auto-discovered by future
issues' `trigger_keywords` matching.

**Don't auto-commit.** Wait until the user has actually run an issue
end-to-end with this style and seen the output before committing. A
scaffold that looks good in summary but produces bad images shouldn't
poison the shared library.

After the user runs an issue and approves the result, suggest:
> "This style scaffold worked well. Want me to commit
> `templates/styles/<name>.yaml` so it ships in the next push?"

If yes:
```bash
git add templates/styles/<name>.yaml && git commit -m "Add <name> style"
```

---

## Common scaffold mistakes

| Symptom | Root cause | Fix |
|---|---|---|
| 4K outputs look generic | `style_anchor` uses vibe language | Rewrite with concrete photographer + camera + film + lighting direction |
| Outputs look like illustration despite rewrite | `needs_rewrite` was set but rewrite incomplete | Add explicit "NOT a painting; a photograph of..." clause |
| Trigger never matches user's actual phrasing | `trigger_keywords` too generic / wrong language | Add the user's verbatim phrase to keywords |
| Library file rejected by validation | `style_anchor` over 200 words / has `{{...}}` | Trim to 50-150 words; remove placeholders |

---

## Cost / time budget

- 5-8 WebSearch calls: <$0.01
- Agent synthesis: 3-5 min
- Validation: instant
- User review at gate: 1-3 min interactive
- **Marginal cost of scaffold itself: <$0.01**

The scaffolded yaml is reusable for future issues — second issue of the
same style = no scaffold cost.

---

## When NOT to scaffold

- User asks for a style already in `templates/styles/` → just match and
  use it
- User wants a *minor variant* of an existing style ("kinfolk but cooler") →
  don't scaffold a new yaml for one-off variation; use the closest match
  and override `style_anchor` inline for that one issue
- User explicitly wants illustration / painting medium output → that's
  **out of scope** for this skill; redirect to a different tool
