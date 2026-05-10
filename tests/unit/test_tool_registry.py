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


def test_tools_by_capability_unknown_returns_empty():
    r = ToolRegistry()
    r.register(FakeImageTool())
    assert r.tools_by_capability("nonexistent") == []


def test_register_rejects_non_basetool():
    import pytest
    r = ToolRegistry()
    with pytest.raises(TypeError):
        r.register("not a tool")


def test_descriptor_shape():
    t = FakeImageTool()
    d = t.descriptor()
    assert set(d.keys()) == {
        "name", "capability", "provider",
        "cost_per_call_usd", "agent_skills", "status",
    }
    assert d["name"] == "FakeImageTool"
    assert d["capability"] == "image_generation"
    assert d["provider"] == "fake"
    assert d["cost_per_call_usd"] == 0.10
    assert d["agent_skills"] == ["fake-skill-doc"]
    assert d["status"] == "active"


def test_registry_discover_method_works():
    """registry.discover() should work (in addition to module-level discover())."""
    from tools.tool_registry import registry as global_registry
    result = global_registry.discover()
    assert result is global_registry  # discover() returns the singleton


def test_agent_skills_instances_isolated():
    """Mutating one instance's agent_skills must not affect another instance or the class."""
    a = FakeImageTool()
    b = FakeImageTool()
    a.agent_skills.append("dynamic-skill")
    assert "dynamic-skill" in a.agent_skills
    assert "dynamic-skill" not in b.agent_skills
    assert "dynamic-skill" not in FakeImageTool.agent_skills
