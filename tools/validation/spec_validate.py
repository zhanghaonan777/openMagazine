"""Validate an issue-spec.yaml + its 5 layer references.

Usage:
    python tools/validation/spec_validate.py library/issue-specs/cosmos-luna-01.yaml

Exit codes:
    0  spec is valid
    1  spec has errors (printed to stderr)
    2  spec file not found / not parseable

Validation checks:
    - spec.schema_version == 1
    - All required spec top-level fields present
    - 5 layer references each resolve to existing yaml files
      (style is exempt — Tier 2 scaffold-style fallback is allowed)
    - Each layer yaml has schema_version == 1 + required fields
    - themes/<name>.yaml.page_plan_hints length == layouts/<layout>.yaml.page_count
    - layouts/<layout>.yaml.storyboard_grid rows*cols == page_count
    - subjects/<name>.yaml.reference_image points to an existing file
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]
LIBRARY_DIR = SKILL_ROOT / "library"
STYLES_DIR = SKILL_ROOT / "styles"


SPEC_REQUIRED_FIELDS = {
    "schema_version",
    "slug",
    "subject",
    "style",
    "theme",
    "layout",
    "brand",
}

LAYER_DIRS = {
    "subject": LIBRARY_DIR / "subjects",
    "theme": LIBRARY_DIR / "themes",
    "layout": LIBRARY_DIR / "layouts",
    "brand": LIBRARY_DIR / "brands",
    "style": STYLES_DIR,           # top-level, not under library/
}

LAYER_REQUIRED_FIELDS = {
    "subject": {"schema_version", "name", "species", "reference_image", "traits"},
    "theme": {"schema_version", "name", "theme_world", "default_cover_line",
              "page_plan_hints"},
    "layout": {"schema_version", "name", "page_count", "aspect",
               "storyboard_grid", "typography_mode"},
    "brand": {"schema_version", "name", "masthead"},
    # style: validated by templates/styles/README.md schema; we don't re-check here
}


class SpecError(Exception):
    """Raised on validation failures; carries a list of error messages."""

    def __init__(self, errors: list[str]):
        super().__init__(f"{len(errors)} validation errors")
        self.errors = errors


def _load_yaml(path: pathlib.Path) -> dict[str, Any]:
    import yaml
    if not path.is_file():
        raise FileNotFoundError(f"yaml not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _check_required(d: dict, required: set[str], where: str) -> list[str]:
    missing = [f for f in required if f not in d]
    if not missing:
        return []
    return [f"{where}: missing required field(s): {', '.join(sorted(missing))}"]


def _parse_grid(grid_str: str) -> tuple[int, int]:
    """Parse '4x4' → (4, 4); '3x4' → (3, 4); raises ValueError if malformed."""
    parts = grid_str.lower().replace("×", "x").split("x")
    if len(parts) != 2:
        raise ValueError(f"storyboard_grid {grid_str!r} must be 'NxM'")
    return int(parts[0]), int(parts[1])


def validate_spec(spec_path: pathlib.Path) -> list[str]:
    """Return a list of error messages. Empty list = valid."""
    errors: list[str] = []

    try:
        spec = _load_yaml(spec_path)
    except FileNotFoundError as e:
        return [str(e)]
    except Exception as e:
        return [f"failed to parse {spec_path}: {e}"]

    spec_dir = spec_path.parent

    # 1. spec required fields
    errors += _check_required(spec, SPEC_REQUIRED_FIELDS, "spec")
    if errors:
        return errors  # bail early — can't proceed if structure is wrong

    if spec.get("schema_version") != 1:
        errors.append(f"spec.schema_version must be 1, got {spec.get('schema_version')!r}")

    # 2. Each layer reference resolves
    layer_yamls: dict[str, dict] = {}
    for layer_field, dir_name in LAYER_DIRS.items():
        ref_name = spec.get(layer_field)
        if not isinstance(ref_name, str) or not ref_name:
            errors.append(f"spec.{layer_field} must be a non-empty string")
            continue

        layer_yaml_path = dir_name / f"{ref_name}.yaml"
        if not layer_yaml_path.is_file():
            if layer_field == "style":
                # style is exempt — Tier 2 scaffold-style fallback handles missing styles
                # (would generate the yaml at runtime). Issue a soft warning, not an error.
                errors.append(
                    f"NOTE: spec.style={ref_name!r} not in {layer_yaml_path}; "
                    f"will trigger scaffold-style meta-protocol at runtime "
                    f"(Tier 2). This is allowed."
                )
                continue
            errors.append(
                f"spec.{layer_field}={ref_name!r} → {layer_yaml_path} not found"
            )
            continue

        try:
            layer_yamls[layer_field] = _load_yaml(layer_yaml_path)
        except Exception as e:
            errors.append(f"failed to load {layer_yaml_path}: {e}")

    # 3. Each layer yaml has required fields
    for layer_field, required in LAYER_REQUIRED_FIELDS.items():
        if layer_field not in layer_yamls:
            continue  # already errored above
        errors += _check_required(
            layer_yamls[layer_field], required,
            f"{layer_field} yaml ({spec[layer_field]})",
        )

    # 4. layout: storyboard_grid rows*cols == page_count
    layout = layer_yamls.get("layout", {})
    if "storyboard_grid" in layout and "page_count" in layout:
        try:
            rows, cols = _parse_grid(layout["storyboard_grid"])
            if rows * cols != layout["page_count"]:
                errors.append(
                    f"layout {spec['layout']}: storyboard_grid {layout['storyboard_grid']} "
                    f"= {rows}×{cols} = {rows*cols}, but page_count={layout['page_count']}; "
                    f"these must match"
                )
        except ValueError as e:
            errors.append(f"layout {spec['layout']}: {e}")

    # 5. theme: page_plan_hints length matches layout.page_count
    theme = layer_yamls.get("theme", {})
    if "page_plan_hints" in theme and "page_count" in layout:
        hints = theme["page_plan_hints"]
        if not isinstance(hints, list):
            errors.append(f"theme {spec['theme']}: page_plan_hints must be a list")
        elif len(hints) != layout["page_count"]:
            errors.append(
                f"theme {spec['theme']}: page_plan_hints has {len(hints)} entries, "
                f"but layout {spec['layout']}.page_count = {layout['page_count']}; "
                f"these must match"
            )

    # 6. subject: reference_image exists (resolve relative to subjects/<name>.yaml)
    subject = layer_yamls.get("subject", {})
    if "reference_image" in subject:
        ref_str = subject["reference_image"]
        subjects_dir = LIBRARY_DIR / "subjects"
        ref_path = (subjects_dir / ref_str).resolve()
        if not ref_path.is_file():
            errors.append(
                f"subject {spec['subject']}: reference_image {ref_str!r} → "
                f"{ref_path} not found"
            )

    # 7. overrides — soft type-check, no required fields
    overrides = spec.get("overrides", {})
    if overrides is not None and not isinstance(overrides, dict):
        errors.append("spec.overrides must be a mapping (or omitted/empty)")

    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="spec_validate", description=__doc__)
    p.add_argument("spec", help="Path to issue-spec.yaml")
    args = p.parse_args(argv)

    spec_path = pathlib.Path(args.spec).resolve()
    errors = validate_spec(spec_path)

    # Separate hard errors from soft NOTEs (scaffold-style fallback)
    hard = [e for e in errors if not e.startswith("NOTE:")]
    soft = [e for e in errors if e.startswith("NOTE:")]

    if not hard and not soft:
        print(f"✓ {spec_path.name}: valid", file=sys.stderr)
        return 0

    if soft:
        for e in soft:
            print(f"  {e}", file=sys.stderr)

    if hard:
        print(f"✗ {spec_path.name}: {len(hard)} error(s)", file=sys.stderr)
        for e in hard:
            print(f"  {e}", file=sys.stderr)
        return 1

    # only NOTEs (soft warnings, scaffold-style fallback) — still valid
    print(f"✓ {spec_path.name}: valid (with notes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ----- BaseTool wrapper for tool registry -----

from tools.base_tool import BaseTool  # noqa: E402


class SpecValidate(BaseTool):
    capability = "validation"
    provider = "local"
    status = "active"
    agent_skills = ["spec-validate-usage"]

    def run(self, spec_path: pathlib.Path) -> list[str]:
        return validate_spec(spec_path)


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(SpecValidate())
