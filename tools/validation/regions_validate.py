"""Validate library/layouts/_components/<type>.regions.yaml files."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import yaml
from jsonschema import Draft7Validator

from tools.base_tool import BaseTool


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]
OVERLAP_THRESHOLD = 0.05  # fraction of smaller region's area


def _load_schema() -> dict:
    return json.loads(
        (SKILL_ROOT / "schemas" / "regions.schema.json").read_text()
    )


def _load_components_registry() -> set[str]:
    reg = yaml.safe_load(
        (SKILL_ROOT / "library" / "components" / "registry.yaml").read_text()
    )
    return set((reg.get("components") or {}).keys())


def _rect_area(rect: list[float]) -> float:
    x1, y1, x2, y2 = rect
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def _rect_overlap_area(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    h = max(0.0, min(ay2, by2) - max(ay1, by1))
    return w * h


def validate_regions(path: pathlib.Path) -> list[str]:
    """Return a list of error messages. Empty list = valid."""
    errors: list[str] = []
    data = yaml.safe_load(pathlib.Path(path).read_text(encoding="utf-8"))

    # 1. JSON-schema structural validation
    schema = _load_schema()
    for e in Draft7Validator(schema).iter_errors(data):
        errors.append(f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}")

    if errors:
        return errors

    regions = data["regions"]

    # 2. Component vocabulary check
    known = _load_components_registry()
    for r in regions:
        comp = r.get("component")
        if comp and comp not in known:
            errors.append(
                f"region {r['id']!r}: component {comp!r} not in "
                f"library/components/registry.yaml"
            )

    # 3. Duplicate region ids
    seen: set[str] = set()
    for r in regions:
        rid = r["id"]
        if rid in seen:
            errors.append(f"duplicate region id: {rid!r}")
        seen.add(rid)

    # 4. Overlap check (above OVERLAP_THRESHOLD of smaller area). Skip:
    #   - any region with role 'accent' (intentionally sits on top)
    #   - pairs where one region has a higher z_index than the other
    #     (intentional CSS layering, e.g., text overlaid on a full-bleed
    #     hero image)
    non_accent = [r for r in regions if r["role"] != "accent"]
    for i, a in enumerate(non_accent):
        for b in non_accent[i + 1:]:
            # Skip if regions are on different z-layers (intentional overlay)
            if (a.get("z_index", 0) or 0) != (b.get("z_index", 0) or 0):
                continue
            overlap = _rect_overlap_area(a["rect_norm"], b["rect_norm"])
            smaller = min(_rect_area(a["rect_norm"]), _rect_area(b["rect_norm"]))
            if smaller > 0 and overlap / smaller > OVERLAP_THRESHOLD:
                errors.append(
                    f"regions {a['id']!r} and {b['id']!r} overlap "
                    f"({overlap / smaller:.0%} of smaller); set different "
                    f"z_index values or move one"
                )

    return errors


class RegionsValidate(BaseTool):
    capability = "validation"
    provider = "local"
    status = "active"

    def run(self, path: pathlib.Path) -> list[str]:
        return validate_regions(path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("path", type=pathlib.Path,
                   help="Path to a *.regions.yaml file")
    a = p.parse_args(argv)
    errs = validate_regions(a.path)
    if not errs:
        print(f"✓ {a.path.name}: valid", file=sys.stderr)
        return 0
    print(f"✗ {a.path.name}: {len(errs)} error(s)", file=sys.stderr)
    for e in errs:
        print(f"  {e}", file=sys.stderr)
    return 1


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(RegionsValidate())


if __name__ == "__main__":
    sys.exit(main())
