# article-writer

How an agent drafts an editorial article from spec + theme + layout.

## When to invoke

Articulate stage of editorial-* pipelines. The agent is asked to fill in
`library/articles/<slug>.yaml` from scratch given:
- subject traits (from research_brief.json)
- theme world + page_plan_hints (from theme yaml)
- layout's spread_plan + text_slots_required (from layout yaml)

## Drafting rules

### 1. Match each spread to its `text_slots_required`

For `editorial-16page`:

| Spread type | Required article fields |
|---|---|
| `cover` | `cover_line` + `cover_kicker` (article-level, not in spread_copy) |
| `toc` | `table_of_contents` (list of `{page, en, zh}`) |
| `feature-spread` | `title` + `kicker` + `lead` + `body` |
| `pull-quote` | `quote` + `quote_attribution` |
| `portrait-wall` | `title` + `captions` (list of `{slot, en, zh}`) |
| `colophon` | `credits` (`photographer` / `art_direction` / `printing` / `copyright` / `contact`) |
| `back-cover` | `quote` + `quote_attribution` |

### 2. Length targets

- `title`: 1–3 words, all caps
- `kicker`: short label like `"Chapter 02"` or `"FEATURE STORY"`
- `lead`: 1–2 sentences, italic-friendly, hooks the reader
- `body`: 3 paragraphs, each 60–120 words. Total ≈ 250 words per spread
- `pull-quote`: 1–2 short lines, max 14 words
- `caption`: 1–4 words

### 3. Voice

Editorial, slightly literary, present tense, restrained. Avoid:
- Marketing language (`"revolutionary"`, `"groundbreaking"`)
- Emojis in body copy
- Generic AI fillers (`"In this article we will explore..."`)
- Second-person address

### 4. Multi-language

Write `en` first. If `brand.default_language == "zh"` or the article has
a Chinese theme, also write `zh`. Use the same voice in zh — terse,
literary, present tense. Don't translate word-for-word; localize.

### 5. `image_slot_overrides`

For each spread, write a one-sentence scene description per `image_slot`
in that spread (matching layout's slot ids). These feed Stage 4 upscale
prompts AND get bundled into the Stage 3 storyboard prompt's `CELL_LIST`.

~~~yaml
image_slot_overrides:
  feature_hero: "Luna at boulder, hand on rock, three-quarter front view, hero portrait"
  feature_captioned.1: "footprints in regolith, low sun raking shadows, 3:2 wide"
  feature_captioned.2: "wide lunar plain, subject mid-frame, deep shadow side"
  feature_captioned.3: "close-up of glove on rock, macro detail"
~~~

Without these, every slot uses the theme's generic page_plan_hint, which
collapses 21 distinct images into ~9 visually similar ones.

### 6. Cross-spread coherence

The 9 spreads should read as one issue with an arc:

| Spread | Role |
|---|---|
| 1 cover | hook |
| 2 toc | preview |
| 3 feature 1 | departure |
| 4 feature 2 | development |
| 5 pull-quote | mid-issue rest |
| 6 feature 3 | climax |
| 7 portrait-wall | montage |
| 8 colophon | resolution |
| 9 back | coda |

Use the theme's `page_plan_hints` as scaffolding; expand each into full
editorial language.

## Self-review before persisting

- ✅ All 9 spreads have all `text_slots_required` fields populated.
- ✅ No two consecutive spread titles share a first word.
- ✅ Every `image_slot` declared in the layout has a slot-specific scene
  in some spread's `image_slot_overrides`.
- ✅ Issue reads as a story (cover hook → coda) not a directory of
  unrelated photos.
- ✅ Word counts in target ranges (no 600-word "body" blocks; no
  3-word "lead" stubs).

If any check fails, revise before writing the yaml — the user will see
the file at the articulate checkpoint and small issues become
expensive feedback rounds at that point.
