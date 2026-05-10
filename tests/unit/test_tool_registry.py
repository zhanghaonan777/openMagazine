"""Tests for tool_registry auto-discovery + capability catalog."""
from tools.tool_registry import ToolRegistry
from tools.base_tool import BaseTool


class FakeImageTool(BaseTool):
    capability = "image_generation"
    provider = "fake"
    cost_per_call_usd = 0.10
    agent_skills = ["fake-skill-doc"]

    def run(self, prompt: str) -> str:
        return f"fake:{prompt}"


def test_register_and_lookup():
    r = ToolRegistry()
    r.register(FakeImageTool())
    tools = r.tools_by_capability("image_generation")
    assert len(tools) == 1
    assert tools[0].provider == "fake"


def test_capability_catalog():
    r = ToolRegistry()
    r.register(FakeImageTool())
    catalog = r.capability_catalog()
    assert "image_generation" in catalog
    assert any(t["provider"] == "fake" for t in catalog["image_generation"])


def test_base_tool_requires_capability():
    """A BaseTool subclass without a capability attribute should fail at import-time."""
    import pytest
    with pytest.raises((TypeError, AttributeError)):
        class BrokenTool(BaseTool):
            pass
        BrokenTool()
