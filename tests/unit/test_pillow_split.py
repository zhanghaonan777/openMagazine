"""Tests for vertex_image.split_storyboard — Phase 2 cell crop."""
from pathlib import Path
from PIL import Image

from tools.image.pillow_split import split_storyboard


def _make_fake_storyboard(path: Path, rows: int, cols: int,
                          cell_w: int, cell_h: int, gutter: int) -> list[tuple]:
    """Build an N×M grid PNG with each cell painted a unique solid color.
    Returns the list of expected colors in row-major order."""
    W = cols * cell_w + (cols + 1) * gutter
    H = rows * cell_h + (rows + 1) * gutter
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    expected = []
    for i in range(rows * cols):
        row, col = divmod(i, cols)
        x = gutter + col * (cell_w + gutter)
        y = gutter + row * (cell_h + gutter)
        color = ((i * 16 + 5) % 256, (i * 32 + 5) % 256, (i * 64 + 5) % 256)
        expected.append(color)
        cell = Image.new("RGB", (cell_w, cell_h), color=color)
        img.paste(cell, (x, y))
    img.save(path)
    return expected


def test_split_4x4_with_explicit_gutter(tmp_path):
    sb = tmp_path / "sb.png"
    expected = _make_fake_storyboard(sb, rows=4, cols=4,
                                     cell_w=120, cell_h=180, gutter=10)

    out_dir = tmp_path / "cells"
    n = split_storyboard(sb, out_dir, rows=4, cols=4, gutter=10)

    assert n == 16
    files = sorted(out_dir.glob("cell-*.png"))
    assert [f.name for f in files] == [f"cell-{i+1:02d}.png" for i in range(16)]
    # Verify each cell's center pixel matches its expected color
    for i, f in enumerate(files):
        with Image.open(f) as img:
            cw, ch = img.size
            center = img.getpixel((cw // 2, ch // 2))
        assert center == expected[i], (
            f"cell-{i+1:02d}.png center {center} != expected {expected[i]}"
        )


def test_split_auto_gutter(tmp_path):
    """auto gutter = max(8, W // 200). Just verify it runs and produces 16 files."""
    sb = tmp_path / "sb.png"
    _make_fake_storyboard(sb, rows=4, cols=4, cell_w=200, cell_h=300, gutter=8)

    out_dir = tmp_path / "cells"
    n = split_storyboard(sb, out_dir, rows=4, cols=4, gutter="auto")

    assert n == 16
    assert len(list(out_dir.glob("cell-*.png"))) == 16


def test_split_3x4_grid(tmp_path):
    """Non-4x4 grids work too (e.g., 3 rows × 4 cols = 12 cells)."""
    sb = tmp_path / "sb.png"
    _make_fake_storyboard(sb, rows=3, cols=4, cell_w=100, cell_h=150, gutter=8)

    out_dir = tmp_path / "cells"
    n = split_storyboard(sb, out_dir, rows=3, cols=4, gutter=8)

    assert n == 12
    files = sorted(out_dir.glob("cell-*.png"))
    assert files[-1].name == "cell-12.png"


def test_split_top_crop_removes_top_band(tmp_path):
    """top_crop_px deterministically crops N pixels off each cell's top.

    Use case: storyboard cells from image_gen.imagegen have page-number
    labels (01-04) baked into the top-left. Cropping the top band
    removes them before the cell becomes a Phase 3 4K composition ref.
    """
    from PIL import Image

    sb = tmp_path / "sb.png"
    _make_fake_storyboard(sb, rows=2, cols=2, cell_w=100, cell_h=200, gutter=8)

    out_dir = tmp_path / "cells"
    n = split_storyboard(sb, out_dir, rows=2, cols=2, gutter=8, top_crop_px=20)

    assert n == 4
    files = sorted(out_dir.glob("cell-*.png"))
    assert len(files) == 4

    # Each cell now has height (200 - 20) = 180; width unchanged
    with Image.open(files[0]) as img:
        cw, ch = img.size
    assert cw == 100, f"width should be unchanged, got {cw}"
    assert ch == 180, f"top_crop_px=20 should reduce height by 20, got {ch}"


def test_split_top_crop_zero_default_unchanged(tmp_path):
    """top_crop_px=0 (default) preserves the existing behavior exactly."""
    from PIL import Image

    sb = tmp_path / "sb.png"
    _make_fake_storyboard(sb, rows=2, cols=2, cell_w=100, cell_h=200, gutter=8)

    out_dir = tmp_path / "cells"
    split_storyboard(sb, out_dir, rows=2, cols=2, gutter=8)  # no top_crop_px

    with Image.open(sorted(out_dir.glob("cell-*.png"))[0]) as img:
        cw, ch = img.size
    assert (cw, ch) == (100, 200), "default behavior should not crop"


def test_split_warns_on_wrong_outer_aspect(tmp_path, capsys):
    """Storyboard not in 2:3 portrait should emit an aspect warning."""
    from PIL import Image
    sb = tmp_path / "square_sb.png"
    Image.new("RGB", (1200, 1200), color="white").save(sb)  # square
    out_dir = tmp_path / "cells"
    from tools.image.pillow_split import split_storyboard
    split_storyboard(sb, out_dir, rows=2, cols=2, gutter=10)
    captured = capsys.readouterr()
    assert "deviates from 2:3" in captured.err


def test_split_top_crop_excessive_raises(tmp_path):
    """top_crop_px >= cell_h would crop the entire cell — should raise."""
    import pytest

    sb = tmp_path / "sb.png"
    _make_fake_storyboard(sb, rows=2, cols=2, cell_w=100, cell_h=150, gutter=8)

    with pytest.raises(ValueError, match="top_crop_px"):
        split_storyboard(sb, tmp_path / "cells", rows=2, cols=2, gutter=8,
                         top_crop_px=200)
