"""Codex CLI native image_gen.imagegen wrapper.

This tool does NOT directly call image_gen.imagegen — that's done by the
Codex agent itself. The tool's role is:

1. Snapshot ~/.codex/generated_images/ BEFORE the call (record state)
2. After agent triggers image_gen.imagegen, the agent passes the
   pre-recorded BEFORE-marker to capture_new_png() which:
   - Looks for a new PNG in ~/.codex/generated_images/
   - Validates it's truly new (not the BEFORE)
   - Copies it to the issue's storyboard.png path

Used in the storyboard-director skill flow.
"""
from __future__ import annotations

import pathlib
import shutil
import time
from typing import Optional

from tools.base_tool import BaseTool


CODEX_GEN_DIR = pathlib.Path.home() / ".codex" / "generated_images"


class CodexImageGen(BaseTool):
    capability = "image_generation"
    provider = "codex"
    cost_per_call_usd = 0.04   # rough estimate; depends on codex plan
    agent_skills = ["codex-image-gen-plumbing"]
    status = "active"

    def run(self, *, mode: str = "storyboard") -> dict:
        """Returns a "before snapshot" dict the caller will use after the
        actual image_gen.imagegen tool call.

        Note: the tool can't call image_gen.imagegen itself — that's a
        Codex-level tool, only the agent loop has access. This run()
        prepares the BEFORE state.
        """
        if mode != "storyboard":
            raise ValueError(f"CodexImageGen only supports mode='storyboard', got {mode!r}")
        return {"before_path": _latest_png(), "ts": time.time()}

    def capture_new_png(
        self,
        before_state: dict,
        out_path: pathlib.Path,
        *,
        timeout_seconds: int = 5,
    ) -> pathlib.Path:
        """After the agent has triggered image_gen.imagegen, copy the new
        PNG that landed in ~/.codex/generated_images/ to `out_path`.

        Raises RuntimeError if no new PNG appears within timeout_seconds.
        """
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            after = _latest_png()
            if after and after != before_state.get("before_path"):
                out_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(after, out_path)
                return out_path
            time.sleep(0.5)
        raise RuntimeError(
            f"image_gen.imagegen produced no new file in {timeout_seconds}s. "
            f"BEFORE was {before_state.get('before_path')}; "
            f"current latest is {_latest_png()}. "
            f"DO NOT fallback to PIL — STOP and report to user."
        )


def _latest_png() -> Optional[pathlib.Path]:
    """Returns the most recent PNG under ~/.codex/generated_images/<uuid>/ig_*.png,
    or None if none exists."""
    if not CODEX_GEN_DIR.is_dir():
        return None
    candidates = list(CODEX_GEN_DIR.glob("*/ig_*.png"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(CodexImageGen())
