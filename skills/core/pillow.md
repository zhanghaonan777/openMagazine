# pillow

`tools/image/pillow_split.py` — N×M cell extraction from a storyboard PNG.

## When to use

Stage 3 storyboard splitting (after `image_gen.imagegen` produces a 4×4 PNG, slice into 16 cells for Stage 4 references).

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

## Why top_crop_px

The storyboard model often draws page numbers at the top of each cell. Slicing without cropping leaks "01", "02", etc. into the upscaled images. Default 60px works for 1024×1536 storyboards; tune via `library/layouts/<name>.yaml`.

## See also

- Layer 3 doc: `.agents/skills/pillow-image-ops.md`
- Layout config: `library/layouts/<name>.yaml.top_crop_px_default`
