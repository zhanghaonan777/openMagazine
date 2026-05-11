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

    # Theme-derived: page plan block + optional overlay layout contracts
    hints = theme.get("page_plan_hints") or []
    page_plan_block = _render_page_plan_block(hints)
    page_contract_block = _render_page_contract_block(
        theme.get("page_overlay_contracts") or []
    )

    pmap = {
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
        "{{PAGE_CONTRACT_BLOCK}}": page_contract_block,
    }

    # v0.3 brand schema_version 2: typography pack + visual tokens.
    # v1 brands have no `typography` / `visual_tokens` keys; the values fall
    # back to "" so prompts using these placeholders won't end up with
    # literal `{{...}}` tokens.
    typography = brand.get("typography") or {}
    visual_tokens = brand.get("visual_tokens") or {}
    pmap["{{TYPOGRAPHY_DISPLAY_FAMILY}}"] = (
        typography.get("display", {}).get("family", "")
    )
    pmap["{{TYPOGRAPHY_BODY_FAMILY}}"] = (
        typography.get("body", {}).get("family", "")
    )
    pmap["{{TYPOGRAPHY_PAIRING_HINT}}"] = (
        typography.get("pairing_notes", "").strip()
    )
    pmap["{{COLOR_ACCENT}}"] = visual_tokens.get("color_accent", "")
    pmap["{{COLOR_BG_PAPER}}"] = visual_tokens.get("color_bg_paper", "")

    return pmap


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


def _render_page_contract_block(contracts: list[dict]) -> str:
    """Format page-level image/HTML overlay contracts for storyboard prompts."""
    if not contracts:
        return (
            "No page-specific overlay contracts supplied. Preserve natural "
            "negative space and keep important subject features away from "
            "areas likely to receive later typography or HTML overlays."
        )
    return "\n\n".join(
        _render_overlay_contract(c, fallback_page=i + 1)
        for i, c in enumerate(contracts)
    )


def page_overlay_contract_text(layers: dict, page_idx: int) -> str:
    """Return a per-page overlay contract for 4K prompts.

    Contracts live at `theme.page_overlay_contracts` and are optional. The
    text is intentionally plain prompt language so both image generation and
    later HTML composition can share the same layout vocabulary.
    """
    if page_idx < 1:
        return (
            "No explicit overlay contract. Keep the subject's face, eyes, "
            "primary object, and readable details clear of any natural "
            "negative-space areas that may receive later HTML/PDF overlays. "
            "Do not generate readable captions, UI boxes, or fake magazine "
            "layout elements."
        )
    theme = layers.get("theme") or {}
    contracts = theme.get("page_overlay_contracts") or []
    for i, contract in enumerate(contracts):
        if int(contract.get("page", i + 1)) == page_idx:
            return _render_overlay_contract(contract, fallback_page=page_idx)
    return (
        f"Page {page_idx:02d}: No explicit overlay contract. Keep the subject's "
        "face, eyes, primary object, and readable details clear of any natural "
        "negative-space areas that may receive later HTML/PDF overlays. Do not "
        "generate readable captions, UI boxes, or fake magazine layout elements."
    )


def _render_overlay_contract(contract: dict, *, fallback_page: int) -> str:
    page = int(contract.get("page", fallback_page))
    lines = [f"Page {page:02d} overlay/layout contract:"]
    fields = [
        ("subject_zone", "subject zone"),
        ("protected_zones", "protected zones"),
        ("reserved_overlay_zones", "reserved overlay zones"),
        ("negative_space", "negative space to preserve"),
        ("html_components", "later HTML components"),
        ("forbidden", "forbidden overlaps"),
        ("image_prompt_notes", "image prompt notes"),
    ]
    for key, label in fields:
        if key in contract and contract[key] not in (None, "", []):
            lines.append(f"- {label}: {_format_contract_value(contract[key])}")
    lines.append(
        "- hard rule: reserved overlay zones must stay visually calm; protected "
        "zones must not be crossed by cards, lines, titles, or dense props."
    )
    return "\n".join(lines)


def _format_contract_value(value) -> str:
    if isinstance(value, list):
        return "; ".join(_format_contract_value(v) for v in value)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            parts.append(f"{k}={_format_contract_value(v)}")
        return "{" + ", ".join(parts) + "}"
    return str(value)
