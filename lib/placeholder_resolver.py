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

    return {
        "{{TRAITS}}": subject.get("traits", ""),
        "{{STYLE_ANCHOR}}": (style or {}).get("style_anchor", ""),
        "{{THEME_WORLD}}": theme.get("theme_world", ""),
        "{{MAGAZINE_NAME}}": masthead,
        "{{COVER_LINE}}": cover_line,
        "{{PROTAGONIST_NAME}}": protagonist_name,
        "{{ISSUE_NUMBER}}": issue_number,
        "{{DATE}}": date,
    }


def _last_digits(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"(\d+)$", text)
    return m.group(1) if m else ""
