"""Tool registry — register tools, query by capability."""
from __future__ import annotations

from collections import defaultdict
import importlib
from typing import Iterable

from tools.base_tool import BaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: list[BaseTool] = []

    def register(self, tool: BaseTool) -> None:
        if not isinstance(tool, BaseTool):
            raise TypeError(f"only BaseTool subclasses can register, got {type(tool)}")
        self._tools.append(tool)

    def tools_by_capability(self, capability: str) -> list[BaseTool]:
        return [t for t in self._tools if t.capability == capability]

    def capability_catalog(self) -> dict[str, list[dict]]:
        cat: dict[str, list[dict]] = defaultdict(list)
        for t in self._tools:
            cat[t.capability].append(t.descriptor())
        return dict(cat)

    def all_tools(self) -> Iterable[BaseTool]:
        return iter(self._tools)

    def discover(self) -> "ToolRegistry":
        """Convenience method — see module-level discover()."""
        # Late binding: at call time the module function exists.
        from tools.tool_registry import discover as _module_discover
        return _module_discover()


# Module-level singleton (most callers use this)
registry = ToolRegistry()


def discover() -> ToolRegistry:
    """Auto-import every tool module so they self-register on import.

    Called by AGENT_GUIDE preflight: `from tools.tool_registry import discover, registry; discover()`.
    """
    modules = [
        "tools.image.codex_image_gen",
        "tools.image.vertex_gemini_image",
        "tools.image.image_selector",
        "tools.image.pillow_split",
        "tools.pdf.reportlab_compose",
        "tools.pdf.weasyprint_compose",
        "tools.pdf.pdf_selector",
        "tools.validation.verify_4k",
        "tools.validation.spec_validate",
        "tools.validation.reference_photo_check",
        "tools.validation.article_validate",
        "tools.meta.scaffold_style",
        "tools.meta.migrate_brand_v1_to_v2",
    ]
    for module in modules:
        importlib.import_module(module)
    return registry
