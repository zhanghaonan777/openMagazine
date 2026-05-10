"""Tool registry — register tools, query by capability."""
from __future__ import annotations

from collections import defaultdict
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


# Module-level singleton (most callers use this)
registry = ToolRegistry()


def discover() -> ToolRegistry:
    """Auto-import every tool module so they self-register on import.

    Called by AGENT_GUIDE preflight: `from tools.tool_registry import discover, registry; discover()`.
    """
    # Each tool module's __init__.py registers its tool(s) on import.
    # We import each capability-family package; their __init__.py does the work.
    import tools.image  # noqa: F401
    import tools.pdf  # noqa: F401
    import tools.validation  # noqa: F401
    import tools.meta  # noqa: F401
    return registry
