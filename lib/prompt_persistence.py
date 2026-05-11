"""Persist rendered prompts + a run manifest so issues are reproducible.

Why this exists: ``lib/prompt_builder*.py`` returns prompt strings that get
fed directly to ``image_gen.imagegen`` / ``VertexGeminiImage`` and are then
GC'd. Without persistence we lose the exact text that produced each output
image — making debugging, A/B comparison, audit, and reproducibility all
impossible.

Directors call:

  save_prompt(issue_dir, kind="storyboard", prompt_text=...)
  save_prompt(issue_dir, kind="upscale", prompt_text=..., slot_id="spread-03.feature_hero")
  save_manifest(issue_dir, spec_slug=..., pipeline=..., templates_used={...})

before invoking the paid API call. Files land at:

  output/<slug>/prompts/storyboard.prompt.txt
  output/<slug>/prompts/<head>/<tail>.prompt.txt   # for dotted slot_ids
  output/<slug>/prompts/<slot_id>.prompt.txt       # for flat slot_ids
  output/<slug>/prompts/manifest.json
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import time


def save_prompt(
    issue_dir: pathlib.Path,
    *,
    kind: str,
    prompt_text: str,
    slot_id: str | None = None,
) -> pathlib.Path:
    """Persist a rendered prompt under ``<issue_dir>/prompts/``.

    Args:
      issue_dir: the issue's output root (``output/<slug>``).
      kind: ``"storyboard"`` (single file) or ``"upscale"`` (per-slot file).
      prompt_text: the substituted prompt string ready to send to the model.
      slot_id: required when ``kind="upscale"``. Dotted ids like
        ``"spread-03.feature_hero"`` split on the FIRST dot so each spread
        gets its own subdirectory.

    Returns: the path written.
    """
    base = pathlib.Path(issue_dir) / "prompts"

    if kind == "storyboard":
        out = base / "storyboard.prompt.txt"
    elif kind == "upscale":
        if not slot_id:
            raise ValueError("upscale prompt requires slot_id")
        if "." in slot_id:
            head, tail = slot_id.split(".", 1)
            out = base / head / f"{tail}.prompt.txt"
        else:
            out = base / f"{slot_id}.prompt.txt"
    else:
        raise ValueError(
            f"unknown prompt kind {kind!r}; expected 'storyboard' or 'upscale'"
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prompt_text, encoding="utf-8")
    return out


def save_manifest(
    issue_dir: pathlib.Path,
    *,
    spec_slug: str,
    pipeline: str,
    templates_used: dict[str, str] | None = None,
) -> pathlib.Path:
    """Write ``<issue_dir>/prompts/manifest.json`` with reproducibility metadata.

    Captures: spec slug, pipeline name, git HEAD + dirty state, UTC
    timestamp, and the mapping of role → template path actually used. This
    is enough to ``git checkout <commit>`` and re-run with the same spec to
    reproduce the issue.
    """
    manifest = {
        "spec_slug": spec_slug,
        "pipeline": pipeline,
        "git_commit": _git_head(),
        "git_dirty": _git_dirty(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "templates_used": templates_used or {},
    }
    out = pathlib.Path(issue_dir) / "prompts" / "manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).strip()
    except Exception:
        return "unknown"


def _git_dirty() -> bool:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).strip()
        return bool(out)
    except Exception:
        return False
