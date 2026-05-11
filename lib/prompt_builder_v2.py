"""prompt_builder_v2 — role-driven upscale prompts + multi-aspect storyboard.

For v0.3 editorial pipeline. v0.2 prompt_builder still serves legacy plain-* layouts.
"""
from __future__ import annotations

import pathlib

from lib.placeholder_resolver import build_placeholder_map


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES_DIR = SKILL_ROOT / "library" / "templates"


ROLE_TEMPLATES = {
    "portrait":     "upscale_portrait.prompt.md",
    "scene":        "upscale_scene.prompt.md",
    "environment":  "upscale_environment.prompt.md",
    "detail":       "upscale_detail.prompt.md",
    "cover_hero":   "upscale_cover_hero.prompt.md",
    "back_coda":    "upscale_back_coda.prompt.md",
}


def _read_template(name: str) -> str:
    p = TEMPLATES_DIR / name
    if not p.is_file():
        raise FileNotFoundError(f"template not found: {p}")
    return p.read_text(encoding="utf-8")


def _apply(template: str, mapping: dict[str, str]) -> str:
    out = template
    for k, v in mapping.items():
        out = out.replace(k, str(v))
    return out


def _render_regions_block(ctx: dict) -> str:
    own = ctx["own_region"]
    own_id = own["id"]
    own_rect = own["rect_norm"]
    own_hint = own.get("image_prompt_hint", "")

    lines = [
        f"This image fills region '{own_id}' at rect "
        f"({own_rect[0]:.2f}, {own_rect[1]:.2f}, {own_rect[2]:.2f}, {own_rect[3]:.2f}). "
        f"{own_hint.strip()}",
        "",
        "The same spread contains the following sibling regions that will "
        "receive HTML/PDF overlays after generation. DO NOT paint readable "
        "text or layout chrome into these areas; keep them calm and low-detail:",
        "",
    ]
    for r in ctx.get("sibling_regions", []):
        rid = r["id"]
        rect = r["rect_norm"]
        role = r["role"]
        hint = r.get("image_prompt_hint", "").strip()
        lines.append(
            f"- region '{rid}' (role={role}, rect "
            f"({rect[0]:.2f}, {rect[1]:.2f}, {rect[2]:.2f}, {rect[3]:.2f}))"
            + (f": {hint}" if hint else "")
        )
    return "\n".join(lines)


def build_upscale_prompt(
    *,
    role: str,
    spec: dict,
    layers: dict,
    slot_id: str,
    scene: str,
    aspect: str,
    regions_context: dict | None = None,
) -> str:
    if role not in ROLE_TEMPLATES:
        raise ValueError(f"unknown role {role!r}; expected one of {list(ROLE_TEMPLATES)}")
    template = _read_template(ROLE_TEMPLATES[role])
    pmap = build_placeholder_map(spec, layers)
    pmap["{{SCENE}}"] = scene
    pmap["{{ASPECT}}"] = aspect
    pmap["{{SLOT_ID}}"] = slot_id
    rendered = _apply(template, pmap)

    if regions_context:
        rendered = _render_regions_block(regions_context) + "\n\n" + rendered

    return rendered


def build_storyboard_prompt_v2(
    spec: dict,
    layers: dict,
    *,
    plan: dict,
    scenes_by_slot: dict[str, str],
    regions_by_spread_type: dict[str, list[dict]] | None = None,
    spread_type_by_idx: dict[int, str] | None = None,
) -> str:
    template = _read_template("storyboard_v2.prompt.md")
    pmap = build_placeholder_map(spec, layers)

    role_lookup = _build_role_lookup(layers)
    spread_type_by_idx = spread_type_by_idx or {}
    regions_by_spread_type = regions_by_spread_type or {}

    cell_lines = []
    layouts_seen: dict[int, str] = {}
    for cell in plan["cells"]:
        slot_id = cell["slot_id"]
        scene = scenes_by_slot.get(slot_id, "")
        role = role_lookup.get(slot_id) or role_lookup.get(_short_id(slot_id), "portrait")
        line = (
            f"{cell['page_label']} - {slot_id} "
            f"({cell['aspect']} {role}) - {scene}"
        ).rstrip(" -")
        cell_lines.append(line)
        # Track unique spread indices for layout block
        try:
            spread_idx = int(slot_id.split(".")[0].replace("spread-", ""))
            layouts_seen.setdefault(spread_idx, spread_type_by_idx.get(spread_idx, ""))
        except (ValueError, IndexError):
            pass

    pmap["{{OUTER_W}}"] = str(plan["outer_size_px"][0])
    pmap["{{OUTER_H}}"] = str(plan["outer_size_px"][1])
    pmap["{{GRID_ROWS}}"] = str(plan.get("grid", {}).get("rows", "?"))
    pmap["{{GRID_COLS}}"] = str(plan.get("grid", {}).get("cols", "?"))
    pmap["{{CELL_COUNT}}"] = str(len(plan["cells"]))
    pmap["{{CELL_LIST}}"] = "\n".join(cell_lines)
    pmap["{{SPREAD_LAYOUTS_BLOCK}}"] = _build_spread_layouts_block(
        layouts_seen, regions_by_spread_type
    )

    rendered = _apply(template, pmap)
    # If template doesn't use {{SPREAD_LAYOUTS_BLOCK}}, append at the end
    if pmap["{{SPREAD_LAYOUTS_BLOCK}}"] and "{{SPREAD_LAYOUTS_BLOCK}}" not in template:
        rendered = rendered.rstrip() + "\n\n" + pmap["{{SPREAD_LAYOUTS_BLOCK}}"]
    return rendered


def _build_spread_layouts_block(
    layouts_seen: dict[int, str],
    regions_by_spread_type: dict[str, list[dict]],
) -> str:
    """Render a 'Spread N (type) region layout:' block per unique spread."""
    parts = []
    for spread_idx, spread_type in sorted(layouts_seen.items()):
        if not spread_type or spread_type not in regions_by_spread_type:
            continue
        parts.append(f"Spread {spread_idx} ({spread_type}) region layout:")
        for r in regions_by_spread_type[spread_type]:
            x1, y1, x2, y2 = r["rect_norm"]
            hint = (r.get("image_prompt_hint") or "").strip()
            parts.append(
                f"- '{r['id']}' (role={r['role']}, rect "
                f"({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f}))"
                + (f": {hint}" if hint else "")
            )
        parts.append("")
    return "\n".join(parts).rstrip()


def _short_id(slot_id: str) -> str:
    """'spread-03.feature_hero' -> 'feature_hero' (drop the spread-NN prefix)."""
    return slot_id.split(".", 1)[-1] if "." in slot_id else slot_id


def _build_role_lookup(layers: dict) -> dict[str, str]:
    """Map both full slot_id and short id (no spread- prefix) to role."""
    lookup: dict[str, str] = {}
    for s in layers.get("layout", {}).get("image_slots", []) or []:
        sid = s.get("id", "")
        role = s.get("role", "portrait")
        lookup[sid] = role
        spread_idx = s.get("spread_idx") or s.get("in_spread")
        if spread_idx:
            lookup[f"spread-{int(spread_idx):02d}.{sid}"] = role
    return lookup
