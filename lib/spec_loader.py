"""spec_loader — load and resolve a spec yaml against the 5 library layers."""
from __future__ import annotations

import pathlib
from typing import Any

import yaml


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
LIBRARY_DIR = SKILL_ROOT / "library"
STYLES_DIR = SKILL_ROOT / "styles"


def load_spec(spec_path: pathlib.Path) -> tuple[dict, pathlib.Path]:
    spec_path = pathlib.Path(spec_path).resolve()
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    return spec, spec_path.parent


def resolve_layers(spec: dict) -> dict:
    """Return a dict with subject/style/theme/layout/brand yaml content keyed
    by layer name. Style is allowed to be absent (Tier 2 fallback at runtime)."""
    result = {}
    for layer in ("subject", "theme", "layout", "brand"):
        ref_name = spec[layer]
        path = LIBRARY_DIR / f"{layer}s" / f"{ref_name}.yaml"
        result[layer] = yaml.safe_load(path.read_text(encoding="utf-8"))

    style_name = spec["style"]
    style_path = STYLES_DIR / f"{style_name}.yaml"
    if style_path.is_file():
        result["style"] = yaml.safe_load(style_path.read_text(encoding="utf-8"))
    else:
        result["style"] = None  # Tier 2 fallback at runtime

    return result
