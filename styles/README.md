# Style Library (simple mode)

Each `<name>.yaml` here is one **photographic style** that can become the
verbatim `{{STYLE_ANCHOR}}` for an entire issue.

This library exists so that user inputs like "国家地理风格" / "Matisse 风格"
/ "梦幻温暖风" can be **looked up as data** instead of relying on the agent
to free-form generate a style anchor every time.

## Schema

```yaml
schema_version: 1
name: <slug>                      # filename = "<name>.yaml"
type: magazine                    # painter | movement | magazine | photographer | mood
display_name:
  en: "..."
  zh: "..."
trigger_keywords:                 # case-insensitive substring match
  - "..."
  - "..."

needs_rewrite: false              # painter / movement / drawing-medium types: true
                                  # magazine / photographer / mood: false

# The verbatim {{STYLE_ANCHOR}} string. Substituted into all 16 prompts.
# After read, the agent uses this string AS-IS — no further rewriting.
style_anchor: |
  <full multi-line photo style anchor — 50-150 words>

# Optional pools the agent can rotate among for per-page variety.
# Used to nudge slight per-page variation without breaking the master
# style_anchor.
photographer_pool:                # OPTIONAL
  - "..."
camera_pool:                      # OPTIONAL
  - "..."

# Where this style was learned from (for audit + scaffold-style provenance).
source_notes: |
  Notes / web sources / typical use case.
```

## Type taxonomy

| `type` | Examples | `needs_rewrite` | What the agent does |
|---|---|---|---|
| `magazine` | National Geographic, Vogue Italia, Kinfolk | false | Use `style_anchor` verbatim. Already photo medium. |
| `photographer` | Annie Leibovitz, Saul Leiter | false | Use `style_anchor` verbatim. |
| `mood` | dreamy-warm, vintage-melancholy | false | Use `style_anchor` verbatim. |
| `painter` | Matisse, Hopper, Klimt | true | `style_anchor` ALREADY contains the photo-medium rewrite. Use verbatim. |
| `movement` | fauvism, ukiyo-e, art-nouveau | true | Same as painter. |

The `needs_rewrite` flag is **descriptive metadata** — it tells you "this
style entered the library after a painter→photo rewrite." The agent does
NOT need to rewrite again at runtime; the `style_anchor` field is already
the rewritten form.

## Trigger matching

Agent matching algorithm (case-insensitive, substring):

```python
for yaml_path in glob("templates/styles/*.yaml"):
    style = yaml.load(yaml_path)
    for keyword in style["trigger_keywords"]:
        if keyword.lower() in user_style_input.lower():
            return style["style_anchor"]   # match!
# No match → trigger references/scaffold-style.md meta-protocol
```

Keep `trigger_keywords` **specific enough** to avoid false positives.
"natgeo" should match National Geographic; just "nat" alone should not.

## Adding a new style

Three paths, in order of preference:

1. **scaffold-style meta-capability** (zero manual work):
   When user gives a style not in the library, `references/scaffold-style.md`
   triggers — agent web-searches the style, synthesizes a yaml, and asks
   you to approve. Lands here automatically.

2. **Manual write** when you already know the recipe:
   Copy an existing yaml as template, edit, drop in here. PR.

3. **Inline fallback** (degraded — should be rare):
   `references/simple-mode-prompts.md` Obligation 2 has 3-class inline
   logic (A: painter rewrite / B: magazine expand / C: mood augment) the
   agent uses when both lookup and scaffold are skipped. The result does
   NOT land in the library.

## Shipped seed styles

| File | Type | Trigger keywords (sample) |
|---|---|---|
| `national-geographic.yaml` | magazine | "国家地理", "natgeo", "national geographic" |
| `vogue-italia.yaml` | magazine | "vogue", "vogue italia", "fashion editorial" |
| `kinfolk.yaml` | magazine | "kinfolk", "极简文艺", "minimalist editorial" |
| `wes-anderson.yaml` | mood | "wes anderson", "韦斯·安德森", "symmetric pastel" |
| `dreamy-warm.yaml` | mood | "dreamy", "梦幻温暖", "warm dreamy" |
| `matisse-fauve.yaml` | painter | "matisse", "马蒂斯", "fauvism", "野兽派" |
| `hopper-quiet.yaml` | painter | "hopper", "edward hopper", "霍珀", "American realism" |
| `hokusai-ukiyo.yaml` | movement | "ukiyo-e", "浮世绘", "hokusai", "葛饰北斋" |
