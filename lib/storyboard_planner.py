"""storyboard_planner — pack heterogeneous-aspect image slots into a grid.

Greedy uniform grid: pick the smallest (rows, cols) such that rows*cols >= n
AND rows/cols ≈ outer_h/outer_w (so cells stay close to square / their slot's
intended aspect). Slots fill row-major.

For v0.3.1+ we may upgrade to a true bin-pack with rowspan/colspan that
honors each slot's declared aspect more precisely.
"""
from __future__ import annotations

import math


OUTER_W_PX = 1024
OUTER_H_PX = 1536  # 2:3 portrait

# Outer aspect h/w for the default canvas. Used to keep cells roughly square
# by aiming for rows/cols ≈ OUTER_RATIO.
OUTER_RATIO = OUTER_H_PX / OUTER_W_PX  # 1.5


def _choose_grid(n: int) -> tuple[int, int]:
    """Find the smallest grid (rows, cols) with:
      - rows * cols >= n
      - rows / cols within [OUTER_RATIO/2, OUTER_RATIO*2] so cells aren't
        wildly skewed (cell aspect stays in [0.5, 2.0]).

    Iterate cols from 1 upward; for each cols pick the smallest rows that
    fits n. Among feasible (rows, cols) pairs, return the one minimizing
    leftover empty cells (rows*cols - n), breaking ties by preferring
    rows/cols closer to OUTER_RATIO.
    """
    best = None
    for cols in range(1, n + 1):
        rows = math.ceil(n / cols)
        # Cell aspect must stay in [0.5, 2.0]
        cell_w = OUTER_W_PX / cols
        cell_h = OUTER_H_PX / rows
        cell_ratio = cell_w / cell_h
        if not (0.5 <= cell_ratio <= 2.0):
            continue
        leftover = rows * cols - n
        ratio_err = abs((rows / cols) - OUTER_RATIO)
        # Prioritize matching outer aspect ratio so cells stay close to
        # square (matching the typical portrait/square slot intent), then
        # minimize leftover empty cells.
        score = (ratio_err, leftover)
        if best is None or score < best[0]:
            best = (score, rows, cols)
    if best is None:
        # No grid satisfied the cell-aspect bound; fall back to the closest.
        cols = max(1, round(math.sqrt(n / OUTER_RATIO)))
        rows = math.ceil(n / cols)
        return rows, cols
    return best[1], best[2]


def plan_storyboard(slots: list[dict], outer_aspect: str = "2:3") -> dict:
    """Pack slots into an outer-aspect-2:3 portrait grid.

    Args:
      slots: each {id, role, aspect, spread_idx, ...}
      outer_aspect: overall storyboard aspect; only "2:3" supported in v0.3.0

    Returns:
      {outer_aspect, outer_size_px, grid: {rows, cols},
       cells: [{slot_id, row, col, rowspan, colspan, aspect, bbox_px, page_label}, ...]}
    """
    if outer_aspect != "2:3":
        raise ValueError(f"only '2:3' outer_aspect supported, got {outer_aspect!r}")

    n = len(slots)
    if n == 0:
        return {
            "outer_aspect": outer_aspect,
            "outer_size_px": [OUTER_W_PX, OUTER_H_PX],
            "grid": {"rows": 0, "cols": 0},
            "cells": [],
        }

    rows, cols = _choose_grid(n)
    cell_w = OUTER_W_PX // cols
    cell_h = OUTER_H_PX // rows

    cells = []
    for i, slot in enumerate(slots):
        row = i // cols
        col = i % cols
        x = col * cell_w
        y = row * cell_h
        cells.append({
            "slot_id": slot["id"],
            "row": row,
            "col": col,
            "rowspan": 1,
            "colspan": 1,
            "aspect": slot.get("aspect", "1:1"),
            "bbox_px": [x, y, cell_w, cell_h],
            "page_label": f"{i + 1:02d}",
        })

    return {
        "outer_aspect": outer_aspect,
        "outer_size_px": [OUTER_W_PX, OUTER_H_PX],
        "grid": {"rows": rows, "cols": cols},
        "cells": cells,
    }
