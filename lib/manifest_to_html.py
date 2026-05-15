"""manifest_to_html — render a slide_manifest to a self-contained HTML doc.

The doc uses absolute-positioned region divs over an @page-sized canvas.
Each slide becomes ONE printable page sized to the slide canvas (1 or 2 page
widths). This is the manifest-driven render path — separate from the legacy
Jinja2 + per-spread template path that ships in WeasyprintCompose.run().

Goal of this module: prove the manifest contract is sufficient input for the
PDF realizer. The visual output is intentionally simpler than the Jinja
templates — no drop-cap, no hyphenation, no per-spread bespoke layout —
but the page rhythm, image placement, and text content faithfully follow
the manifest. The Jinja templates remain canonical for v0.3.2 production.
"""
from __future__ import annotations

import html as _html
import pathlib
from typing import Any


def manifest_to_html(
    manifest: dict,
    *,
    issue_dir: pathlib.Path | str | None = None,
    interactive: bool = False,
) -> str:
    """Render a slide_manifest to a self-contained HTML string.

    issue_dir, when provided, is the absolute path that image source_paths
    in the manifest are relative to. We emit <img src> as a file:// URI
    rooted at issue_dir so WeasyPrint can find the bitmap regardless of
    its base_url setting.

    interactive=True enables the browser-edit mode: text regions get
    contenteditable, a floating toolbar appears, and edits are tracked
    against bind_field paths. The user downloads an article-patch.json
    that lib.article_patch can apply back to library/articles/<slug>.yaml.
    Do not pass interactive=True to WeasyPrint — the JS won't fire and the
    toolbar would be a static element in the PDF.
    """
    target = manifest.get("output_target", {})
    tokens = manifest.get("design_tokens", {})
    palette = tokens.get("color_palette", {})

    page_w, page_h, unit = _page_size_with_unit(target)
    paper = palette.get("paper", "#FFFFFF")
    ink = palette.get("ink", "#1A1A1A")

    issue_root = pathlib.Path(issue_dir).resolve() if issue_dir else None

    # Declare an @page rule per pages_per_instance value used; gives us
    # 1-page singlets and 2-page facing canvases.
    page_widths: set[int] = set()
    for slide in manifest.get("slides", []):
        ppi = int(slide.get("pages_per_instance", 1))
        page_widths.add(ppi)

    page_rules = []
    for ppi in sorted(page_widths):
        page_rules.append(
            f"@page slide{ppi} {{ size: {page_w * ppi}{unit} {page_h}{unit}; margin: 0; }}"
        )

    css = _format_css(
        page_rules="\n".join(page_rules),
        paper=paper,
        ink=ink,
        page_w=page_w,
        page_h=page_h,
        unit=unit,
    )
    if interactive:
        css += "\n" + _INTERACTIVE_CSS

    body_parts = [
        _render_slide(
            slide, palette=palette, issue_root=issue_root, interactive=interactive
        )
        for slide in manifest.get("slides", [])
    ]
    if interactive:
        body_parts.insert(0, _INTERACTIVE_TOOLBAR)
        body_parts.append(f"<script>\n{_INTERACTIVE_JS}\n</script>")

    locale = manifest.get("locale", "en")
    spec_slug = manifest.get("spec_slug", "")
    body_attrs = (
        f' data-spec-slug="{_html.escape(spec_slug)}"'
        f' data-locale="{_html.escape(locale)}"'
        f' data-interactive="{"true" if interactive else "false"}"'
    )
    return _DOC_TEMPLATE.format(
        locale=_html.escape(locale),
        title=_html.escape(spec_slug),
        css=css,
        body_attrs=body_attrs,
        body="\n".join(body_parts),
    )


# ---------------------------------------------------------------------------
# Slide / region rendering
# ---------------------------------------------------------------------------


def _render_slide(
    slide: dict,
    *,
    palette: dict,
    issue_root: pathlib.Path | None,
    interactive: bool = False,
) -> str:
    spread_type = slide.get("spread_type", "")
    ppi = int(slide.get("pages_per_instance", 1))
    spread_idx = slide.get("spread_idx", "?")

    # Sort regions by z_index so painters' order is deterministic.
    regions = sorted(
        slide.get("regions", []), key=lambda r: int(r.get("z_index", 0))
    )
    region_html = "\n".join(
        _render_region(
            r, palette=palette, issue_root=issue_root, interactive=interactive
        )
        for r in regions
    )

    return (
        f'<section class="slide slide{ppi}" '
        f'data-spread-idx="{spread_idx}" '
        f'data-spread-type="{_html.escape(spread_type)}">\n'
        f"{region_html}\n"
        f"</section>"
    )


def _render_region(
    region: dict,
    *,
    palette: dict,
    issue_root: pathlib.Path | None,
    interactive: bool = False,
) -> str:
    role = region.get("role", "decorative")
    region_id = region.get("id", "")
    rect = region.get("rect_norm") or [0, 0, 1, 1]
    if len(rect) != 4:
        rect = [0, 0, 1, 1]
    x0, y0, x1, y1 = rect
    left = x0 * 100
    top = y0 * 100
    width = (x1 - x0) * 100
    height = (y1 - y0) * 100
    z_index = int(region.get("z_index", 0))
    claim_role = region.get("claim_role")

    style_props = [
        f"left:{left:.4f}%",
        f"top:{top:.4f}%",
        f"width:{width:.4f}%",
        f"height:{height:.4f}%",
        f"z-index:{z_index}",
    ]

    data_attrs = [
        f'data-role="{_html.escape(role)}"',
        f'data-id="{_html.escape(region_id)}"',
    ]
    if claim_role:
        data_attrs.append(f'data-claim-role="{_html.escape(str(claim_role))}"')
    bind_field = region.get("bind_field")
    if bind_field:
        data_attrs.append(f'data-bind-field="{_html.escape(str(bind_field))}"')

    classes = [
        "region",
        f"region-{role}",
        f"region-id-{_safe_class(region_id)}",
    ]
    if claim_role:
        classes.append(f"claim-{claim_role}")

    extra_attrs: list[str] = []
    if interactive and role == "text" and bind_field:
        extra_attrs.append('contenteditable="true"')
        extra_attrs.append('spellcheck="false"')

    inner = _render_region_inner(region, palette=palette, issue_root=issue_root, style_props=style_props)
    style_str = ";".join(style_props)

    return (
        f'<div class="{" ".join(classes)}" '
        f"{' '.join(data_attrs)} "
        + (" ".join(extra_attrs) + " " if extra_attrs else "")
        + f'style="{style_str}">'
        f"{inner}"
        f"</div>"
    )


def _render_region_inner(
    region: dict,
    *,
    palette: dict,
    issue_root: pathlib.Path | None,
    style_props: list[str],
) -> str:
    role = region.get("role")

    if role == "image":
        img = region.get("image") or {}
        src = img.get("source_path", "")
        if issue_root and src and not src.startswith(("http:", "https:", "file:")):
            src = (issue_root / src).resolve().as_uri()
        alt = img.get("alt_text", "")
        return f'<img src="{_html.escape(src)}" alt="{_html.escape(alt)}">'

    if role == "text":
        text = region.get("text") or ""
        typography = region.get("typography") or {}
        style_props.extend(_typography_to_style(typography))
        cp = region.get("component_props") or {}
        align = cp.get("align")
        if align:
            style_props.append(f"text-align:{align}")
        # Preserve newlines in body text as <br> for the minimal renderer.
        # Real templates do paragraph splitting; we keep this simple.
        body = "<br>".join(_html.escape(line) for line in text.split("\n"))
        return body

    if role == "accent":
        accent = region.get("accent") or {}
        color = accent.get("color") or palette.get("accent", "#000000")
        # Accent background = accent color; the region's height controls
        # the visible thickness in the layout.
        style_props.append(f"background:{color}")
        return ""

    # decorative / container / unknown: empty div with class hooks
    return ""


def _typography_to_style(t: dict) -> list[str]:
    out: list[str] = []
    chain = t.get("family_chain") or []
    if chain:
        out.append("font-family:" + ", ".join(_css_font_name(f) for f in chain))
    if isinstance(t.get("size_pt"), (int, float)):
        out.append(f"font-size:{t['size_pt']}pt")
    if isinstance(t.get("weight"), int):
        out.append(f"font-weight:{t['weight']}")
    if isinstance(t.get("style"), str) and t["style"] in ("italic", "oblique"):
        out.append(f"font-style:{t['style']}")
    if isinstance(t.get("line_height"), (int, float)):
        out.append(f"line-height:{t['line_height']}")
    if isinstance(t.get("letter_spacing"), (int, float)):
        out.append(f"letter-spacing:{t['letter_spacing']}em")
    if isinstance(t.get("transform"), str) and t["transform"] != "none":
        out.append(f"text-transform:{t['transform']}")
    if isinstance(t.get("color"), str):
        out.append(f"color:{t['color']}")
    return out


def _css_font_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return "serif"
    if name.lower() in ("serif", "sans-serif", "monospace", "cursive", "fantasy"):
        return name.lower()
    if " " in name and not (name.startswith("'") or name.startswith('"')):
        return f"'{name}'"
    return name


def _safe_class(s: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in s)


def _page_size_with_unit(target: dict) -> tuple[float, float, str]:
    ps = target.get("page_size") or {}
    return float(ps.get("width", 210)), float(ps.get("height", 297)), str(ps.get("unit", "mm"))


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


def _format_css(*, page_rules: str, paper: str, ink: str,
                page_w: float, page_h: float, unit: str) -> str:
    """Render the document CSS (named pages + slide layout)."""
    page_w_two = page_w * 2
    return (
        f"{page_rules}\n\n"
        "* { box-sizing: border-box; }\n"
        f"html, body {{ margin: 0; padding: 0; background: {paper}; color: {ink}; }}\n"
        "body { font-family: serif; }\n\n"
        ".slide {\n"
        "  position: relative;\n"
        "  overflow: hidden;\n"
        "  page-break-after: always;\n"
        f"  background: {paper};\n"
        "}\n"
        f".slide1 {{ width: {page_w}{unit}; height: {page_h}{unit}; page: slide1; }}\n"
        f".slide2 {{ width: {page_w_two}{unit}; height: {page_h}{unit}; page: slide2; }}\n\n"
        ".region { position: absolute; }\n"
        ".region-image > img { width: 100%; height: 100%; object-fit: cover; display: block; }\n"
        ".region-text { display: flex; flex-direction: column; justify-content: flex-start; }\n"
    )


_DOC_TEMPLATE = """\
<!DOCTYPE html>
<html lang="{locale}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body{body_attrs}>
{body}
</body>
</html>
"""


_INTERACTIVE_CSS = """\
/* Interactive (browser-edit) affordances */
[contenteditable] {
  outline: 1px dashed transparent;
  transition: outline-color 120ms ease;
  cursor: text;
}
[contenteditable]:hover { outline-color: rgba(0,0,0,0.18); }
[contenteditable]:focus { outline-color: rgba(0,100,200,0.6); outline-offset: 2px; }
.region-edited { background: rgba(255, 220, 0, 0.18) !important; }
#om-toolbar {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 9999;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-shadow: 0 4px 18px rgba(0,0,0,0.12);
  padding: 8px 12px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 12px;
  color: #222;
  display: flex;
  align-items: center;
  gap: 12px;
}
#om-toolbar strong { font-weight: 600; }
#om-toolbar button {
  border: 1px solid #888;
  background: #fafafa;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
#om-toolbar button:hover:not(:disabled) { background: #f0f0f0; }
#om-toolbar button:disabled { opacity: 0.45; cursor: not-allowed; }
@media print { #om-toolbar { display: none; } }
"""


_INTERACTIVE_TOOLBAR = """\
<div id="om-toolbar" data-no-bind>
  <span><strong id="om-edit-count">0</strong> edits</span>
  <button id="om-save-btn" type="button" disabled>Download article-patch.json</button>
</div>
"""


# The edit-tracker. Vanilla JS, no deps. Keyed by [data-bind-field].
_INTERACTIVE_JS = """\
(function () {
  var edits = new Map();
  var nodes = document.querySelectorAll('[contenteditable="true"][data-bind-field]');
  nodes.forEach(function (el) {
    var original = el.innerText;
    el.dataset.originalText = original;
    el.addEventListener('input', function () {
      var current = el.innerText;
      var field = el.dataset.bindField;
      if (current === original) {
        edits.delete(field);
        el.classList.remove('region-edited');
      } else {
        edits.set(field, current);
        el.classList.add('region-edited');
      }
      updateStatus();
    });
  });

  function updateStatus() {
    var count = edits.size;
    var countEl = document.getElementById('om-edit-count');
    var btn = document.getElementById('om-save-btn');
    if (countEl) countEl.textContent = String(count);
    if (btn) btn.disabled = count === 0;
  }

  var btn = document.getElementById('om-save-btn');
  if (btn) {
    btn.addEventListener('click', function () {
      var body = document.body;
      var patch = {
        generated_at: new Date().toISOString(),
        spec_slug: body.dataset.specSlug || '',
        locale: body.dataset.locale || 'en',
        patches: Object.fromEntries(edits),
      };
      var blob = new Blob([JSON.stringify(patch, null, 2)], {
        type: 'application/json',
      });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = 'article-patch.json';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    });
  }
  updateStatus();
})();
"""
