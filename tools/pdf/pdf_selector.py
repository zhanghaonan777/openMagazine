"""pdf_selector — route pdf_compose calls by layout schema_version.

v1 layouts (plain-4 / plain-16, full-bleed image-only) → ReportlabCompose.
v2 layouts (editorial-16page, multi-image spreads with text) → WeasyprintCompose.

Director skills declare 'dispatch pdf_compose' and let the selector pick the
backend based on the resolved layout, instead of hard-coding either engine.
"""
from __future__ import annotations

from tools.base_tool import BaseTool
from tools.pdf.reportlab_compose import ReportlabCompose
from tools.pdf.weasyprint_compose import WeasyprintCompose


class PdfSelector(BaseTool):
    capability = "pdf_compose"
    provider = "selector"
    status = "active"

    def __init__(self):
        super().__init__()
        self._reportlab = ReportlabCompose()
        self._weasyprint = WeasyprintCompose()

    def choose_backend(self, *, layout: dict) -> BaseTool:
        sv = layout.get("schema_version")
        if sv == 1:
            return self._reportlab
        if sv == 2:
            return self._weasyprint
        raise ValueError(
            f"unsupported layout.schema_version {sv!r}; expected 1 or 2"
        )

    def run(self, *, layout: dict, **kwargs):
        return self.choose_backend(layout=layout).run(**kwargs)


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(PdfSelector())
