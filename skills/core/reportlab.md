# reportlab

`tools/pdf/reportlab_compose.py` — A4 portrait PDF assembly.

## When to use

Stage 5 (compose). Takes `<issue>/images/page-*.png` and produces `<issue>/magazine.pdf`.

## How to use

~~~python
from tools.pdf.reportlab_compose import ReportlabCompose
import pathlib

tool = ReportlabCompose()
result = tool.run(
    pathlib.Path("output/<slug>/"),  # issue_dir; expects images/ subdirectory
    out_path=None,                    # default: <issue>/magazine.pdf
    order_file=None,                  # optional: text file with one filename per line
    spread_mode="split",              # "split" → 3:2 image becomes two pages
)
# result = {"out_path": str, "image_count": int, "page_count": int, "size_mb": float}
~~~

## Aspect classification

| Image aspect | Treatment |
|---|---|
| 2:3 ± 0.05 | Full-bleed portrait page |
| 3:2 ± 0.05 | Split into two portrait pages (default) OR one landscape page (`spread_mode="landscape"`) |
| Other | Letterboxed onto black portrait page (warning) |

## See also

- Layer 3 doc: `.agents/skills/reportlab-typography.md`
- Page numbering: open issue — currently no page numbers; integrate into image during Stage 4 prompt
