"""output_selector — route compose calls by spec.output_target.

Replaces v0.3.1's pdf_selector.py. Backward-compatible: if invoked with
a `layout={...}` kwarg (old API), routes by `layout.schema_version`.
"""
from __future__ import annotations

from tools.base_tool import BaseTool
from tools.output.reportlab_compose import ReportlabCompose
from tools.output.weasyprint_compose import WeasyprintCompose


class OutputSelector(BaseTool):
    capability = "output_realizer"
    provider = "selector"
    status = "active"

    def __init__(self):
        super().__init__()
        self._reportlab = ReportlabCompose()
        self._weasyprint = WeasyprintCompose()
        # PresentationsAdapter + HtmlInteractiveCompose lazily imported.
        self._presentations = None
        self._html_interactive = None

    def choose_backend(
        self, *, target: dict | None = None, layout: dict | None = None
    ) -> BaseTool:
        # Legacy v0.3.1 API: layout dict with schema_version
        if target is None and layout is not None:
            sv = layout.get("schema_version")
            if sv == 1:
                return self._reportlab
            if sv == 2:
                return self._weasyprint
            raise ValueError(f"unsupported layout.schema_version {sv!r}")

        if target is None:
            return self._weasyprint  # default

        realizer = target.get("realizer")
        if realizer == "weasyprint":
            return self._weasyprint
        if realizer == "reportlab":
            return self._reportlab
        if realizer == "presentations":
            if self._presentations is None:
                from tools.output.presentations_adapter import PresentationsAdapter
                self._presentations = PresentationsAdapter()
            return self._presentations
        if realizer == "html-interactive":
            if self._html_interactive is None:
                from tools.output.html_interactive_compose import HtmlInteractiveCompose
                self._html_interactive = HtmlInteractiveCompose()
            return self._html_interactive
        raise ValueError(f"unknown realizer {realizer!r}")

    def run(self, *, target: dict | None = None, layout: dict | None = None, **kwargs):
        return self.choose_backend(target=target, layout=layout).run(**kwargs)


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(OutputSelector())
