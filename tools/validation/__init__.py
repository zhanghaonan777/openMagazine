"""validation capability family.

Tool modules register when imported by `tools.tool_registry.discover()`.
Keep this package import side-effect free so `python -m tools.validation.*`
does not pre-import the target module.
"""
from tools.validation import regions_validate  # noqa: F401
from tools.validation import design_system_validate  # noqa: F401
