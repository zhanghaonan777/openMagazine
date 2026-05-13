"""design_system_loader — read profiles and per-issue design systems.

profiles are a closed registry of publication types
(consumer-retail / finance-ir / ...). design-systems are per-issue
resolved decisions (typography fallback chain, text-safe contracts,
brand authenticity gates, output targets).

This is the v0.3.2 data-layer entrypoint that mirrors v0.3.1's
regions_loader pattern.
"""
from __future__ import annotations

import pathlib

import yaml


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]

DEFAULT_FALLBACK_FAMILIES = ["Georgia", "Times New Roman", "serif"]
DEFAULT_MONO_FALLBACK_FAMILIES = ["Menlo", "Courier", "monospace"]


class ProfileNotFoundError(FileNotFoundError):
    """Raised when library/profiles/<name>.yaml is missing."""


class DesignSystemNotFoundError(FileNotFoundError):
    """Raised when library/design-systems/<slug>.yaml is missing."""


def load_profile(name: str) -> dict:
    """Load and return the profile yaml for the given profile name."""
    path = SKILL_ROOT / "library" / "profiles" / f"{name}.yaml"
    if not path.is_file():
        raise ProfileNotFoundError(
            f"no profile yaml for name={name!r}; expected {path}"
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_design_system(slug: str) -> dict:
    """Load and return the design-system yaml for the given issue slug."""
    path = SKILL_ROOT / "library" / "design-systems" / f"{slug}.yaml"
    if not path.is_file():
        raise DesignSystemNotFoundError(
            f"no design-system yaml for slug={slug!r}; expected {path}"
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def resolve_design_system(
    spec: dict, layers: dict, *, profile_name: str | None = None
) -> dict:
    """Compose a per-issue design-system from spec + brand + profile.

    Returns the resolved dict (also suitable for persisting to
    library/design-systems/<slug>.yaml).
    """
    slug = spec["slug"]
    brand = layers.get("brand") or {}
    brand_name = brand.get("name", spec.get("brand", "unknown"))
    profile_name = profile_name or "consumer-retail"

    # Build typography_resolution from brand.typography + default fallbacks
    typography_in = brand.get("typography") or {}
    typography_resolution: dict[str, dict] = {}
    for slot, slot_cfg in typography_in.items():
        if not isinstance(slot_cfg, dict):
            continue
        desired = slot_cfg.get("family", "")
        is_mono = slot in ("meta", "kicker", "page_number") and "Mono" in desired
        fallback = DEFAULT_MONO_FALLBACK_FAMILIES if is_mono else DEFAULT_FALLBACK_FAMILIES
        typography_resolution[slot] = {
            "desired_family": desired,
            "fallback_chain": list(fallback),
            "resolved_at_render": None,
        }

    return {
        "schema_version": 1,
        "slug": slug,
        "profile": profile_name,
        "brand": brand_name,
        "inheritance": {
            "base_brand_typography": True,
            "base_brand_print_specs": True,
            "base_brand_visual_tokens": True,
        },
        "typography_resolution": typography_resolution,
        "text_safe_contracts": {
            "default_rule": (
                "When text overlays or sits inside a generated visual field, "
                "keep clean negative space inside each text-safe rectangle."
            ),
            "per_spread_overrides": {},
        },
        "brand_authenticity": {
            "do_not_generate": ["logo", "mascot", "app_icon"],
            "do_not_approximate": [],
            "asset_provenance_required": [],
            "asset_provenance_optional": [],
        },
        "layout_quality": {
            "min_gap_px": 16,
            "max_text_image_overlap_px": 25,
            "max_text_text_overlap_px": 10,
            "fail_on": "error",
        },
        "output_targets": [
            {"format": "a4-magazine", "realizer": "weasyprint"}
        ],
        "contact_sheet_rubric": {
            "distinct_layouts_required": 7,
            "template_collapse_threshold": 3,
        },
    }
