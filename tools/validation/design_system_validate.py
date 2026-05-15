"""Validate library/design-systems/<slug>.yaml files."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml
from jsonschema import Draft7Validator

from tools.base_tool import BaseTool


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _parse_slide_size(raw: str | None) -> tuple[int, int] | None:
    if not raw or "x" not in str(raw).lower():
        return None
    left, right = str(raw).lower().split("x", 1)
    try:
        return int(left), int(right)
    except ValueError:
        return None


def _load_schema() -> dict:
    return json.loads(
        (SKILL_ROOT / "schemas" / "design-system.schema.json").read_text()
    )


def validate_design_system(path: pathlib.Path) -> list[str]:
    """Return a list of error messages. Empty list = valid."""
    errors: list[str] = []
    data = yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))

    schema = _load_schema()
    for e in Draft7Validator(schema).iter_errors(data):
        errors.append(
            f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
        )

    if errors:
        return errors

    # Semantic checks beyond schema
    typography = data.get("typography_resolution") or {}
    for slot, cfg in typography.items():
        if not cfg.get("fallback_chain"):
            errors.append(
                f"typography_resolution/{slot}: fallback_chain must have >= 1 entry"
            )

    for idx, target in enumerate(data.get("output_targets") or []):
        fmt = target.get("format")
        if fmt != "magazine-pptx":
            continue
        if target.get("realizer") != "presentations":
            errors.append(
                f"output_targets/{idx}: magazine-pptx must use realizer=presentations"
            )
        size = _parse_slide_size(target.get("slide_size"))
        if not size:
            errors.append(
                f"output_targets/{idx}: magazine-pptx requires slide_size like 720x1080"
            )
            continue
        width, height = size
        if height <= width:
            errors.append(
                f"output_targets/{idx}: magazine-pptx slide_size must be portrait 2:3"
            )
        ratio = width / height
        if abs(ratio - (2 / 3)) > 0.03:
            errors.append(
                f"output_targets/{idx}: magazine-pptx slide_size must be near 2:3"
            )
        if not target.get("page_count"):
            errors.append(
                f"output_targets/{idx}: magazine-pptx requires page_count"
            )

    return errors


class DesignSystemValidate(BaseTool):
    capability = "validation"
    provider = "local"
    status = "active"

    def run(self, path: pathlib.Path) -> list[str]:
        return validate_design_system(path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", type=pathlib.Path)
    a = p.parse_args(argv)
    errs = validate_design_system(a.path)
    if not errs:
        print(f"✓ {a.path.name}: valid", file=sys.stderr)
        return 0
    print(f"✗ {a.path.name}: {len(errs)} error(s)", file=sys.stderr)
    for e in errs:
        print(f"  {e}", file=sys.stderr)
    return 1


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(DesignSystemValidate())


if __name__ == "__main__":
    sys.exit(main())
