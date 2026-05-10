"""prompt_builder — render storyboard / upscale prompts from templates + spec/layers.

Templates live at `library/templates/*.prompt.md`. Each template uses
`{{PLACEHOLDER}}` tokens that `lib.placeholder_resolver.build_placeholder_map`
can fill, plus per-call extras like `{{SCENE}}` for inner / back pages.
"""
from __future__ import annotations

import pathlib

from lib.placeholder_resolver import build_placeholder_map


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES_DIR = SKILL_ROOT / "library" / "templates"


def _read_template(name: str) -> str:
    path = TEMPLATES_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"template not found: {path}")
    return path.read_text(encoding="utf-8")


def _apply(template: str, mapping: dict[str, str]) -> str:
    out = template
    for k, v in mapping.items():
        out = out.replace(k, str(v))
    return out


def build_storyboard_prompt(spec: dict, layers: dict) -> str:
    """Render the storyboard.prompt.md template for the given spec + layers."""
    template = _read_template("storyboard.prompt.md")
    pmap = build_placeholder_map(spec, layers)
    return _apply(template, pmap)


def build_cover_prompt(spec: dict, layers: dict) -> str:
    """Render the cover (page 01) 4K prompt."""
    template = _read_template("upscale_cover.prompt.md")
    pmap = build_placeholder_map(spec, layers)
    return _apply(template, pmap)


def build_inner_prompt(spec: dict, layers: dict, *, scene: str) -> str:
    """Render an inner-page 4K prompt with the given scene description.

    `scene` is per-call — typically the corresponding entry from
    layers['theme'].page_plan_hints, with the leading 'NN: ' prefix stripped.
    """
    template = _read_template("upscale_inner.prompt.md")
    pmap = build_placeholder_map(spec, layers)
    pmap["{{SCENE}}"] = scene
    return _apply(template, pmap)


def build_back_prompt(spec: dict, layers: dict, *, scene: str = "") -> str:
    """Render the back-cover (final page) 4K prompt.

    `scene` is per-call. If empty, the prompt's `{{SCENE}}` token will collapse
    to an empty string and the template's default coda language carries the
    composition.
    """
    template = _read_template("upscale_back.prompt.md")
    pmap = build_placeholder_map(spec, layers)
    pmap["{{SCENE}}"] = scene
    return _apply(template, pmap)


def page_plan_scene_for(layers: dict, page_idx: int) -> str:
    """Helper: pull the `page_plan_hints[page_idx-1]` entry, strip the 'NN: '
    prefix, return the remainder. Returns "" if missing."""
    hints = (layers.get("theme") or {}).get("page_plan_hints") or []
    if page_idx < 1 or page_idx > len(hints):
        return ""
    raw = str(hints[page_idx - 1])
    # Strip leading "NN: " or "NN — " or just "NN " patterns
    import re
    return re.sub(r"^\s*\d+\s*[:\-—]\s*", "", raw).strip()
