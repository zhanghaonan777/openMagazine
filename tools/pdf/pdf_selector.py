"""pdf_selector — v0.3.1 backward-compat shim. Use tools.output.output_selector."""
import warnings

warnings.warn(
    "tools.pdf.pdf_selector is deprecated; use tools.output.output_selector",
    DeprecationWarning,
    stacklevel=2,
)

from tools.output.reportlab_compose import ReportlabCompose
from tools.output.weasyprint_compose import WeasyprintCompose
from tools.base_tool import BaseTool


class PdfSelector(BaseTool):
    """Backward-compat shim for v0.3.1 PdfSelector. Delegates to output backends."""
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
