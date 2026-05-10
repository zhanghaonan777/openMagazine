"""reference_photo_check — assert reference photo long edge >= 1024 px."""
from __future__ import annotations

import pathlib

from tools.base_tool import BaseTool


class ReferencePhotoCheck(BaseTool):
    capability = "validation"
    provider = "local"
    status = "active"

    def run(self, photo_path: pathlib.Path, *, min_long_edge: int = 1024) -> bool:
        from PIL import Image
        with Image.open(photo_path) as im:
            w, h = im.size
        long_edge = max(w, h)
        if long_edge < min_long_edge:
            raise ValueError(
                f"{photo_path.name}: long edge {long_edge}px < min {min_long_edge}px. "
                f"Reference photo must be at least 1024 on long edge for 4K dual-ref."
            )
        return True


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(ReferencePhotoCheck())
