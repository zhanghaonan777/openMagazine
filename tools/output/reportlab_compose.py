"""reportlab_compose — A4 portrait PDF assembly from <issue>/images/page-*.png.

Ported from predecessor only_image_magazine_gen/helpers/build_pdf.py
(simple-mode paths only; no styled-mode).
"""
from __future__ import annotations

import pathlib
import re
import sys
from typing import Iterable

from tools.base_tool import BaseTool

ASPECT_TOL = 0.05
PORTRAIT_RATIO = 2 / 3
LANDSCAPE_RATIO = 3 / 2


class ReportlabCompose(BaseTool):
    capability = "pdf_compose"
    provider = "reportlab"
    status = "active"
    agent_skills = ["reportlab-typography"]

    def run(
        self,
        issue_dir: pathlib.Path,
        out_path: pathlib.Path | None = None,
        *,
        order_file: pathlib.Path | None = None,
        spread_mode: str = "split",
    ) -> dict:
        """Assembles <issue>/images/page-*.png into a single A4 portrait PDF."""
        if out_path is None:
            out_path = issue_dir / "magazine.pdf"

        if order_file:
            images = _read_order_file(order_file, issue_dir)
        else:
            images = _discover(issue_dir)

        if not images:
            raise RuntimeError(f"no images found under {issue_dir}/images/")

        n_images, n_pages = build_pdf(images, out_path, spread_mode=spread_mode)
        size_mb = out_path.stat().st_size / (1024 * 1024)
        print(
            f"[pdf] {out_path.name}  {n_images} images -> {n_pages} pages  {size_mb:.1f} MB",
            file=sys.stderr,
        )
        return {
            "out_path": str(out_path),
            "image_count": n_images,
            "page_count": n_pages,
            "size_mb": size_mb,
        }


def _classify(img_path: pathlib.Path) -> str:
    from PIL import Image
    with Image.open(img_path) as im:
        w, h = im.size
    ratio = w / h
    if abs(ratio - PORTRAIT_RATIO) < ASPECT_TOL:
        return "portrait"
    if abs(ratio - LANDSCAPE_RATIO) < ASPECT_TOL:
        return "landscape"
    return "other"


def _discover(issue_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return <issue>/images/page-NN.png sorted by NN ascending."""
    page_re = re.compile(r"page-(\d+)")

    def _key(p: pathlib.Path) -> int:
        m = page_re.search(p.stem)
        return int(m.group(1)) if m else 0

    images_dir = issue_dir / "images"
    if not images_dir.is_dir():
        return []
    return sorted(images_dir.glob("page-*.png"), key=_key)


def _read_order_file(path: pathlib.Path, issue_dir: pathlib.Path) -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        p = (issue_dir / line).resolve()
        if not p.exists():
            raise FileNotFoundError(f"order entry not found: {line}")
        out.append(p)
    return out


def _add_full_bleed(c, img_path: pathlib.Path, page_w: float, page_h: float) -> None:
    c.drawImage(str(img_path), 0, 0, page_w, page_h, preserveAspectRatio=False)
    c.showPage()


def _add_letterboxed(c, img_path: pathlib.Path, page_w: float, page_h: float) -> None:
    c.setFillColorRGB(0, 0, 0)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    c.drawImage(str(img_path), 0, 0, page_w, page_h, preserveAspectRatio=True, anchor="c")
    c.showPage()


def _add_spread(c, img_path: pathlib.Path, page_w: float, page_h: float) -> None:
    """3:2 image -> two A4 portrait pages (split vertically)."""
    from PIL import Image
    from reportlab.lib.utils import ImageReader

    with Image.open(img_path) as im:
        w, h = im.size
        half_w = w // 2
        target_w = int(h * (2 / 3))
        left_box = (half_w - target_w, 0, half_w, h)
        right_box = (half_w, 0, half_w + target_w, h)
        left_img = im.crop(left_box).copy()
        right_img = im.crop(right_box).copy()
    c.drawImage(ImageReader(left_img), 0, 0, page_w, page_h, preserveAspectRatio=False)
    c.showPage()
    c.drawImage(ImageReader(right_img), 0, 0, page_w, page_h, preserveAspectRatio=False)
    c.showPage()


def build_pdf(
    images: Iterable[pathlib.Path],
    out_path: pathlib.Path,
    *,
    spread_mode: str = "split",
) -> tuple[int, int]:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    images = list(images)
    if not images:
        raise ValueError("no images to assemble")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    A4_W, A4_H = A4
    c = canvas.Canvas(str(out_path), pagesize=A4)

    image_count = 0
    page_count = 0
    for img in images:
        kind = _classify(img)
        image_count += 1

        if kind == "landscape" and spread_mode == "split":
            _add_spread(c, img, A4_W, A4_H)
            page_count += 2
        elif kind == "landscape" and spread_mode == "landscape":
            c.setPageSize(landscape(A4))
            c.drawImage(str(img), 0, 0, A4_H, A4_W, preserveAspectRatio=False)
            c.showPage()
            c.setPageSize(A4)
            page_count += 1
        elif kind == "portrait":
            _add_full_bleed(c, img, A4_W, A4_H)
            page_count += 1
        else:
            print(f"warn: {img.name} non-standard aspect — letterboxing", file=sys.stderr)
            _add_letterboxed(c, img, A4_W, A4_H)
            page_count += 1

    c.save()
    return image_count, page_count


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(ReportlabCompose())
