"""config_loader — read config.yaml with environment-variable overrides."""
from __future__ import annotations

import os
import pathlib
from typing import Any

import yaml


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG_PATH = SKILL_ROOT / "config.yaml"


def load_config() -> dict[str, Any]:
    """Load config.yaml. Returns empty dict if file missing."""
    if not CONFIG_PATH.is_file():
        return {}
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def get_parallelism(default: int = 3) -> int:
    """Stage-4 upscale parallelism, hard-capped at 3.

    Resolution order:
      1. env OPENMAGAZINE_PARALLELISM (or OPEN_ZAZHI_PARALLELISM legacy)
      2. config.yaml → defaults.parallelism
      3. default arg

    Vertex Gemini 3 Pro Image emits 503 UNAVAILABLE storms above ~3 concurrent
    calls (empirical, predecessor's experience). Environment overrides can
    reduce parallelism, but values above 3 are clamped to 3.
    """
    env_val = (
        os.environ.get("OPENMAGAZINE_PARALLELISM")
        or os.environ.get("OPEN_ZAZHI_PARALLELISM")
    )
    if env_val:
        try:
            return min(3, max(1, int(env_val)))
        except ValueError:
            pass
    cfg = load_config()
    n = cfg.get("defaults", {}).get("parallelism", default)
    try:
        return min(3, max(1, int(n)))
    except (TypeError, ValueError):
        return default
