"""ImageSelector — routes to the right backend by mode.

Modes:
  storyboard   → CodexImageGen  (Stage 3; codex CLI required)
  upscale_4k   → VertexGeminiImage  (Stage 4 / Stage 5 cover/back)
"""
from __future__ import annotations

import pathlib
from typing import Any

from tools.base_tool import BaseTool
from tools.image.codex_image_gen import CodexImageGen
from tools.image.vertex_gemini_image import VertexGeminiImage


class ImageSelector(BaseTool):
    capability = "image_generation"
    provider = "selector"
    status = "active"

    def __init__(self):
        super().__init__()
        self._codex = CodexImageGen()
        self._vertex = VertexGeminiImage()

    def choose_backend(self, *, mode: str) -> BaseTool:
        if mode == "storyboard":
            return self._codex
        elif mode == "upscale_4k":
            return self._vertex
        else:
            raise ValueError(
                f"unknown mode {mode!r}; expected 'storyboard' or 'upscale_4k'"
            )

    def run(self, *, mode: str, **kwargs) -> Any:
        return self.choose_backend(mode=mode).run(**kwargs)


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(ImageSelector())
