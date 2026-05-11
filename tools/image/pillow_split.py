"""pillow_split — N×M cell extraction from a storyboard PNG.

Used in Stage 3 (storyboard-director). The agent passes the storyboard PNG
and the layout's storyboard_grid + top_crop_px_default.
"""
from __future__ import annotations

import pathlib
import sys

from tools.base_tool import BaseTool


class PillowSplit(BaseTool):
    capability = "image_processing"
    provider = "pillow"
    status = "active"

    def run(
        self,
        storyboard_path: pathlib.Path,
        out_dir: pathlib.Path,
        *,
        rows: int = 4,
        cols: int = 4,
        gutter: "str | int" = "auto",
        top_crop_px: int = 0,
    ) -> int:
        return split_storyboard(
            storyboard_path, out_dir,
            rows=rows, cols=cols, gutter=gutter, top_crop_px=top_crop_px,
        )


def split_storyboard(
    storyboard_path: pathlib.Path,
    out_dir: pathlib.Path,
    *,
    rows: int = 4,
    cols: int = 4,
    gutter: "str | int" = "auto",
    top_crop_px: int = 0,
) -> int:
    """Split an N×M grid storyboard PNG into individual cell files."""
    from PIL import Image

    img = Image.open(storyboard_path)
    W, H = img.size
    outer_ratio = W / H
    if abs(outer_ratio - 2 / 3) > 0.10:
        print(
            f"[pillow_split] WARNING: storyboard outer aspect {outer_ratio:.3f} "
            f"deviates from 2:3 (0.667). Cells will inherit the wrong aspect. "
            f"Storyboard prompt likely missed the OUTPUT IMAGE FORMAT constraint.",
            file=sys.stderr,
        )
    g = max(8, W // 200) if gutter == "auto" else int(gutter)
    cell_w = (W - (cols + 1) * g) // cols
    cell_h = (H - (rows + 1) * g) // rows

    if top_crop_px < 0:
        raise ValueError(f"top_crop_px must be >= 0, got {top_crop_px}")
    if top_crop_px >= cell_h:
        raise ValueError(
            f"top_crop_px {top_crop_px} >= cell_h {cell_h} would crop entire cell"
        )

    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i in range(cols * rows):
        row, col = divmod(i, cols)
        x = g + col * (cell_w + g)
        y = g + row * (cell_h + g)
        cell = img.crop((x, y + top_crop_px, x + cell_w, y + cell_h))
        cell.save(out_dir / f"cell-{i+1:02d}.png")

    crop_note = f", top-cropped {top_crop_px}px" if top_crop_px else ""
    print(
        f"[pillow_split] {rows}×{cols} = {rows*cols} cells "
        f"({cell_w}×{cell_h - top_crop_px} each, gutter={g}px{crop_note}) → {out_dir}",
        file=sys.stderr,
    )
    return rows * cols


def split_by_plan(
    storyboard_path: pathlib.Path,
    out_dir: pathlib.Path,
    *,
    plan: dict,
) -> int:
    """Split a storyboard into per-slot cell PNGs using a plan from
    `lib.storyboard_planner.plan_storyboard`. Each cell is saved at
    {out_dir}/{spread-NN}/{slot}.png if its slot_id contains ".",
    otherwise at {out_dir}/{slot_id}.png.

    Returns count of files written.
    """
    from PIL import Image

    img = Image.open(storyboard_path)
    W, H = img.size
    outer_ratio = W / H
    if abs(outer_ratio - 2 / 3) > 0.10:
        print(
            f"[pillow_split.split_by_plan] WARNING: storyboard outer aspect "
            f"{outer_ratio:.3f} deviates from 2:3 (0.667). Planned cells "
            f"will inherit the wrong aspect.",
            file=sys.stderr,
        )
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for cell in plan["cells"]:
        x, y, w, h = cell["bbox_px"]
        crop = img.crop((x, y, x + w, y + h))
        slot_id = cell["slot_id"]  # e.g. "spread-03.feature_hero"
        if "." in slot_id:
            head, tail = slot_id.split(".", 1)
            sub = out_dir / head
            sub.mkdir(parents=True, exist_ok=True)
            out_path = sub / f"{tail}.png"
        else:
            out_path = out_dir / f"{slot_id}.png"
        crop.save(out_path)
        count += 1

    print(
        f"[pillow_split.split_by_plan] {count} cells → {out_dir}",
        file=sys.stderr,
    )
    return count


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(PillowSplit())
