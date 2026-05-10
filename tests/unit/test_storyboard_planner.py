"""Tests for storyboard_planner."""
import pytest

from lib.storyboard_planner import plan_storyboard


def test_plan_basic_4_slots():
    slots = [
        {"id": "spread-01.cover_hero",   "role": "cover_hero", "aspect": "3:4", "spread_idx": 1},
        {"id": "spread-03.feature_hero", "role": "portrait",   "aspect": "3:4", "spread_idx": 3},
        {"id": "spread-03.feature_captioned.1", "role": "scene", "aspect": "3:2", "spread_idx": 3},
        {"id": "spread-09.back_coda",    "role": "back_coda",  "aspect": "2:3", "spread_idx": 9},
    ]
    plan = plan_storyboard(slots, outer_aspect="2:3")
    assert plan["outer_aspect"] == "2:3"
    assert plan["outer_size_px"] == [1024, 1536]
    assert len(plan["cells"]) == 4
    slot_ids = {c["slot_id"] for c in plan["cells"]}
    assert slot_ids == {s["id"] for s in slots}


def test_plan_21_slots_packs_into_grid():
    """Editorial-16page has 21 slots — they all fit in 1024x1536."""
    slots = [
        {"id": f"slot.{i}", "role": "portrait", "aspect": "1:1", "spread_idx": (i // 6) + 1}
        for i in range(21)
    ]
    plan = plan_storyboard(slots)
    assert len(plan["cells"]) == 21
    bboxes = [tuple(c["bbox_px"]) for c in plan["cells"]]
    assert len(set(bboxes)) == 21


def test_cells_have_required_keys():
    slots = [{"id": "s.1", "role": "portrait", "aspect": "1:1", "spread_idx": 1}]
    plan = plan_storyboard(slots)
    cell = plan["cells"][0]
    for k in ("slot_id", "row", "col", "rowspan", "colspan", "aspect", "bbox_px", "page_label"):
        assert k in cell, f"missing key {k}"


def test_grid_proportional_to_outer_aspect():
    """Grid must keep cell aspect close to 1:1 (rows/cols ~ 1.5 since outer
    is 2:3 portrait). Otherwise cells degenerate to thin stripes that the
    storyboard model can't render meaningfully.

    Deviation from plan: plan's algorithm starts cols=1 with breakpoint
    rows >= cols, which trivially terminates at cols=1, producing 21x1 for
    n=21. We pick the rows*cols >= n grid that minimizes |rows/cols - 1.5|,
    which matches spec §7.1's example of 6x4 for n=21.
    """
    expected = {
        4:  (2, 2),   # cells 512x768
        9:  (3, 3),   # cells 341x512
        16: (4, 4),   # cells 256x384
        21: (6, 4),   # cells 256x256 — matches spec §7.1
    }
    for n, (exp_rows, exp_cols) in expected.items():
        slots = [{"id": f"s.{i}", "role": "p", "aspect": "1:1", "spread_idx": 1}
                 for i in range(n)]
        plan = plan_storyboard(slots)
        rows = plan["grid"]["rows"]
        cols = plan["grid"]["cols"]
        cell_w = 1024 // cols
        cell_h = 1536 // rows
        ratio = cell_w / cell_h
        assert 0.5 <= ratio <= 2.0, (
            f"n={n} produced {rows}x{cols} grid with cell aspect {ratio:.2f} "
            f"(cell {cell_w}x{cell_h}) — too skewed"
        )
        assert rows * cols >= n, f"grid {rows}x{cols} can't hold {n} slots"
        assert (rows, cols) == (exp_rows, exp_cols), (
            f"n={n}: expected {exp_rows}x{exp_cols} grid, got {rows}x{cols}"
        )


def test_empty_slots_returns_empty_cells():
    plan = plan_storyboard([])
    assert plan["cells"] == []


def test_unsupported_outer_aspect_raises():
    with pytest.raises(ValueError, match="2:3"):
        plan_storyboard([{"id": "s", "role": "p", "aspect": "1:1", "spread_idx": 1}],
                        outer_aspect="16:9")
