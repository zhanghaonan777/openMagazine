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
    """Auto-import every tool module under tools/ so they self-register.

    Walks the `tools` package recursively and imports each leaf module that
    isn't infrastructure (`base_tool`, `tool_registry`, `__init__`). Replaces
    the v0.1 hand-maintained module list which drifted as new families were
    added (`tools/output/` in v0.3.2, `tools/validation/scorecard_validate.py`
    in v0.3.2.1) and as `tools/pdf/{reportlab,weasyprint}_compose.py` moved
    to `tools/output/`.

    Called by AGENT_GUIDE preflight:
    `from tools.tool_registry import discover, registry; discover()`.
    """
    import pathlib
    import pkgutil

    import tools as tools_pkg

    tools_root = pathlib.Path(tools_pkg.__file__).parent
    skip_leaves = {"base_tool", "tool_registry"}

    for module_info in pkgutil.walk_packages(
        path=[str(tools_root)],
        prefix="tools.",
    ):
        if module_info.ispkg:
            continue
        leaf = module_info.name.rsplit(".", 1)[-1]
        if leaf in skip_leaves:
            continue
        importlib.import_module(module_info.name)
    return registry
