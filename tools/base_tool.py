"""BaseTool — abstract contract every tool subclasses."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Tools declare capability, provider, cost, and agent_skills.

    Subclasses MUST set:
      - capability: str  (one of "image_generation", "pdf_compose",
                          "validation", "meta")
      - provider: str    (e.g., "vertex", "codex", "reportlab")
    Subclasses MAY set:
      - cost_per_call_usd: float (default 0)
      - agent_skills: list[str]  (Layer 3 doc names; default [])
      - status: str              ("active" | "experimental" | "deprecated")
    """

    capability: str
    provider: str = "unknown"
    cost_per_call_usd: float = 0.0
    agent_skills: list[str] = []
    status: str = "active"

    def __init__(self):
        if not getattr(type(self), "capability", None):
            raise AttributeError(
                f"{type(self).__name__} must declare a 'capability' class attribute"
            )

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        ...

    def descriptor(self) -> dict:
        return {
            "name": type(self).__name__,
            "capability": self.capability,
            "provider": self.provider,
            "cost_per_call_usd": self.cost_per_call_usd,
            "agent_skills": list(self.agent_skills),
            "status": self.status,
        }
