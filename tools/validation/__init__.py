"""validation capability family.

Tool modules register when imported by `tools.tool_registry.discover()`.
Keep this package import side-effect free so `python -m tools.validation.*`
does not pre-import the target module.
"""
