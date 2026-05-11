"""regions_loader — read library/layouts/_components/<type>.regions.yaml.

This is the canonical "where stuff lives on a spread" data layer. Image
generation and HTML render both read through this loader.
"""
from __future__ import annotations

import pathlib

import yaml


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]


class RegionsNotFoundError(FileNotFoundError):
    """Raised when a spread type has no regions yaml on disk yet."""


def load_regions(spread_type: str) -> dict:
    """Load and return the regions yaml for the given spread type.

    Raises ``RegionsNotFoundError`` if no yaml exists for this spread type
    (during migration, only some spreads have yamls; the renderer must
    fall back to legacy CSS-positioned templates for the rest).
    """
    path = (
        SKILL_ROOT
        / "library"
        / "layouts"
        / "_components"
        / f"{spread_type}.regions.yaml"
    )
    if not path.is_file():
        raise RegionsNotFoundError(
            f"no regions yaml for spread_type={spread_type!r}; expected {path}"
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def regions_for_image_prompt(
    spread_type: str, image_slot: str
) -> dict[str, object]:
    """Return the calling slot's own region plus every sibling region.

    Used by prompt_builder_v2 to inject "this image fills region X, do not
    paint into sibling regions Y/Z/..." text into the upscale prompt.

    Raises ValueError if no region in the regions yaml claims this image_slot.
    """
    regions = load_regions(spread_type)
    own = None
    siblings: list[dict] = []
    for r in regions["regions"]:
        if r.get("role") == "image" and r.get("image_slot") == image_slot:
            own = r
        elif (
            r.get("role") == "image_grid"
            and image_slot in (r.get("image_slots") or [])
        ):
            own = r
        else:
            siblings.append(r)
    if own is None:
        raise ValueError(
            f"no region in {spread_type} claims image_slot={image_slot!r}"
        )
    return {"own_region": own, "sibling_regions": siblings}
