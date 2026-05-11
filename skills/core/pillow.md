# pillow

`tools/image/pillow_split.py` — cell extraction from storyboard PNGs.

## When to use

Stage 3 storyboard splitting:
- v1 simple layouts: slice an N×M grid into `cells/cell-NN.png`.
- v2 editorial layouts: slice planned irregular cells into `cells/spread-NN/<slot>.png`.

## How to use

~~~python
from tools.image.pillow_split import split_storyboard
import pathlib

cell_count = split_storyboard(
    pathlib.Path("output/<slug>/storyboard.png"),
    pathlib.Path("output/<slug>/cells/"),
    rows=4,
    cols=4,
    gutter="auto",       # or an int — gutter pixel width
    top_crop_px=60,      # remove page-number labels (cropped from each cell's top)
)
~~~

For v2 editorial storyboards:

~~~python
from tools.image.pillow_split import split_by_plan
from lib.storyboard_planner import plan_storyboard

plan = plan_storyboard(layout)
cell_count = split_by_plan(
    pathlib.Path("output/<slug>/storyboard.png"),
    pathlib.Path("output/<slug>/cells/"),
    plan=plan,
)
~~~

## Why top_crop_px

The storyboard model often draws page numbers at the top of each cell. Slicing without cropping leaks "01", "02", etc. into the upscaled images. Default 60px works for 1024×1536 storyboards; tune via `library/layouts/<name>.yaml`.

## See also

- Layer 3 doc: `.agents/skills/pillow-image-ops.md`
- Layout config: `library/layouts/<name>.yaml.top_crop_px_default` for v1; `image_slots` for v2
