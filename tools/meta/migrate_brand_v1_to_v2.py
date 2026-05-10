"""Migrate library/brands/<name>.yaml from schema_version 1 to 2.

Adds typography / print_specs / visual_tokens from a chosen brand preset,
preserving any v1 fields (name, masthead, display_name).

Usage:
    python tools/meta/migrate_brand_v1_to_v2.py library/brands/meow-life.yaml \\
        --preset editorial-classic
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any

import yaml


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]
PRESETS_DIR = SKILL_ROOT / "library" / "brands" / "_presets"

V1_TO_V2_DEFAULTS = {
    "default_language": "en",
}


def migrate(brand_path: pathlib.Path, *, preset: str, dry_run: bool = False) -> dict:
    """Read v1 brand, return v2 dict (and optionally write it back)."""
    brand_path = pathlib.Path(brand_path)
    v1 = yaml.safe_load(brand_path.read_text(encoding="utf-8"))
    if v1.get("schema_version") == 2:
        raise ValueError(f"{brand_path} already v2; nothing to migrate")

    preset_path = PRESETS_DIR / f"{preset}.yaml"
    if not preset_path.is_file():
        raise FileNotFoundError(f"preset not found: {preset_path}")
    p = yaml.safe_load(preset_path.read_text(encoding="utf-8"))

    # Copy preset typography / print_specs / visual_tokens
    out = {
        "schema_version": 2,
        "name": v1.get("name", "unknown"),
        "display_name": v1.get("display_name", {"en": v1.get("name", "Unknown")}),
        "masthead": v1.get("masthead", v1.get("name", "MAGAZINE").upper()),
        "default_language": v1.get("default_language", V1_TO_V2_DEFAULTS["default_language"]),
        "typography": p["typography"],
        "print_specs": p["print_specs"],
        "visual_tokens": p["visual_tokens"],
    }

    if not dry_run:
        brand_path.write_text(
            yaml.safe_dump(out, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("brand_path", type=pathlib.Path)
    p.add_argument("--preset", default="editorial-classic")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    try:
        out = migrate(a.brand_path, preset=a.preset, dry_run=a.dry_run)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if a.dry_run:
        print(yaml.safe_dump(out, sort_keys=False, allow_unicode=True))
    else:
        print(f"migrated: {a.brand_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
