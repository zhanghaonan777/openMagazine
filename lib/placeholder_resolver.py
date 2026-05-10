"""placeholder_resolver — build the {{TOKEN}} → value map from spec + 5 layers."""
from __future__ import annotations

import re
import time
from typing import Any


def build_placeholder_map(spec: dict, layers: dict) -> dict[str, str]:
    """Apply the priority order: spec.overrides > spec.<field> > layer yaml."""
    overrides = spec.get("overrides") or {}

    subject = layers["subject"]
    theme = layers["theme"]
    brand = layers["brand"]
    style = layers["style"]

    # Protagonist name
    protagonist_name = (
        subject.get("display_name", {}).get("en")
        or subject.get("name", "Luna")
    )

    # Issue number
    issue_number = (
        spec.get("issue_number")
        or _last_digits(spec.get("slug", ""))
        or "01"
    )

    # Date
    date = spec.get("date") or time.strftime("%B %Y").upper()

    # Cover line: overrides > theme.default_cover_line.en (with PROTAGONIST_NAME substitution)
    cover_line = overrides.get("cover_line")
    if not cover_line:
        cover_line_template = theme.get("default_cover_line", {}).get("en", "")
        cover_line = cover_line_template.replace("{{PROTAGONIST_NAME}}", protagonist_name)

    # Magazine name (masthead)
    masthead = overrides.get("masthead") or brand.get("masthead", "")

    # Layout-derived placeholders
    layout = layers.get("layout") or {}
    storyboard_grid = layout.get("storyboard_grid", "2x2")
    rows, cols = _parse_grid(storyboard_grid)
    page_count = layout.get("page_count", rows * cols)

    # Theme-derived: page plan block
    hints = theme.get("page_plan_hints") or []
    page_plan_block = _render_page_plan_block(hints)

    return {
        "{{TRAITS}}": subject.get("traits", ""),
        "{{STYLE_ANCHOR}}": (style or {}).get("style_anchor", ""),
        "{{THEME_WORLD}}": theme.get("theme_world", ""),
        "{{MAGAZINE_NAME}}": masthead,
        "{{COVER_LINE}}": cover_line,
        "{{PROTAGONIST_NAME}}": protagonist_name,
        "{{ISSUE_NUMBER}}": issue_number,
        "{{DATE}}": date,
        "{{GRID_ROWS}}": str(rows),
        "{{GRID_COLS}}": str(cols),
        "{{PAGE_COUNT}}": str(page_count),
        "{{PAGE_NUMBER_RANGE}}": f"01-{int(page_count):02d}",
        "{{PAGE_PLAN_BLOCK}}": page_plan_block,
    }


def _last_digits(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"(\d+)$", text)
    return m.group(1) if m else ""


def _parse_grid(grid_str: str) -> tuple[int, int]:
    """Parse '2x2' / '3x3' / '4x4' → (rows, cols). Accepts '×' too."""
    parts = str(grid_str).lower().replace("×", "x").split("x")
    if len(parts) != 2:
        raise ValueError(f"storyboard_grid {grid_str!r} must be 'NxM'")
    return int(parts[0]), int(parts[1])


def _render_page_plan_block(hints: list[str]) -> str:
    """Format page_plan_hints as a multi-line block.

    Hints are expected to start with "NN: " — e.g. "01: cover hero ...".
    Render each hint on its own line, preserving the prefix. Strip trailing
    whitespace per line. If a hint is missing the prefix, leave as-is.
    """
    if not hints:
        return ""
    return "\n".join(str(h).rstrip() for h in hints)
