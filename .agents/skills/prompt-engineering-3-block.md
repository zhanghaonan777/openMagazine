# prompt-engineering-3-block

A reusable 3-block pattern for image-generation prompts.

## The pattern

~~~
[Block 1: STYLE ANCHOR]
photographed by <photographer>, shot on <camera> with <lens>, <film stock> grain,
raw uncorrected, no LUTs.

[Block 2: SCENE]
<subject> <action / pose>, <setting>, <lighting>, <shot scale>.

[Block 3: NEGATIVES]
no <unwanted style 1>, no <unwanted style 2>, no <unwanted artifact>.
~~~

## Why this structure

- **Block 1 first**: anchors the rendering medium. Most image models weight earlier tokens more heavily; if you put style at the end, it's frequently overridden by scene words.
- **Block 2 in plain English**: the model parses scene descriptions best as natural sentences, not as keyword lists.
- **Block 3 last**: negative prompts work well at the end where the model has finished building the positive concept.

## Common style anchors

- "photographed by Annie Leibovitz, shot on Hasselblad H6D, Kodak Portra 800 grain, raw uncorrected, no LUTs"
- "photographed by Roger Deakins, shot on Arri Alexa with Cooke Anamorphic, raw uncorrected, no LUTs"
- "photographed by Saul Leiter, shot on Leica M3 with 50mm Summicron, Kodachrome grain, raw uncorrected"

## Common negative prompt phrases

- `cartoonish, plastic skin/fur, AI-looking`
- `illustrative style, poster art, painted look`
- `garbled typography, watermarks, text artifacts`
- `shallow depth-of-field bokeh blur` (when crisp focus is desired)
