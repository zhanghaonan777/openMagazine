# pillow-image-ops

PIL / Pillow common operations for image pipelines.

## Open + size

~~~python
from PIL import Image
with Image.open(path) as im:
    w, h = im.size
~~~

## Crop

`im.crop((left, top, right, bottom))` — the box is in image coordinates (top-left origin), pixels not points.

## Grid splitting

For an N×M grid with gutters:

~~~python
W, H = im.size
g = max(8, W // 200)              # auto gutter
cell_w = (W - (cols + 1) * g) // cols
cell_h = (H - (rows + 1) * g) // rows
for i in range(rows * cols):
    row, col = divmod(i, cols)
    x = g + col * (cell_w + g)
    y = g + row * (cell_h + g)
    cell = im.crop((x, y, x + cell_w, y + cell_h))
    cell.save(out_dir / f"cell-{i+1:02d}.png")
~~~

## Top-band crop (remove headers)

If the source has a labels band at the top of each cell (e.g., page numbers):

~~~python
cell = im.crop((x, y + top_crop_px, x + cell_w, y + cell_h))
~~~

## Resize / thumbnail

- `im.resize((w, h), Image.LANCZOS)` — high-quality scale.
- `im.thumbnail((max_w, max_h))` — preserves aspect, mutates in place.

## Format conversions

- `im.convert("RGB")` — strip alpha for JPEG output.
- `im.save("out.jpg", quality=92)` — JPEG quality 92 is a sweet spot.

## File size sanity

A 4K (2048×3072) RGB PNG = ~10-25 MB; lower likely indicates degraded output.
