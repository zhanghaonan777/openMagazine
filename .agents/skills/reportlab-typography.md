# reportlab-typography

ReportLab PDF assembly idioms.

## Page sizes

- A4 portrait: `from reportlab.lib.pagesizes import A4` → (595.27, 841.89) points
- A4 landscape: `landscape(A4)` → (841.89, 595.27)
- Letter: `LETTER` → (612, 792)

Set per-page: `c.setPageSize(landscape(A4))`. Reset: `c.setPageSize(A4)`.

## Drawing images

~~~python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

c = canvas.Canvas("out.pdf", pagesize=A4)
W, H = A4
c.drawImage("page.png", 0, 0, W, H, preserveAspectRatio=False)  # full-bleed
c.showPage()
c.save()
~~~

- `preserveAspectRatio=False` → fills the page, may stretch.
- `preserveAspectRatio=True, anchor="c"` → letterbox centered.

## In-memory images via ImageReader

When the image isn't a file (e.g., cropped from PIL):

~~~python
from reportlab.lib.utils import ImageReader
c.drawImage(ImageReader(pil_image), 0, 0, W, H)
~~~

## Multi-page from one source

For a 3:2 spread to two A4 portrait pages: crop the PIL source into left/right halves, draw each on its own page.

## Typography

- Embed fonts: `pdfmetrics.registerFont(TTFont(name, path))`.
- Set: `c.setFont("Helvetica-Bold", 24)`.
- Draw: `c.drawString(x, y, "Title")` (uses bottom-left origin).
- Color: `c.setFillColorRGB(r, g, b)` with floats 0-1.

## File size

For 4K source images embedded full-bleed, expect ~5-15 MB per page in the output PDF. ReportLab encodes raster images via JPEG/Flate; PNG sources keep alpha.
