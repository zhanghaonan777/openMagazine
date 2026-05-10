"""Weasyprint compose — render HTML/CSS to print PDF.

Used by editorial-* layouts (schema_version=2). Reads layout html.j2 +
components, fills with article copy + brand typography + image paths,
renders to magazine.pdf.
"""
from __future__ import annotations

# --- macOS arm64 Homebrew preload shim ---
# weasyprint's cffi-based gobject lookup (via ctypes.util.find_library) fails
# by default on Apple Silicon because cffi calls dlopen("libgobject-2.0-0")
# with no path/extension and no Homebrew dir on the search list. We solve it
# two ways (defense in depth) at module-import time, BEFORE
# `from weasyprint import HTML` triggers cffi:
#   1) Add Homebrew lib dir to DYLD_FALLBACK_LIBRARY_PATH so cffi's bare-name
#      dlopen resolves.
#   2) Preload key libs with RTLD_GLOBAL so transitive symbols are present.
import os
import sys
import ctypes
if sys.platform == "darwin":
    for _root in ("/opt/homebrew/lib", "/usr/local/lib"):
        if os.path.isdir(_root):
            _existing = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
            _parts = _existing.split(":") if _existing else []
            if _root not in _parts:
                _parts.insert(0, _root)
                os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(_parts)
    for _libname in ("libgobject-2.0.0.dylib", "libpango-1.0.0.dylib",
                     "libharfbuzz.0.dylib", "libfontconfig.1.dylib"):
        for _root in ("/opt/homebrew/lib", "/usr/local/lib"):
            _p = os.path.join(_root, _libname)
            if os.path.isfile(_p):
                try:
                    ctypes.CDLL(_p, mode=ctypes.RTLD_GLOBAL)
                    break
                except OSError:
                    pass

# --- normal imports ---
import pathlib
from typing import Any

from tools.base_tool import BaseTool


class WeasyprintCompose(BaseTool):
    capability = "pdf_compose"
    provider = "weasyprint"
    cost_per_call_usd = 0.0
    agent_skills = ["weasyprint-cookbook"]
    status = "active"

    def render_html_string(self, html: str, out_path: pathlib.Path,
                           *, base_url: pathlib.Path | None = None) -> dict:
        """Render an HTML string to PDF at out_path. Returns metadata."""
        from weasyprint import HTML

        out_path = pathlib.Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        base = str(base_url) if base_url else None
        doc = HTML(string=html, base_url=base).render()
        doc.write_pdf(str(out_path))
        size_mb = out_path.stat().st_size / (1024 * 1024)
        page_count = len(doc.pages)
        print(
            f"[weasyprint] {out_path.name}  {page_count} pages  {size_mb:.1f} MB",
            file=sys.stderr,
        )
        return {
            "pdf_path": str(out_path),
            "page_count": page_count,
            "size_mb": size_mb,
        }

    def render_template(
        self,
        *,
        layout_j2: pathlib.Path,
        context: dict,
        out_path: pathlib.Path,
        save_html: bool = True,
    ) -> dict:
        """Render a Jinja2 template with context, then to PDF.

        layout_j2 is the path to the template; the layout's directory + the
        project's library/layouts/ are included on the Jinja2 search path so
        {% include "_components/..." %} works. base_url for relative image
        paths is the project root.
        """
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        layout_j2 = pathlib.Path(layout_j2)
        project_root = pathlib.Path(__file__).resolve().parents[2]
        layout_dir = layout_j2.parent
        env = Environment(
            loader=FileSystemLoader([str(layout_dir), str(project_root / "library" / "layouts")]),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        tmpl = env.get_template(layout_j2.name)
        html = tmpl.render(**context)

        out_path = pathlib.Path(out_path)
        if save_html:
            html_path = out_path.with_suffix(".html")
            html_path.write_text(html, encoding="utf-8")

        return self.render_html_string(html, out_path, base_url=project_root)

    def run(self, *, issue_dir: pathlib.Path, layout: dict, brand: dict,
            article: dict, spec: dict) -> dict:
        """High-level entry: derive layout_j2 from layout name and render."""
        project_root = pathlib.Path(__file__).resolve().parents[2]
        layout_j2 = project_root / "library" / "layouts" / f"{layout['name']}.html.j2"
        out_path = pathlib.Path(issue_dir) / "magazine.pdf"

        context = {
            "layout": layout,
            "brand": brand,
            "article": article,
            "spec": spec,
            "language": brand.get("default_language", "en"),
            "issue_dir": str(issue_dir),
            "images_root": str(pathlib.Path(issue_dir) / "images"),
        }
        meta = self.render_template(
            layout_j2=layout_j2,
            context=context,
            out_path=out_path,
            save_html=True,
        )
        meta["html_path"] = str(out_path.with_suffix(".html"))
        return meta


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(WeasyprintCompose())
