"""scaffold_style — placeholder; actual logic is in skills/meta/scaffold-style.md.

The agent reads scaffold-style.md as a meta-protocol skill, runs WebSearch
itself, and produces the new style yaml. This BaseTool subclass exists
to declare the capability for the registry; it doesn't do anything at
runtime in v0.1.

In Batch 2, this could become an actual orchestrator that the agent
invokes to drive the scaffold protocol step-by-step.
"""
from __future__ import annotations

from tools.base_tool import BaseTool


class ScaffoldStyle(BaseTool):
    capability = "meta"
    provider = "agent-driven"
    status = "experimental"
    agent_skills = []

    def run(self, *args, **kwargs):
        raise NotImplementedError(
            "scaffold_style.py is a registry placeholder. "
            "Read skills/meta/scaffold-style.md and execute the protocol agent-side."
        )


# Auto-register so capability_catalog shows it
from tools.tool_registry import registry  # noqa: E402

registry.register(ScaffoldStyle())
