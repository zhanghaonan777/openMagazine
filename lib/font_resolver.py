"""font_resolver — resolve typography requests against the local font system.

Uses `fc-match` (Linux/Mac via fontconfig) to determine which actual
font file the system will use for a requested family name. Walks a
fallback chain when the desired family doesn't match.

The resolved log gets written to output/<slug>/font-resolution.json
at compose time, so PDF and PPTX realizers can guarantee identical
substitutions.
"""
from __future__ import annotations

import shutil
import subprocess


def _fc_match(family: str) -> str:
    """Return what fc-match says will be used for this family. Empty
    string on any error."""
    if not shutil.which("fc-match"):
        return ""
    try:
        result = subprocess.run(
            ["fc-match", "--format=%{family[0]}", family],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def resolve_font(
    desired_family: str, fallback_chain: list[str]
) -> dict:
    """Resolve a single typography request.

    Returns:
        {
            "requested": "<desired_family>",
            "matched":   "<actually-used family>",
            "fallback_used": bool,
            "reason":   "<short explanation>",
        }
    """
    matched = _fc_match(desired_family)
    if matched and matched.lower() == desired_family.lower():
        return {
            "requested": desired_family,
            "matched": matched,
            "fallback_used": False,
            "reason": "desired family resolved directly",
        }

    # Walk the fallback chain
    for fallback in fallback_chain:
        fb_matched = _fc_match(fallback)
        if fb_matched and fb_matched.lower() == fallback.lower():
            return {
                "requested": desired_family,
                "matched": fb_matched,
                "fallback_used": True,
                "reason": f"desired '{desired_family}' not installed; matched fallback '{fallback}'",
            }

    # No exact match anywhere; report whatever fc-match said for the desired
    return {
        "requested": desired_family,
        "matched": matched,
        "fallback_used": True,
        "reason": f"no exact match found; system default used: '{matched}'",
    }


def resolve_typography_pack(design_system: dict) -> dict[str, dict]:
    """Resolve every slot in design_system.typography_resolution. Returns
    a dict {slot_name: resolution_log}."""
    log: dict[str, dict] = {}
    typography = design_system.get("typography_resolution") or {}
    for slot, slot_cfg in typography.items():
        if not isinstance(slot_cfg, dict):
            continue
        log[slot] = resolve_font(
            slot_cfg.get("desired_family", ""),
            slot_cfg.get("fallback_chain") or [],
        )
    return log
