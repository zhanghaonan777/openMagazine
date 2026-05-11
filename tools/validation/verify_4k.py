"""verify_4k — validate generated PNG file size + aspect.

Replaces helpers/vertex_image.py:verify from predecessor.
"""
from __future__ import annotations

import pathlib
import sys

from tools.base_tool import BaseTool


class Verify4K(BaseTool):
    capability = "validation"
    provider = "local"
    status = "active"

    def run(self, issue_dir: pathlib.Path) -> int:
        return verify(issue_dir)


def _classify_aspect(w: int, h: int) -> str:
    ratio = w / h
    if abs(ratio - 2 / 3) < 0.05:
        return "2:3 portrait"
    if abs(ratio - 3 / 4) < 0.05:
        return "3:4 portrait"
    if abs(ratio - 3 / 2) < 0.05:
        return "3:2 landscape"
    if abs(ratio - 16 / 10) < 0.05:
        return "16:10 landscape"
    if abs(ratio - 1.0) < 0.05:
        return "1:1 square"
    return f"non-standard ({ratio:.3f})"


def verify(issue_dir: pathlib.Path) -> int:
    from PIL import Image

    if not issue_dir.is_dir():
        print(f"not a directory: {issue_dir}", file=sys.stderr)
        return 2

    files: list[pathlib.Path] = []
    images_dir = issue_dir / "images"
    if images_dir.is_dir():
        files.extend(sorted(images_dir.glob("page-*.png")))
        if not files:
            files.extend(sorted(images_dir.glob("spread-*/*.png")))

    if not files:
        print(f"no images found under {issue_dir}/images/", file=sys.stderr)
        return 1

    rows = []
    warn_count = 0
    for f in files:
        size_mb = f.stat().st_size / (1024 * 1024)
        with Image.open(f) as im:
            w, h = im.size
        aspect = _classify_aspect(w, h)
        flags = []
        if size_mb < 5.0:
            flags.append("⚠ small")
        if size_mb > 40.0:
            flags.append("⚠ huge")
        if "non-standard" in aspect:
            flags.append("⚠ aspect")
        if flags:
            warn_count += 1
        rel = str(f.relative_to(issue_dir))
        rows.append((rel, w, h, aspect, size_mb, flags))

    name_w = max(len(r[0]) for r in rows)
    asp_w = max(len(r[3]) for r in rows)
    for rel, w, h, aspect, size_mb, flags in rows:
        flag_str = "  ".join(flags) if flags else "✓"
        print(
            f"  {rel.ljust(name_w)}  {w:>5} × {h:<5}  {aspect.ljust(asp_w)}  {size_mb:>5.1f} MB   {flag_str}",
            file=sys.stderr,
        )

    ok_count = len(rows) - warn_count
    print(f"\n  {ok_count} ok / {warn_count} warning(s)  in {issue_dir}", file=sys.stderr)
    return 0 if warn_count == 0 else 1


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(Verify4K())
