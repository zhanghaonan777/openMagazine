# Regions as Shared Contract — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote spread "regions" (where stuff lives on a magazine spread) to a first-class data layer, shared by three consumers — image-gen prompts, HTML/CSS render, article copy validation — so the three stop synchronizing through human attention.

**Architecture:** Each spread type ships a `regions.yaml` declaring every bounding box with role, coordinates, and component binding. A closed component registry constrains the vocabulary. Migration is incremental (one component at a time); legacy CSS-positioned components keep working until each is migrated. The image-gen prompt builder injects sibling-region context per upscale call so the model is told which rectangles to keep calm for later HTML overlays.

**Tech Stack:** Python 3.10, pytest, jsonschema, PyYAML, Jinja2, WeasyPrint (downstream, not directly touched).

**Predecessor:** v0.3.0 (`commit 7794053`). See [spec](../specs/2026-05-11-regions-as-shared-contract-design.md).

**Prerequisite signal:** The spec recommends at least one live editorial-16page smoke run on v0.3.0 before R3+. R1 + R2 are safe additive-only work that does not depend on empirical findings. R3 (image-prompt injection) and beyond should ideally land after the smoke run so the prompt format can be informed by observed model behavior. The plan does not enforce this — execute it in whichever order works for you.

---

## Phase R1 — Schema + loader + validator (~1 day, 5 tasks)

Foundation. Zero behavior change. Just adds files. Safe to ship without any empirical signal.

### Task R1-T1: Author `schemas/regions.schema.json`

**Files:**
- Create: `~/github/openMagazine/schemas/regions.schema.json`

- [ ] **Step R1-T1.1: Create the JSON schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Spread regions",
  "type": "object",
  "required": ["schema_version", "spread_type", "regions"],
  "properties": {
    "schema_version": {"const": 1},
    "spread_type": {"type": "string"},
    "pages_per_instance": {"type": "integer", "minimum": 1, "maximum": 4},
    "bounds": {
      "type": "string",
      "enum": ["full", "left-page", "right-page", "full-bleed", "custom"],
      "default": "full"
    },
    "regions": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "rect_norm", "role"],
        "properties": {
          "id": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
          "rect_norm": {
            "type": "array",
            "items": {"type": "number", "minimum": 0, "maximum": 1},
            "minItems": 4,
            "maxItems": 4
          },
          "role": {
            "enum": ["image", "image_grid", "text", "text_decorative", "negative_space", "accent"]
          },
          "image_slot": {"type": "string"},
          "image_slots": {"type": "array", "items": {"type": "string"}},
          "grid_cols": {"type": "integer", "minimum": 1, "maximum": 8},
          "aspect": {"type": "string"},
          "component": {"type": "string"},
          "text_field": {"type": "string"},
          "component_props": {"type": "object"},
          "image_prompt_hint": {"type": "string"},
          "z_index": {"type": "integer", "default": 0}
        },
        "allOf": [
          {
            "if": {"properties": {"role": {"const": "image"}}},
            "then": {"required": ["image_slot", "aspect"]}
          },
          {
            "if": {"properties": {"role": {"const": "image_grid"}}},
            "then": {"required": ["image_slots", "grid_cols"]}
          },
          {
            "if": {"properties": {"role": {"const": "text"}}},
            "then": {"required": ["component", "text_field"]}
          },
          {
            "if": {"properties": {"role": {"const": "text_decorative"}}},
            "then": {"required": ["component"]}
          },
          {
            "if": {"properties": {"role": {"const": "accent"}}},
            "then": {"required": ["component"]}
          }
        ]
      }
    }
  }
}
```

- [ ] **Step R1-T1.2: Verify schema parses**

Run:
```bash
.venv/bin/python -c "import json; json.load(open('schemas/regions.schema.json'))"
```
Expected: no output (success).

- [ ] **Step R1-T1.3: Commit**

```bash
git add schemas/regions.schema.json
git commit -m "feat(schemas): regions.schema.json for spread regions yaml"
```

---

### Task R1-T2: Component registry yaml + its schema

**Files:**
- Create: `~/github/openMagazine/library/components/registry.yaml`
- Create: `~/github/openMagazine/library/components/README.md`
- Create: `~/github/openMagazine/schemas/components-registry.schema.json`

- [ ] **Step R1-T2.1: Create directory + README**

```bash
mkdir -p ~/github/openMagazine/library/components
```

```markdown
# library/components/

Closed registry of every visual component a region can name. Adding a
new component is a small explicit PR — directors can't invent component
names. This mirrors the PPT skill's 22-locked-layouts philosophy applied
to component primitives.

See `registry.yaml` for the canonical list; `../layouts/_components/*.j2`
for how each is rendered; `docs/component-registry-reference.md` for
prose docs.

## Adding a new component

1. Add an entry to `registry.yaml` with `description`, `typography_slot`,
   `accepts_props`.
2. Add a corresponding rendering rule to the `render_component` macro
   (see `library/layouts/_components/_macros/region.j2.html`).
3. Update `docs/component-registry-reference.md`.
4. Run `tests/contracts/test_v2_pipelines.py` to confirm validation still
   passes.
```

- [ ] **Step R1-T2.2: Create `library/components/registry.yaml`**

```yaml
schema_version: 1

components:
  Kicker:
    description: Small uppercase label, mono font (e.g. "Chapter 01")
    typography_slot: kicker
    typical_size: "8-10pt"
    accepts_props: []

  Title:
    description: Large display headline
    typography_slot: display
    typical_size: "32-48pt"
    accepts_props: [align]

  Lead:
    description: Italic intro paragraph that hooks the reader
    typography_slot: body
    typical_size: "11-13pt italic"
    accepts_props: []

  Body:
    description: Long-form running text
    typography_slot: body
    accepts_props: [hyphenate, align, columns]

  BodyWithDropCap:
    description: Body with raised-initial drop cap on first paragraph
    typography_slot: body
    accepts_props: [drop_cap, drop_cap_lines, hyphenate, align]

  PullQuote:
    description: Large inset quote
    typography_slot: pull_quote
    accepts_props: [align]

  Caption:
    description: Small italic image caption
    typography_slot: caption
    accepts_props: []

  CaptionedThumbnail:
    description: Image + caption pair
    typography_slot: caption
    accepts_props: [aspect]

  AccentRule:
    description: Horizontal hairline in accent color
    typography_slot: ~
    accepts_props: [thickness, width_pct]

  Folio:
    description: Page number + optional footer text
    typography_slot: page_number
    accepts_props: [position]

  Masthead:
    description: Brand masthead (e.g. "MEOW LIFE")
    typography_slot: display
    accepts_props: []

  CoverLine:
    description: Cover sub-headline
    typography_slot: display
    accepts_props: [align]
```

- [ ] **Step R1-T2.3: Create `schemas/components-registry.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Component registry",
  "type": "object",
  "required": ["schema_version", "components"],
  "properties": {
    "schema_version": {"const": 1},
    "components": {
      "type": "object",
      "patternProperties": {
        "^[A-Z][a-zA-Z]+$": {
          "type": "object",
          "required": ["description"],
          "properties": {
            "description": {"type": "string"},
            "typography_slot": {"type": ["string", "null"]},
            "typical_size": {"type": "string"},
            "accepts_props": {
              "type": "array",
              "items": {"type": "string"}
            }
          }
        }
      },
      "additionalProperties": false
    }
  }
}
```

- [ ] **Step R1-T2.4: Verify both parse + validate against each other**

Run:
```bash
.venv/bin/python -c "
import json, yaml, jsonschema
schema = json.load(open('schemas/components-registry.schema.json'))
data = yaml.safe_load(open('library/components/registry.yaml').read())
jsonschema.validate(instance=data, schema=schema)
print('valid')
"
```
Expected output: `valid`

- [ ] **Step R1-T2.5: Commit**

```bash
git add library/components/ schemas/components-registry.schema.json
git commit -m "feat(library): components/registry.yaml — closed component vocabulary"
```

---

### Task R1-T3: `lib/regions_loader.py` + tests

**Files:**
- Create: `~/github/openMagazine/lib/regions_loader.py`
- Create: `~/github/openMagazine/tests/unit/test_regions_loader.py`

- [ ] **Step R1-T3.1: Write the failing test**

```python
"""Tests for regions_loader."""
from pathlib import Path

import pytest
import yaml

from lib.regions_loader import (
    load_regions,
    regions_for_image_prompt,
    RegionsNotFoundError,
)


SKILL_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sample_yaml(tmp_path, monkeypatch):
    """Write a minimal regions yaml under a temporary library/layouts/_components/.

    Patches SKILL_ROOT so load_regions finds it.
    """
    components_dir = tmp_path / "library" / "layouts" / "_components"
    components_dir.mkdir(parents=True)
    yaml_path = components_dir / "feature-spread.regions.yaml"
    yaml_path.write_text(yaml.safe_dump({
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "hero_image", "rect_norm": [0.0, 0.0, 0.5, 1.0],
             "role": "image", "image_slot": "feature_hero", "aspect": "3:4"},
            {"id": "title", "rect_norm": [0.55, 0.15, 0.95, 0.30],
             "role": "text", "component": "Title", "text_field": "title"},
            {"id": "body", "rect_norm": [0.55, 0.45, 0.95, 0.85],
             "role": "text", "component": "BodyWithDropCap", "text_field": "body"},
        ],
    }))
    monkeypatch.setattr("lib.regions_loader.SKILL_ROOT", tmp_path)
    return yaml_path


def test_load_regions_returns_dict(sample_yaml):
    regions = load_regions("feature-spread")
    assert regions["spread_type"] == "feature-spread"
    assert regions["schema_version"] == 1
    assert len(regions["regions"]) == 3


def test_load_regions_missing_raises(monkeypatch, tmp_path):
    monkeypatch.setattr("lib.regions_loader.SKILL_ROOT", tmp_path)
    with pytest.raises(RegionsNotFoundError):
        load_regions("does-not-exist")


def test_regions_for_image_prompt_own_and_siblings(sample_yaml):
    ctx = regions_for_image_prompt("feature-spread", "feature_hero")
    assert ctx["own_region"]["id"] == "hero_image"
    assert ctx["own_region"]["image_slot"] == "feature_hero"
    sibling_ids = {r["id"] for r in ctx["sibling_regions"]}
    assert sibling_ids == {"title", "body"}


def test_regions_for_image_prompt_unknown_slot_raises(sample_yaml):
    with pytest.raises(ValueError, match="image_slot"):
        regions_for_image_prompt("feature-spread", "nonexistent_slot")
```

- [ ] **Step R1-T3.2: Run test to verify it fails**

Run:
```bash
.venv/bin/python -m pytest tests/unit/test_regions_loader.py -v
```
Expected: `ModuleNotFoundError: No module named 'lib.regions_loader'`

- [ ] **Step R1-T3.3: Write `lib/regions_loader.py`**

```python
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
```

- [ ] **Step R1-T3.4: Run tests, expect pass**

Run:
```bash
.venv/bin/python -m pytest tests/unit/test_regions_loader.py -v
```
Expected: 4 passed.

- [ ] **Step R1-T3.5: Commit**

```bash
git add lib/regions_loader.py tests/unit/test_regions_loader.py
git commit -m "feat(lib): regions_loader for spread regions yaml + image prompt context"
```

---

### Task R1-T4: `tools/validation/regions_validate.py` + tests

**Files:**
- Create: `~/github/openMagazine/tools/validation/regions_validate.py`
- Create: `~/github/openMagazine/tests/unit/test_regions_validate.py`
- Modify: `~/github/openMagazine/tools/validation/__init__.py`

- [ ] **Step R1-T4.1: Write the failing test**

```python
"""Tests for regions_validate."""
from pathlib import Path

import pytest
import yaml

from tools.validation.regions_validate import validate_regions


def _write_yaml(tmp_path, data):
    p = tmp_path / "x.regions.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


def test_valid_regions_yaml_returns_empty_errors(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "hero", "rect_norm": [0.0, 0.0, 0.5, 1.0],
             "role": "image", "image_slot": "feature_hero", "aspect": "3:4"},
        ],
    })
    assert validate_regions(p) == []


def test_rect_norm_out_of_range_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "bad", "rect_norm": [0.0, 0.0, 1.5, 1.0],  # x2 > 1
             "role": "negative_space"},
        ],
    })
    errors = validate_regions(p)
    assert any("rect_norm" in e for e in errors)


def test_text_region_missing_text_field_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "title", "rect_norm": [0.55, 0.1, 0.95, 0.3],
             "role": "text", "component": "Title"},  # missing text_field
        ],
    })
    errors = validate_regions(p)
    assert any("text_field" in e for e in errors)


def test_unknown_component_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "title", "rect_norm": [0.55, 0.1, 0.95, 0.3],
             "role": "text", "component": "InventedComponent",
             "text_field": "title"},
        ],
    })
    errors = validate_regions(p)
    assert any("InventedComponent" in e for e in errors)


def test_overlapping_regions_above_threshold_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "a", "rect_norm": [0.0, 0.0, 0.5, 0.5], "role": "negative_space"},
            {"id": "b", "rect_norm": [0.1, 0.1, 0.6, 0.6], "role": "negative_space"},
        ],
    })
    errors = validate_regions(p)
    assert any("overlap" in e for e in errors)


def test_duplicate_region_id_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "spread_type": "feature-spread",
        "regions": [
            {"id": "x", "rect_norm": [0.0, 0.0, 0.4, 0.4], "role": "negative_space"},
            {"id": "x", "rect_norm": [0.5, 0.5, 0.9, 0.9], "role": "negative_space"},
        ],
    })
    errors = validate_regions(p)
    assert any("duplicate" in e.lower() for e in errors)
```

- [ ] **Step R1-T4.2: Run test, expect ImportError**

Run:
```bash
.venv/bin/python -m pytest tests/unit/test_regions_validate.py -v
```
Expected: `ModuleNotFoundError: No module named 'tools.validation.regions_validate'`

- [ ] **Step R1-T4.3: Write `tools/validation/regions_validate.py`**

```python
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
        # If structural validation fails, deeper checks would be noisy.
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

    # 4. Overlap check (above OVERLAP_THRESHOLD of smaller area, ignoring
    # accent regions which intentionally sit on top of text)
    non_accent = [r for r in regions if r["role"] != "accent"]
    for i, a in enumerate(non_accent):
        for b in non_accent[i + 1:]:
            overlap = _rect_overlap_area(a["rect_norm"], b["rect_norm"])
            smaller = min(_rect_area(a["rect_norm"]), _rect_area(b["rect_norm"]))
            if smaller > 0 and overlap / smaller > OVERLAP_THRESHOLD:
                errors.append(
                    f"regions {a['id']!r} and {b['id']!r} overlap "
                    f"({overlap / smaller:.0%} of smaller); set z_index "
                    f"explicitly or move one"
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
```

- [ ] **Step R1-T4.4: Update `tools/validation/__init__.py`**

Append:
```python
from tools.validation import regions_validate  # noqa: F401
```

- [ ] **Step R1-T4.5: Run tests, expect pass**

Run:
```bash
.venv/bin/python -m pytest tests/unit/test_regions_validate.py -v
```
Expected: 6 passed.

- [ ] **Step R1-T4.6: Commit**

```bash
git add tools/validation/regions_validate.py tools/validation/__init__.py \
        tests/unit/test_regions_validate.py
git commit -m "feat(tools/validation): regions_validate for spread regions yaml"
```

---

### Task R1-T5: Wire regions validation into v2 contract tests

**Files:**
- Modify: `~/github/openMagazine/tests/contracts/test_v2_pipelines.py`

- [ ] **Step R1-T5.1: Append the parametrized contract test**

Append to `tests/contracts/test_v2_pipelines.py`:

```python
from tools.validation.regions_validate import validate_regions


def _regions_yamls():
    return sorted(
        (SKILL_ROOT / "library" / "layouts" / "_components")
        .glob("*.regions.yaml")
    )


@pytest.mark.parametrize(
    "regions_path", _regions_yamls(), ids=lambda p: p.name
)
def test_regions_yaml_validates(regions_path):
    errors = validate_regions(regions_path)
    assert errors == [], (
        f"{regions_path.name}: {len(errors)} error(s)\n  "
        + "\n  ".join(errors)
    )
```

This auto-discovers every `*.regions.yaml` that lands later (R2/R4). Today
it parametrizes over an empty list (no yamls yet); future yamls auto-join.

- [ ] **Step R1-T5.2: Run contract tests, expect pass**

Run:
```bash
.venv/bin/python -m pytest tests/contracts/ -v
```
Expected: all green, with the new test reporting `1 deselected` (no
yamls match yet) or simply not parametrizing visibly. Note: pytest emits a
warning when a parametrize list is empty; that's acceptable here because
the list grows as later phases add yamls.

- [ ] **Step R1-T5.3: Commit**

```bash
git add tests/contracts/test_v2_pipelines.py
git commit -m "test(contracts): auto-validate every *.regions.yaml"
```

---

## Phase R2 — Pilot: migrate feature-spread (~1 day, 4 tasks)

First end-to-end vertical slice. Migrates ONE component (feature-spread)
to read regions, leaves the other six on the legacy CSS path.

### Task R2-T1: Write `feature-spread.regions.yaml`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/feature-spread.regions.yaml`

- [ ] **Step R2-T1.1: Write the yaml**

```yaml
schema_version: 1
spread_type: feature-spread
pages_per_instance: 2

regions:
  - id: hero_image
    rect_norm: [0.0, 0.0, 0.5, 1.0]
    role: image
    image_slot: feature_hero
    aspect: "3:4"
    image_prompt_hint: |
      The protagonist subject lives in this region. Sharp focus, primary
      lighting, full color, dominant composition element.

  - id: kicker
    rect_norm: [0.55, 0.08, 0.95, 0.12]
    role: text
    component: Kicker
    text_field: kicker
    image_prompt_hint: "calm zone for a small uppercase mono label"

  - id: accent_rule_top
    rect_norm: [0.55, 0.13, 0.70, 0.135]
    role: accent
    component: AccentRule
    image_prompt_hint: "calm zone for a hairline horizontal rule"

  - id: title
    rect_norm: [0.55, 0.15, 0.95, 0.30]
    role: text
    component: Title
    text_field: title
    image_prompt_hint: |
      Uniform low-detail background. A large display-serif title will be
      overlaid here — keep this region visually quiet.

  - id: lead
    rect_norm: [0.55, 0.33, 0.95, 0.43]
    role: text
    component: Lead
    text_field: lead

  - id: body
    rect_norm: [0.55, 0.46, 0.95, 0.83]
    role: text
    component: BodyWithDropCap
    text_field: body
    component_props:
      drop_cap: true
      hyphenate: true
      align: justify
    image_prompt_hint: "negative space, no important detail behind body text"

  - id: captioned_strip
    rect_norm: [0.55, 0.86, 0.95, 0.98]
    role: image_grid
    image_slots: [feature_captioned.1, feature_captioned.2, feature_captioned.3]
    grid_cols: 3
    image_prompt_hint: |
      Three small 3:2 thumbnails will be placed here. Keep this strip
      visually calm; no large foreground elements.
```

- [ ] **Step R2-T1.2: Validate**

Run:
```bash
.venv/bin/python tools/validation/regions_validate.py \
  library/layouts/_components/feature-spread.regions.yaml
```
Expected output: `✓ feature-spread.regions.yaml: valid`

- [ ] **Step R2-T1.3: Run contract test**

Run:
```bash
.venv/bin/python -m pytest tests/contracts/test_v2_pipelines.py -v
```
Expected: `test_regions_yaml_validates[feature-spread.regions.yaml]` PASSES.

- [ ] **Step R2-T1.4: Commit**

```bash
git add library/layouts/_components/feature-spread.regions.yaml
git commit -m "feat(layouts/regions): feature-spread.regions.yaml (7 regions)"
```

---

### Task R2-T2: Region rendering macros

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/_macros/region.j2.html`

- [ ] **Step R2-T2.1: Create the macro file**

```jinja
{# Render a single region as an absolutely-positioned div inside
   `.spread-bounds`. Dispatches by role to specific component renderers. #}

{% macro render_region(region, sc, slot_path, language, language_default='en') %}
  {%- set lang = language or language_default %}
  {%- set x1, y1, x2, y2 = region.rect_norm %}
  <div class="region region-{{ region.id }}{% if region.component %} region-{{ region.component|lower }}{% endif %}"
       data-component="{{ region.component|default('') }}"
       data-role="{{ region.role }}"
       style="position: absolute;
              left:   {{ '%.2f'|format(x1 * 100) }}%;
              top:    {{ '%.2f'|format(y1 * 100) }}%;
              width:  {{ '%.2f'|format((x2 - x1) * 100) }}%;
              height: {{ '%.2f'|format((y2 - y1) * 100) }}%;
              z-index: {{ region.z_index|default(0) }};
              overflow: hidden;">
    {%- if region.role == 'image' %}
      {{- render_image(region, slot_path) }}
    {%- elif region.role == 'image_grid' %}
      {{- render_image_grid(region, slot_path) }}
    {%- elif region.role == 'text' %}
      {%- set text = (sc[region.text_field] or {}).get(lang, sc[region.text_field]) if sc[region.text_field] is mapping else sc[region.text_field] %}
      {{- render_text_component(region.component, text, region.component_props|default({})) }}
    {%- elif region.role == 'text_decorative' %}
      {{- render_text_component(region.component, '', region.component_props|default({})) }}
    {%- elif region.role == 'accent' %}
      {{- render_accent(region.component, region.component_props|default({})) }}
    {%- elif region.role == 'negative_space' %}
      {# intentionally empty #}
    {%- endif %}
  </div>
{% endmacro %}

{% macro render_image(region, slot_path) %}
  <img src="{{ slot_path(region.image_slot) }}"
       alt="{{ region.image_slot }}"
       style="width: 100%; height: 100%; object-fit: cover; display: block;">
{% endmacro %}

{% macro render_image_grid(region, slot_path) %}
  {%- set cols = region.grid_cols|default(region.image_slots|length) %}
  <div style="display: grid;
              grid-template-columns: repeat({{ cols }}, 1fr);
              gap: 4mm;
              width: 100%; height: 100%;">
    {%- for s in region.image_slots %}
      <img src="{{ slot_path(s) }}"
           alt="{{ s }}"
           style="width: 100%; height: 100%; object-fit: cover; display: block;">
    {%- endfor %}
  </div>
{% endmacro %}

{% macro render_text_component(component, text, props) %}
  {%- if component == 'Kicker' %}
    <span class="kicker">{{ text }}</span>
  {%- elif component == 'Title' %}
    <h2 class="title" style="margin: 0;">{{ text }}</h2>
  {%- elif component == 'Lead' %}
    <p class="lead" style="margin: 0; font-style: italic;">{{ text }}</p>
  {%- elif component == 'Body' %}
    <div class="body{% if props.hyphenate %} body-hyphenate{% endif %}"
         style="{% if props.align %}text-align: {{ props.align }};{% endif %}">
      {%- for para in text.split('\n\n') %}<p>{{ para }}</p>{%- endfor %}
    </div>
  {%- elif component == 'BodyWithDropCap' %}
    <div class="body drop-cap{% if props.hyphenate %} body-hyphenate{% endif %}"
         style="{% if props.align %}text-align: {{ props.align }};{% endif %}">
      {%- for para in text.split('\n\n') %}<p>{{ para }}</p>{%- endfor %}
    </div>
  {%- elif component == 'PullQuote' %}
    <blockquote class="pull-quote" style="margin: 0;">{{ text }}</blockquote>
  {%- elif component == 'Caption' %}
    <figcaption class="caption">{{ text }}</figcaption>
  {%- elif component == 'Folio' %}
    <span class="folio">{{ text }}</span>
  {%- elif component == 'Masthead' %}
    <div class="title title-xl"
         style="font-family: var(--font-display); letter-spacing: 0.04em;">{{ text }}</div>
  {%- elif component == 'CoverLine' %}
    <div class="kicker" style="color: inherit;">{{ text }}</div>
  {%- else %}
    <span>{{ text }}</span>
  {%- endif %}
{% endmacro %}

{% macro render_accent(component, props) %}
  {%- if component == 'AccentRule' %}
    <hr class="accent"
        style="margin: 0;
               border: 0;
               border-top: {{ props.thickness|default('1.5pt') }} solid var(--color-accent);
               width: {{ props.width_pct|default(100) }}%;">
  {%- endif %}
{% endmacro %}
```

- [ ] **Step R2-T2.2: Smoke test the macro renders without Jinja error**

Run:
```bash
.venv/bin/python -c "
import pathlib
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader('library/layouts'),
    autoescape=select_autoescape(['html']),
)
template_str = '''
{% from \"_components/_macros/region.j2.html\" import render_region %}
{{ render_region({\"id\": \"x\", \"rect_norm\": [0, 0, 0.5, 1], \"role\": \"negative_space\"}, {}, lambda s: '/p.png', 'en') }}
'''
print(env.from_string(template_str).render())
"
```
Expected: an HTML snippet printed, no error.

- [ ] **Step R2-T2.3: Commit**

```bash
git add library/layouts/_components/_macros/region.j2.html
git commit -m "feat(layouts/_macros): region.j2.html — render_region dispatch macros"
```

---

### Task R2-T3: Rewrite `feature-spread.html.j2` to use regions

**Files:**
- Modify: `~/github/openMagazine/library/layouts/_components/feature-spread.html.j2`

- [ ] **Step R2-T3.1: Read the existing feature-spread template**

```bash
cat library/layouts/_components/feature-spread.html.j2
```

Capture the current structure so the new version preserves identical
context-variable expectations (`sc`, `spread_idx`, `language`, `images_root`).

- [ ] **Step R2-T3.2: Replace the file**

Overwrite `library/layouts/_components/feature-spread.html.j2` with:

```jinja
{%- from '_components/_macros/region.j2.html' import render_region %}
{%- import 'yaml.j2' as yaml_helper with context %}{# placeholder: actual yaml loading happens via context.regions #}

{# Expected context:
   - sc                  : article.spread_copy entry for this spread
   - spread_idx          : 1-indexed spread number
   - regions             : list of region dicts from feature-spread.regions.yaml
                           (injected by WeasyprintCompose, see Task R2-T4)
   - images_root         : str — where output/<slug>/images/ lives
   - language            : 'en' | 'zh'
#}

{%- macro slot_path(slot_id) -%}
  {{ images_root }}/spread-{{ '%02d'|format(spread_idx) }}/{{ slot_id }}.png
{%- endmacro %}

<section class="spread feature-spread" data-spread-idx="{{ spread_idx }}">
  <div class="spread-bounds"
       style="position: relative; height: var(--content-h, 250mm); overflow: hidden;">
    {%- for region in regions %}
      {{ render_region(region, sc, slot_path, language) }}
    {%- endfor %}
  </div>
</section>
```

- [ ] **Step R2-T3.3: Add `--content-h` CSS variable to `_base.html.j2`**

Inspect `_base.html.j2`'s `:root { ... }` block. If `--content-h` is not
defined, add it next to other layout variables. The value should be
`297mm - {{ brand.print_specs.margin_top_mm }}mm - {{ brand.print_specs.margin_bottom_mm }}mm`.

In `library/layouts/_base.html.j2`, inside the `:root {}` block at the top
of the `<style>` section, add:

```css
:root {
  /* … existing vars … */
  --content-h: calc(297mm
                    - {{ brand.print_specs.margin_top_mm }}mm
                    - {{ brand.print_specs.margin_bottom_mm }}mm);
}
```

If `:root` already exists, append the `--content-h` line; do not duplicate.

- [ ] **Step R2-T3.4: Commit**

```bash
git add library/layouts/_components/feature-spread.html.j2 \
        library/layouts/_base.html.j2
git commit -m "feat(layouts): feature-spread.html.j2 rewritten on regions macro"
```

---

### Task R2-T4: Inject regions into compose stage

**Files:**
- Modify: `~/github/openMagazine/tools/pdf/weasyprint_compose.py`
- Modify: `~/github/openMagazine/library/layouts/editorial-16page.html.j2`

- [ ] **Step R2-T4.1: Make WeasyprintCompose load regions per spread**

Read `tools/pdf/weasyprint_compose.py`. Locate the function that builds
the Jinja context for each spread (the render loop). Inject a `regions`
list per spread by calling `regions_loader.load_regions(spread_type)` and
catching `RegionsNotFoundError` (fall back to empty list → legacy CSS
path renders).

Add near the top of `tools/pdf/weasyprint_compose.py`:

```python
from lib.regions_loader import load_regions, RegionsNotFoundError
```

In the spread-rendering loop (search for the place where each spread's
context is built), add:

```python
spread_type = sc["type"]
try:
    regions_doc = load_regions(spread_type)
    spread_regions = regions_doc["regions"]
except RegionsNotFoundError:
    spread_regions = []   # legacy CSS path
context["regions"] = spread_regions
```

- [ ] **Step R2-T4.2: Update `editorial-16page.html.j2` to pass regions**

In `library/layouts/editorial-16page.html.j2`, find the dispatch chain
(`{% if sc.type == "feature-spread" %}{% include ... %}{% endif %}`). For
the feature-spread branch, ensure the `regions` variable is in scope when
including the component:

```jinja
{% elif sc.type == "feature-spread" %}
  {% include '_components/feature-spread.html.j2' %}
```

Jinja `{% include %}` shares the parent context, so `regions` set in
weasyprint_compose flows through automatically. If the existing dispatch
uses `with context` or explicit variable passing, preserve that pattern.

- [ ] **Step R2-T4.3: Run integration test**

Run:
```bash
.venv/bin/python -m pytest tests/integration/test_render_dry_run.py -v
```
Expected: PASS. Page count and PNG size sanity unchanged.

If FAIL: open `tests/<tmp>/issue/magazine.html` and inspect the rendered
`<section class="spread feature-spread">` block. Common failure modes:
- `regions` undefined in context → step R2-T4.1 didn't run / variable name wrong.
- Empty `regions` list → `load_regions` couldn't find the yaml (path bug).
- Region rects render but content invisible → text fields in placeholder
  article are empty strings, which is fine; verify the `<div class="region">`
  divs exist in the HTML output.

- [ ] **Step R2-T4.4: Add a focused assertion to the integration test**

Append to `tests/integration/test_render_dry_run.py`:

```python
def test_feature_spread_renders_via_regions(issue_dir):
    """Regions-driven feature-spread emits region divs (not legacy
    .grid-2-7-5 markup)."""
    # Load fixtures
    layout = yaml.safe_load((SKILL_ROOT / "library/layouts/editorial-16page.yaml").read_text())
    brand = yaml.safe_load((SKILL_ROOT / "library/brands/meow-life.yaml").read_text())
    article = yaml.safe_load((SKILL_ROOT / "library/articles/cosmos-luna-may-2026.yaml").read_text())

    images_dir = issue_dir / "images"
    _make_placeholder_pngs(images_dir, layout)

    tool = WeasyprintCompose()
    layout_j2 = SKILL_ROOT / "library/layouts/editorial-16page.html.j2"
    out_pdf = issue_dir / "magazine.pdf"
    tool.render_template(
        layout_j2=layout_j2,
        context={
            "layout": layout, "brand": brand, "article": article,
            "spec": {"slug": "test"},
            "language": brand.get("default_language", "en"),
            "issue_dir": str(issue_dir), "images_root": str(images_dir),
        },
        out_path=out_pdf,
        save_html=True,
    )
    html = out_pdf.with_suffix(".html").read_text(encoding="utf-8")
    # Region divs present
    assert 'class="region region-hero_image"' in html
    assert 'class="region region-title' in html  # may have region-title region-title together
    # Region count for a feature-spread: 7 regions × 3 feature-spread
    # instances in cosmos-luna-may-2026 = 21 region divs (minimum).
    # Use 'data-role=' as the anchor since region class names can chain.
    assert html.count('data-role="image"') >= 3      # 3 hero_image
    assert html.count('data-role="image_grid"') >= 3 # 3 captioned_strips
```

Run:
```bash
.venv/bin/python -m pytest tests/integration/test_render_dry_run.py -v
```
Expected: 2 passed.

- [ ] **Step R2-T4.5: Commit**

```bash
git add tools/pdf/weasyprint_compose.py \
        library/layouts/editorial-16page.html.j2 \
        tests/integration/test_render_dry_run.py
git commit -m "feat(compose): inject regions into spread context; verify in dry-run"
```

---

## Phase R3 — Image prompts get regions context (~half day, 3 tasks)

Adds the regions-context block to upscale prompts. **This is the phase
that most benefits from a live smoke run first** — the prompt format
should be tuned by observed model behavior. Land R1 + R2 first; pause
here for a smoke run; resume.

### Task R3-T1: Extend `build_upscale_prompt` with `regions_context`

**Files:**
- Modify: `~/github/openMagazine/lib/prompt_builder_v2.py`
- Modify: `~/github/openMagazine/tests/unit/test_prompt_builder_v2.py`

- [ ] **Step R3-T1.1: Write the failing test**

Append to `tests/unit/test_prompt_builder_v2.py`:

```python
def test_build_upscale_prompt_with_regions_context(spec, layers):
    regions_context = {
        "own_region": {
            "id": "hero_image",
            "rect_norm": [0.0, 0.0, 0.5, 1.0],
            "role": "image",
            "image_slot": "feature_hero",
            "image_prompt_hint": "subject lives here, sharp focus",
        },
        "sibling_regions": [
            {
                "id": "title",
                "rect_norm": [0.55, 0.15, 0.95, 0.30],
                "role": "text",
                "component": "Title",
                "image_prompt_hint": "uniform low-detail background",
            },
            {
                "id": "captioned_strip",
                "rect_norm": [0.55, 0.86, 0.95, 0.98],
                "role": "image_grid",
                "image_prompt_hint": "calm strip",
            },
        ],
    }
    p = build_upscale_prompt(
        role="portrait", spec=spec, layers=layers,
        slot_id="spread-03.feature_hero",
        scene="character at boulder, hand on rock",
        aspect="3:4",
        regions_context=regions_context,
    )
    # Own region declared
    assert "hero_image" in p
    assert "subject lives here" in p
    # Sibling regions declared and explicitly off-limits
    assert "title" in p
    assert "captioned_strip" in p
    assert "uniform low-detail background" in p
    # No unfilled placeholders
    assert "{{" not in p


def test_build_upscale_prompt_without_regions_context_unchanged(spec, layers):
    """Backward compatibility: omit regions_context → prompt body matches
    the v0.3.0 shape (no regions section)."""
    p_old = build_upscale_prompt(
        role="portrait", spec=spec, layers=layers,
        slot_id="spread-03.feature_hero",
        scene="character at boulder",
        aspect="3:4",
    )
    p_new = build_upscale_prompt(
        role="portrait", spec=spec, layers=layers,
        slot_id="spread-03.feature_hero",
        scene="character at boulder",
        aspect="3:4",
        regions_context=None,
    )
    assert p_old == p_new
    assert "sibling regions" not in p_old.lower()
```

- [ ] **Step R3-T1.2: Run, expect failure**

Run:
```bash
.venv/bin/python -m pytest tests/unit/test_prompt_builder_v2.py -v
```
Expected: 2 new tests FAIL (no `regions_context` kwarg or no injection).

- [ ] **Step R3-T1.3: Modify `lib/prompt_builder_v2.py`**

Modify `build_upscale_prompt` to accept an optional `regions_context`
keyword argument and prepend a regions block when provided:

```python
def build_upscale_prompt(
    *,
    role: str,
    spec: dict,
    layers: dict,
    slot_id: str,
    scene: str,
    aspect: str,
    regions_context: dict | None = None,   # NEW
) -> str:
    if role not in ROLE_TEMPLATES:
        raise ValueError(f"unknown role {role!r}; expected one of {list(ROLE_TEMPLATES)}")
    template = _read_template(ROLE_TEMPLATES[role])
    pmap = build_placeholder_map(spec, layers)
    pmap["{{SCENE}}"] = scene
    pmap["{{ASPECT}}"] = aspect
    pmap["{{SLOT_ID}}"] = slot_id
    rendered = _apply(template, pmap)

    if regions_context:
        rendered = _render_regions_block(regions_context) + "\n\n" + rendered

    return rendered


def _render_regions_block(ctx: dict) -> str:
    own = ctx["own_region"]
    own_id = own["id"]
    own_rect = own["rect_norm"]
    own_hint = own.get("image_prompt_hint", "")

    lines = [
        f"This image fills region '{own_id}' at rect "
        f"({own_rect[0]:.2f}, {own_rect[1]:.2f}, {own_rect[2]:.2f}, {own_rect[3]:.2f}). "
        f"{own_hint.strip()}",
        "",
        "The same spread contains the following sibling regions that will "
        "receive HTML/PDF overlays after generation. DO NOT paint readable "
        "text or layout chrome into these areas; keep them calm and low-detail:",
        "",
    ]
    for r in ctx.get("sibling_regions", []):
        rid = r["id"]
        rect = r["rect_norm"]
        role = r["role"]
        hint = r.get("image_prompt_hint", "").strip()
        lines.append(
            f"- region '{rid}' (role={role}, rect "
            f"({rect[0]:.2f}, {rect[1]:.2f}, {rect[2]:.2f}, {rect[3]:.2f}))"
            + (f": {hint}" if hint else "")
        )
    return "\n".join(lines)
```

- [ ] **Step R3-T1.4: Run tests, expect pass**

Run:
```bash
.venv/bin/python -m pytest tests/unit/test_prompt_builder_v2.py -v
```
Expected: 7 passed (5 existing + 2 new).

- [ ] **Step R3-T1.5: Commit**

```bash
git add lib/prompt_builder_v2.py tests/unit/test_prompt_builder_v2.py
git commit -m "feat(lib): build_upscale_prompt accepts regions_context for region-aware prompts"
```

---

### Task R3-T2: Storyboard prompt gets per-spread regions context

**Files:**
- Modify: `~/github/openMagazine/lib/prompt_builder_v2.py`
- Modify: `~/github/openMagazine/tests/unit/test_prompt_builder_v2.py`

- [ ] **Step R3-T2.1: Write the failing test**

Append to `tests/unit/test_prompt_builder_v2.py`:

```python
def test_build_storyboard_v2_with_regions_by_spread(spec, layers):
    plan = {
        "outer_aspect": "2:3",
        "outer_size_px": [1024, 1536],
        "grid": {"rows": 1, "cols": 2},
        "cells": [
            {"slot_id": "spread-03.feature_hero", "row": 0, "col": 0,
             "rowspan": 1, "colspan": 1, "aspect": "3:4",
             "bbox_px": [0, 0, 512, 1536], "page_label": "01"},
            {"slot_id": "spread-09.back_coda", "row": 0, "col": 1,
             "rowspan": 1, "colspan": 1, "aspect": "2:3",
             "bbox_px": [512, 0, 512, 1536], "page_label": "02"},
        ],
    }
    regions_by_spread_type = {
        "feature-spread": [
            {"id": "hero_image", "rect_norm": [0, 0, 0.5, 1], "role": "image",
             "image_slot": "feature_hero", "aspect": "3:4"},
            {"id": "title", "rect_norm": [0.55, 0.15, 0.95, 0.3], "role": "text",
             "component": "Title", "text_field": "title"},
        ],
    }
    spread_type_by_idx = {3: "feature-spread", 9: "back-cover"}
    p = build_storyboard_prompt_v2(
        spec, layers,
        plan=plan,
        scenes_by_slot={"spread-03.feature_hero": "hero", "spread-09.back_coda": "coda"},
        regions_by_spread_type=regions_by_spread_type,
        spread_type_by_idx=spread_type_by_idx,
    )
    assert "spread-03.feature_hero" in p
    assert "spread 3 region layout" in p.lower() or "feature-spread region layout" in p.lower()
    # back-cover has no regions yaml in this test → no layout block for spread 9
    assert "spread-09.back_coda" in p
    assert "{{" not in p
```

- [ ] **Step R3-T2.2: Run, expect failure**

Run:
```bash
.venv/bin/python -m pytest tests/unit/test_prompt_builder_v2.py::test_build_storyboard_v2_with_regions_by_spread -v
```
Expected: FAIL (`build_storyboard_prompt_v2` doesn't accept the new kwargs).

- [ ] **Step R3-T2.3: Extend `build_storyboard_prompt_v2`**

Update the signature and inject a per-spread layout block:

```python
def build_storyboard_prompt_v2(
    spec: dict,
    layers: dict,
    *,
    plan: dict,
    scenes_by_slot: dict[str, str],
    regions_by_spread_type: dict[str, list[dict]] | None = None,
    spread_type_by_idx: dict[int, str] | None = None,
) -> str:
    template = _read_template("storyboard_v2.prompt.md")
    pmap = build_placeholder_map(spec, layers)

    role_lookup = _build_role_lookup(layers)
    spread_type_by_idx = spread_type_by_idx or {}
    regions_by_spread_type = regions_by_spread_type or {}

    cell_lines = []
    layouts_seen: dict[int, str] = {}
    for cell in plan["cells"]:
        slot_id = cell["slot_id"]
        scene = scenes_by_slot.get(slot_id, "")
        role = role_lookup.get(slot_id) or role_lookup.get(_short_id(slot_id), "portrait")
        line = (
            f"{cell['page_label']} - {slot_id} "
            f"({cell['aspect']} {role}) - {scene}"
        ).rstrip(" -")
        cell_lines.append(line)
        # Track unique spread indices for layout block
        try:
            spread_idx = int(slot_id.split(".")[0].replace("spread-", ""))
            layouts_seen.setdefault(spread_idx, spread_type_by_idx.get(spread_idx, ""))
        except (ValueError, IndexError):
            pass

    pmap["{{OUTER_W}}"] = str(plan["outer_size_px"][0])
    pmap["{{OUTER_H}}"] = str(plan["outer_size_px"][1])
    pmap["{{GRID_ROWS}}"] = str(plan.get("grid", {}).get("rows", "?"))
    pmap["{{GRID_COLS}}"] = str(plan.get("grid", {}).get("cols", "?"))
    pmap["{{CELL_COUNT}}"] = str(len(plan["cells"]))
    pmap["{{CELL_LIST}}"] = "\n".join(cell_lines)
    pmap["{{SPREAD_LAYOUTS_BLOCK}}"] = _build_spread_layouts_block(
        layouts_seen, regions_by_spread_type
    )

    rendered = _apply(template, pmap)
    # If template doesn't use {{SPREAD_LAYOUTS_BLOCK}}, append at the end
    if pmap["{{SPREAD_LAYOUTS_BLOCK}}"] and "{{SPREAD_LAYOUTS_BLOCK}}" not in template:
        rendered = rendered.rstrip() + "\n\n" + pmap["{{SPREAD_LAYOUTS_BLOCK}}"]
    return rendered


def _build_spread_layouts_block(
    layouts_seen: dict[int, str],
    regions_by_spread_type: dict[str, list[dict]],
) -> str:
    """Render a 'Spread N (type) region layout:' block per unique spread."""
    parts = []
    for spread_idx, spread_type in sorted(layouts_seen.items()):
        if not spread_type or spread_type not in regions_by_spread_type:
            continue
        parts.append(f"Spread {spread_idx} ({spread_type}) region layout:")
        for r in regions_by_spread_type[spread_type]:
            x1, y1, x2, y2 = r["rect_norm"]
            hint = (r.get("image_prompt_hint") or "").strip()
            parts.append(
                f"- '{r['id']}' (role={r['role']}, rect "
                f"({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f}))"
                + (f": {hint}" if hint else "")
            )
        parts.append("")
    return "\n".join(parts).rstrip()
```

- [ ] **Step R3-T2.4: Run tests, expect pass**

Run:
```bash
.venv/bin/python -m pytest tests/unit/test_prompt_builder_v2.py -v
```
Expected: 8 passed.

- [ ] **Step R3-T2.5: Commit**

```bash
git add lib/prompt_builder_v2.py tests/unit/test_prompt_builder_v2.py
git commit -m "feat(lib): build_storyboard_prompt_v2 accepts per-spread regions context"
```

---

### Task R3-T3: Wire regions into directors

**Files:**
- Modify: `~/github/openMagazine/skills/pipelines/editorial-16page/storyboard-director.md`
- Modify: `~/github/openMagazine/skills/pipelines/editorial-16page/upscale-director.md`

- [ ] **Step R3-T3.1: Modify storyboard-director.md**

Find the Python block that calls `build_storyboard_prompt_v2(...)`. Just
before that call, add the regions loading:

```python
# Load per-spread regions yamls (gracefully skip spreads without yamls
# during migration). Build the spread_type → regions map and the
# spread_idx → spread_type map for the prompt builder.
from lib.regions_loader import load_regions, RegionsNotFoundError

regions_by_spread_type: dict[str, list[dict]] = {}
spread_type_by_idx: dict[int, str] = {}
for sp in layers["layout"]["spread_plan"]:
    spread_type_by_idx[int(sp["idx"])] = sp["type"]
    if sp["type"] in regions_by_spread_type:
        continue
    try:
        regions_doc = load_regions(sp["type"])
        regions_by_spread_type[sp["type"]] = regions_doc["regions"]
    except RegionsNotFoundError:
        pass  # legacy CSS spread; no regions block

prompt = build_storyboard_prompt_v2(
    spec, layers,
    plan=plan,
    scenes_by_slot=scenes_by_slot,
    regions_by_spread_type=regions_by_spread_type,
    spread_type_by_idx=spread_type_by_idx,
)
```

- [ ] **Step R3-T3.2: Modify upscale-director.md**

Find the per-slot loop that calls `build_upscale_prompt(...)`. Before the
call, build `regions_context`:

```python
from lib.regions_loader import regions_for_image_prompt, RegionsNotFoundError

# Build spread_idx → spread_type once
spread_type_by_idx = {
    int(sp["idx"]): sp["type"]
    for sp in layers["layout"]["spread_plan"]
}

# … inside the for s in layers["layout"]["image_slots"] loop … #
spread_type = spread_type_by_idx[s["spread_idx"]]
try:
    regions_context = regions_for_image_prompt(spread_type, short)
except (RegionsNotFoundError, ValueError):
    regions_context = None  # legacy CSS spread or slot not in regions yaml

prompt = build_upscale_prompt(
    role=s["role"], spec=spec, layers=layers,
    slot_id=full, scene=scene, aspect=s["aspect"],
    regions_context=regions_context,
)
```

- [ ] **Step R3-T3.3: Commit**

```bash
git add skills/pipelines/editorial-16page/storyboard-director.md \
        skills/pipelines/editorial-16page/upscale-director.md
git commit -m "docs(skills/pipelines): editorial-16page directors now load regions context"
```

---

## Phase R4 — Migrate remaining 6 components (~1.5 days, 6 tasks)

Each task follows the same template as Task R2-T1 + R2-T3 but applied to
a different spread type. All 6 tasks are mutually independent and can run
in parallel sub-agents.

### Task R4-T1: Migrate `cover`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/cover.regions.yaml`
- Modify: `~/github/openMagazine/library/layouts/_components/cover.html.j2`

- [ ] **Step R4-T1.1: Read existing `cover.html.j2`** to capture current dimensions

```bash
cat library/layouts/_components/cover.html.j2
```

Note the current rectangle positions (cover hero full-bleed; masthead
near top; cover line near bottom).

- [ ] **Step R4-T1.2: Write `cover.regions.yaml`**

```yaml
schema_version: 1
spread_type: cover
pages_per_instance: 1

regions:
  - id: cover_hero
    rect_norm: [0.0, 0.0, 1.0, 1.0]
    role: image
    image_slot: cover_hero
    aspect: "3:4"
    image_prompt_hint: |
      Full-bleed hero image. Keep top ~12% and bottom ~25% relatively
      calm for masthead and cover-line overlays.

  - id: masthead
    rect_norm: [0.05, 0.04, 0.95, 0.12]
    role: text
    component: Masthead
    text_field: cover_kicker
    z_index: 10

  - id: cover_kicker
    rect_norm: [0.06, 0.78, 0.94, 0.83]
    role: text
    component: CoverLine
    text_field: cover_kicker
    component_props:
      align: left
    z_index: 10

  - id: cover_line
    rect_norm: [0.06, 0.84, 0.94, 0.95]
    role: text
    component: CoverLine
    text_field: cover_line
    component_props:
      align: left
    z_index: 10
```

Note: the cover spread reads `text_field` from `article.cover_line` /
`article.cover_kicker` — article-level fields, NOT `spread_copy[0]` (see
`docs/SCHEMA_V2_MIGRATION.md`). The rendering macro must handle this; for
this migration, the `feature-spread.html.j2` style `sc` accessor will not
work as-is — see step R4-T1.4.

- [ ] **Step R4-T1.3: Validate**

```bash
.venv/bin/python tools/validation/regions_validate.py \
  library/layouts/_components/cover.regions.yaml
```
Expected: `✓ cover.regions.yaml: valid`.

- [ ] **Step R4-T1.4: Rewrite `cover.html.j2`**

Cover text fields live on `article.*` (not `sc.*`), so the include needs
to pass an `sc`-like proxy. Overwrite `cover.html.j2`:

```jinja
{%- from '_components/_macros/region.j2.html' import render_region %}

{# Cover-specific: text_field lookups go to article (root), not spread_copy[0].
   Build a proxy dict so render_region's sc[field] accessor works. #}
{%- set cover_sc = {
  'cover_line':   article.cover_line,
  'cover_kicker': article.cover_kicker,
} %}

{%- macro slot_path(slot_id) -%}
  {{ images_root }}/spread-01/{{ slot_id }}.png
{%- endmacro %}

<section class="spread cover" data-spread-idx="1">
  <div class="spread-bounds"
       style="position: relative; height: var(--content-h, 250mm); overflow: hidden;">
    {%- for region in regions %}
      {{ render_region(region, cover_sc, slot_path, language) }}
    {%- endfor %}
  </div>
</section>
```

- [ ] **Step R4-T1.5: Run integration test**

```bash
.venv/bin/python -m pytest tests/integration/test_render_dry_run.py -v
```
Expected: PASS.

- [ ] **Step R4-T1.6: Commit**

```bash
git add library/layouts/_components/cover.regions.yaml \
        library/layouts/_components/cover.html.j2
git commit -m "feat(layouts): migrate cover to regions-driven layout"
```

---

### Task R4-T2: Migrate `toc`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/toc.regions.yaml`
- Modify: `~/github/openMagazine/library/layouts/_components/toc.html.j2`

- [ ] **Step R4-T2.1: Write `toc.regions.yaml`**

```yaml
schema_version: 1
spread_type: toc
pages_per_instance: 2

regions:
  - id: section_label
    rect_norm: [0.05, 0.10, 0.45, 0.14]
    role: text
    component: Kicker
    text_field: section_label   # if missing on sc, renders empty string
    component_props: {align: left}

  - id: accent_rule_left
    rect_norm: [0.05, 0.16, 0.30, 0.165]
    role: accent
    component: AccentRule

  - id: section_title
    rect_norm: [0.05, 0.20, 0.45, 0.36]
    role: text
    component: Title
    text_field: title_override   # falls back to "Contents" if absent
    component_props: {align: left}

  - id: toc_list
    rect_norm: [0.55, 0.20, 0.95, 0.90]
    role: text_decorative
    component: TocList
    component_props:
      align: left

  - id: folio_left
    rect_norm: [0.05, 0.97, 0.20, 1.0]
    role: text_decorative
    component: Folio

  - id: folio_right
    rect_norm: [0.80, 0.97, 0.95, 1.0]
    role: text_decorative
    component: Folio
```

Note: this adds a new component `TocList` to the registry. Update
`library/components/registry.yaml`:

```yaml
TocList:
  description: Table-of-contents list (page numbers + section titles)
  typography_slot: body
  accepts_props: [align]
```

And `library/layouts/_components/_macros/region.j2.html`'s `render_text_component`
macro: add a branch for `TocList` that walks `sc.table_of_contents`.

- [ ] **Step R4-T2.2: Validate**

```bash
.venv/bin/python tools/validation/regions_validate.py \
  library/layouts/_components/toc.regions.yaml
```
Expected: `✓ toc.regions.yaml: valid`.

- [ ] **Step R4-T2.3: Rewrite `toc.html.j2`** following the same pattern as cover.

- [ ] **Step R4-T2.4: Run integration test + commit**

```bash
.venv/bin/python -m pytest tests/integration/test_render_dry_run.py -v
git add library/layouts/_components/toc.regions.yaml \
        library/layouts/_components/toc.html.j2 \
        library/layouts/_components/_macros/region.j2.html \
        library/components/registry.yaml
git commit -m "feat(layouts): migrate toc to regions-driven layout + add TocList component"
```

---

### Task R4-T3: Migrate `pull-quote`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/pull-quote.regions.yaml`
- Modify: `~/github/openMagazine/library/layouts/_components/pull-quote.html.j2`

- [ ] **Step R4-T3.1: Write `pull-quote.regions.yaml`**

```yaml
schema_version: 1
spread_type: pull-quote
pages_per_instance: 2

regions:
  - id: env_image
    rect_norm: [0.0, 0.0, 1.0, 1.0]
    role: image
    image_slot: pullquote_environment
    aspect: "16:10"
    image_prompt_hint: |
      Full-bleed environmental landscape. Center 50% bottom-third must be
      visually calm — a large quote will overlay there.

  - id: gradient_overlay
    rect_norm: [0.0, 0.0, 1.0, 1.0]
    role: accent
    component: VerticalGradient
    component_props:
      direction: bottom
      strength: 0.5
    z_index: 5

  - id: quote
    rect_norm: [0.10, 0.55, 0.90, 0.78]
    role: text
    component: PullQuote
    text_field: quote
    component_props: {align: center}
    z_index: 10

  - id: quote_attribution
    rect_norm: [0.10, 0.80, 0.90, 0.85]
    role: text
    component: Caption
    text_field: quote_attribution
    component_props: {align: center}
    z_index: 10
```

Add `VerticalGradient` to the component registry. Update render_accent to
handle it (linear-gradient on the div's CSS background).

- [ ] **Step R4-T3.2: Validate, rewrite j2, run integration test, commit**

Same pattern as R4-T2.4.

```bash
git commit -m "feat(layouts): migrate pull-quote to regions-driven layout"
```

---

### Task R4-T4: Migrate `portrait-wall`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/portrait-wall.regions.yaml`
- Modify: `~/github/openMagazine/library/layouts/_components/portrait-wall.html.j2`

- [ ] **Step R4-T4.1: Write `portrait-wall.regions.yaml`**

```yaml
schema_version: 1
spread_type: portrait-wall
pages_per_instance: 2

regions:
  - id: title
    rect_norm: [0.05, 0.05, 0.95, 0.09]
    role: text
    component: Kicker
    text_field: title
    component_props: {align: left}

  - id: accent_rule
    rect_norm: [0.05, 0.10, 0.30, 0.105]
    role: accent
    component: AccentRule

  - id: portrait_grid
    rect_norm: [0.05, 0.13, 0.95, 0.95]
    role: image_grid
    image_slots:
      - portrait_wall.1
      - portrait_wall.2
      - portrait_wall.3
      - portrait_wall.4
      - portrait_wall.5
      - portrait_wall.6
    grid_cols: 3
    image_prompt_hint: |
      Six 1:1 square portraits arranged in 3×2. Each portrait must have
      consistent framing — subject centered, similar tightness, matched
      lighting direction.
```

Captions are rendered inside each thumbnail via render_image_grid; needs
extension so the grid macro can render per-slot caption from
`sc.captions[index]`. Add caption support to render_image_grid:

```jinja
{% macro render_image_grid(region, sc, slot_path) %}
  {%- set cols = region.grid_cols|default(region.image_slots|length) %}
  <div style="display: grid;
              grid-template-columns: repeat({{ cols }}, 1fr);
              gap: 4mm;
              width: 100%; height: 100%;">
    {%- for s in region.image_slots %}
      {%- set caption = (sc.captions[loop.index0] if sc.captions and loop.index0 < sc.captions|length else None) %}
      <figure style="display: flex; flex-direction: column; gap: 2mm; margin: 0;">
        <img src="{{ slot_path(s) }}"
             alt="{{ s }}"
             style="width: 100%; height: 100%; object-fit: cover; display: block;">
        {%- if caption %}
          <figcaption class="caption">{{ caption[language] if caption is mapping else caption }}</figcaption>
        {%- endif %}
      </figure>
    {%- endfor %}
  </div>
{% endmacro %}
```

This requires passing `sc` into `render_image_grid`. Update render_region
to pass `sc` through.

- [ ] **Step R4-T4.2: Validate, rewrite j2, run integration test, commit**

```bash
git commit -m "feat(layouts): migrate portrait-wall to regions-driven layout"
```

---

### Task R4-T5: Migrate `colophon`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/colophon.regions.yaml`
- Modify: `~/github/openMagazine/library/layouts/_components/colophon.html.j2`

- [ ] **Step R4-T5.1: Write `colophon.regions.yaml`**

```yaml
schema_version: 1
spread_type: colophon
pages_per_instance: 2

regions:
  - id: section_label
    rect_norm: [0.05, 0.10, 0.45, 0.13]
    role: text
    component: Kicker
    text_field: section_label
    component_props: {align: left}

  - id: accent_rule
    rect_norm: [0.05, 0.15, 0.30, 0.155]
    role: accent
    component: AccentRule

  - id: credits_block
    rect_norm: [0.05, 0.20, 0.45, 0.95]
    role: text_decorative
    component: CreditsBlock
    component_props: {align: left}

  - id: right_quote
    rect_norm: [0.55, 0.30, 0.95, 0.70]
    role: text_decorative
    component: PullQuote
    component_props: {align: left}
```

Add `CreditsBlock` to the component registry. Renderer walks
`sc.credits` (photographer / art_direction / printing / copyright /
contact) and emits one stack per language.

- [ ] **Step R4-T5.2: Validate, rewrite j2, run integration test, commit**

```bash
git commit -m "feat(layouts): migrate colophon to regions-driven layout"
```

---

### Task R4-T6: Migrate `back-cover`

**Files:**
- Create: `~/github/openMagazine/library/layouts/_components/back-cover.regions.yaml`
- Modify: `~/github/openMagazine/library/layouts/_components/back-cover.html.j2`

- [ ] **Step R4-T6.1: Write `back-cover.regions.yaml`**

```yaml
schema_version: 1
spread_type: back-cover
pages_per_instance: 1

regions:
  - id: back_coda
    rect_norm: [0.0, 0.0, 1.0, 1.0]
    role: image
    image_slot: back_coda
    aspect: "2:3"
    image_prompt_hint: |
      Full-bleed quiet coda image. Keep bottom 30% calm for the optional
      closing quote overlay.

  - id: gradient_overlay
    rect_norm: [0.0, 0.0, 1.0, 1.0]
    role: accent
    component: VerticalGradient
    component_props:
      direction: bottom
      strength: 0.55
    z_index: 5

  - id: closing_quote
    rect_norm: [0.10, 0.70, 0.90, 0.85]
    role: text
    component: PullQuote
    text_field: quote
    component_props: {align: center}
    z_index: 10

  - id: closing_attribution
    rect_norm: [0.10, 0.87, 0.90, 0.92]
    role: text
    component: Caption
    text_field: quote_attribution
    component_props: {align: center}
    z_index: 10
```

- [ ] **Step R4-T6.2: Validate, rewrite j2, run integration test, commit**

```bash
git commit -m "feat(layouts): migrate back-cover to regions-driven layout"
```

---

## Phase R5 — Cleanup + docs (~half day, 4 tasks)

### Task R5-T1: Update `overlay-safe-layout.md` with subsumed-by banner

**Files:**
- Modify: `~/github/openMagazine/skills/meta/overlay-safe-layout.md`

- [ ] **Step R5-T1.1: Prepend the banner**

At the top of `skills/meta/overlay-safe-layout.md`, after the `# title`
line, insert:

```markdown
> **Status as of v0.3.1:** This skill's concept (shared layout contract
> between image gen and HTML overlay) has been promoted into a first-class
> data layer. See [regions-as-shared-contract spec](../../docs/superpowers/specs/2026-05-11-regions-as-shared-contract-design.md)
> and the per-spread `library/layouts/_components/<type>.regions.yaml`
> files. This skill remains as the high-level rationale doc; the
> `theme.page_overlay_contracts` field is deprecated in v2 paths and
> kept only for legacy v1 (smoke-test-4page) compatibility.
```

- [ ] **Step R5-T1.2: Commit**

```bash
git add skills/meta/overlay-safe-layout.md
git commit -m "docs(skills/meta): overlay-safe-layout banner — subsumed by regions"
```

---

### Task R5-T2: Write `docs/regions-reference.md`

**Files:**
- Create: `~/github/openMagazine/docs/regions-reference.md`

- [ ] **Step R5-T2.1: Write the reference**

```markdown
# Regions Reference

Every editorial spread is composed of **regions** — named, coordinate-
positioned bounding boxes that all three consumers (image gen, HTML
render, article copy validation) read from one file.

See [`docs/superpowers/specs/2026-05-11-regions-as-shared-contract-design.md`](superpowers/specs/2026-05-11-regions-as-shared-contract-design.md)
for the design rationale. This page is the catalogue.

## Where each spread's regions live

| Spread type | Regions file |
|---|---|
| `cover` | `library/layouts/_components/cover.regions.yaml` |
| `toc` | `library/layouts/_components/toc.regions.yaml` |
| `feature-spread` | `library/layouts/_components/feature-spread.regions.yaml` |
| `pull-quote` | `library/layouts/_components/pull-quote.regions.yaml` |
| `portrait-wall` | `library/layouts/_components/portrait-wall.regions.yaml` |
| `colophon` | `library/layouts/_components/colophon.regions.yaml` |
| `back-cover` | `library/layouts/_components/back-cover.regions.yaml` |

## Region shape

| Field | Type | Role |
|---|---|---|
| `id` | string | Stable identifier, used in CSS class + sidecar JSON |
| `rect_norm` | `[x1, y1, x2, y2]` in `[0,1]` | Bounding box relative to spread |
| `role` | enum | `image` / `image_grid` / `text` / `text_decorative` / `accent` / `negative_space` |
| `image_slot` | string | (image role) name from `layout.image_slots[*].id` |
| `image_slots` | list | (image_grid role) ordered list of slot names |
| `component` | string | (text/accent role) name from `library/components/registry.yaml` |
| `text_field` | string | (text role) field name from article `spread_copy` |
| `component_props` | object | per-component customization |
| `image_prompt_hint` | string | free text passed to the image gen prompt |
| `z_index` | int | stacking when regions overlap (default 0) |

## Adding a new spread type

1. Write `library/layouts/_components/<type>.regions.yaml`.
2. Run `python tools/validation/regions_validate.py library/layouts/_components/<type>.regions.yaml`.
3. Write `library/layouts/_components/<type>.html.j2` using the regions
   render macro (see `_macros/region.j2.html`).
4. Add a `{% elif sc.type == "<type>" %}` branch in `editorial-*.html.j2`.
5. Update this catalogue.
6. Run `tests/contracts/test_v2_pipelines.py` — the new yaml is auto-
   discovered and validated.
```

- [ ] **Step R5-T2.2: Commit**

```bash
git add docs/regions-reference.md
git commit -m "docs: regions-reference.md catalogue + authoring guide"
```

---

### Task R5-T3: Write `docs/component-registry-reference.md`

**Files:**
- Create: `~/github/openMagazine/docs/component-registry-reference.md`

- [ ] **Step R5-T3.1: Write the doc**

```markdown
# Component Registry Reference

Every region with `role: text`, `text_decorative`, or `accent` must
reference a component listed in `library/components/registry.yaml`. This
is a **closed set** — directors and article-writers cannot invent
component names.

This mirrors the PPT skill's 22-locked-layout philosophy applied to
component primitives.

## Current components (v0.3.1)

| Component | Typography slot | Typical use |
|---|---|---|
| `Kicker` | `kicker` | Small uppercase label, mono font |
| `Title` | `display` | Large display headline |
| `Lead` | `body` italic | Intro paragraph |
| `Body` | `body` | Long-form running text |
| `BodyWithDropCap` | `body` + `drop_cap` | Body with raised-initial drop cap |
| `PullQuote` | `pull_quote` | Large inset quote |
| `Caption` | `caption` | Small italic image caption |
| `CaptionedThumbnail` | `caption` | Image + caption pair |
| `AccentRule` | — | Horizontal hairline in accent color |
| `Folio` | `page_number` | Page number + optional footer |
| `Masthead` | `display` | Brand masthead |
| `CoverLine` | `display` | Cover sub-headline |
| `TocList` | `body` | Table-of-contents list |
| `CreditsBlock` | `body` | Multi-line credits stack |
| `VerticalGradient` | — | Decorative top/bottom gradient overlay |

## Adding a new component

1. Add an entry to `library/components/registry.yaml`.
2. Add a rendering branch to `render_text_component` (or
   `render_accent`) in `library/layouts/_components/_macros/region.j2.html`.
3. Update this catalogue.
4. Run `tests/unit/test_regions_validate.py` to confirm the registry
   parses + the validator accepts the new name.
5. Run `tests/contracts/test_v2_pipelines.py` to confirm regions yamls
   that reference the new component validate.
```

- [ ] **Step R5-T3.2: Commit**

```bash
git add docs/component-registry-reference.md
git commit -m "docs: component-registry-reference.md catalogue + authoring guide"
```

---

### Task R5-T4: Final test run + push

**Files:**
- (no file changes)

- [ ] **Step R5-T4.1: Run full test suite**

Run:
```bash
.venv/bin/python -m pytest tests/ -v 2>&1 | tail -20
```
Expected: all green. Compared to v0.3.0's 115 tests, expect approximately
`115 + 4 (regions_loader) + 6 (regions_validate) + 2 (prompt_builder_v2 regions) + 1 (integration regions assertion)`
≈ **128 passing**.

- [ ] **Step R5-T4.2: Verify each spread type renders**

Inspect the integration test's HTML output to confirm all 7 spread types
land region divs:

```bash
.venv/bin/python -m pytest tests/integration/test_render_dry_run.py -v
# Then inspect /tmp/pytest-.../magazine.html — grep for 'data-role='
```

Each spread should produce its declared regions (≥ 1 image, ≥ 1 text
region for spreads with text).

- [ ] **Step R5-T4.3: Update `docs/v0.3-ARCHITECTURE.md`**

Add a section noting the regions data layer:

```markdown
## v0.3.1: Regions data layer

Each editorial spread is composed of **regions** declared in
`library/layouts/_components/<type>.regions.yaml`. The same data is read
by:

- WeasyPrint render (positions absolute divs from `rect_norm`)
- Image gen prompts (model is told sibling regions to keep calm)
- `article_validate` (every `role: text` region must have its
  `text_field` populated)

See [regions-reference.md](regions-reference.md) and
[component-registry-reference.md](component-registry-reference.md).
```

Commit + push:

```bash
git add docs/v0.3-ARCHITECTURE.md
git commit -m "docs: v0.3-ARCHITECTURE notes regions data layer"
git push
```

---

## Self-Review

Spec coverage check:

- ✅ §1 Goal — Task R2-T1 + R3-T1 demonstrate the three consumers reading one yaml
- ✅ §4.1 Coordinate system: normalized — schemas/regions.schema.json enforces `[0,1]` range
- ✅ §4.2 File layout — Tasks R2-T1 and R4-T{1..6} place yamls next to their j2
- ✅ §4.3 Component registry: closed — Task R1-T2 lands `registry.yaml`; validator (R1-T4) rejects unknown
- ✅ §4.4 6-role taxonomy — schemas/regions.schema.json enum
- ✅ §4.5 Image-gen prompt injection — Tasks R3-T1 + R3-T2
- ✅ §4.6 Migration: one component at a time — R2 (pilot) then R4-T{1..6} per spread
- ✅ §5.5 Persisted sidecar — not in this plan; deferred to a follow-up
  (existing `prompt_persistence.py` saves text; regions sidecar JSON
  would be a small extension, but no consumer reads it yet)
- ✅ §9.1 Phased rollout — five phases R1-R5 match the spec
- ✅ §9.3 Coexistence with overlay contracts — R5-T1 banner; no field removal

Placeholder scan: none of "TBD" / "TODO" / "implement later" patterns
present in normative sections.

Type consistency: `regions_for_image_prompt()` signature matches between
R1-T3 (definition) and R3-T3 (caller). `build_upscale_prompt()` kwarg
`regions_context` matches between R3-T1 (definition) and R3-T3 (caller).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-11-regions-as-shared-contract.md`.

**Recommended sequencing given the empirical prerequisite:**

1. **R1 (5 tasks)** — execute now. Zero risk, all additive. Lands schemas
   + loader + validator + contract test wiring.
2. **R2 (4 tasks)** — execute after R1. First migration; first
   regions-driven render of an existing spread (feature-spread).
3. **(PAUSE)** — run live editorial-16page smoke test on v0.3.0 + R1 + R2.
   Observe model behavior with the new prompt format. Decide if R3's
   approach needs tuning based on what you see.
4. **R3 (3 tasks)** — execute after smoke gives signal. May iterate on
   the prompt-injection format.
5. **R4 (6 tasks)** — execute after R3 lands. All 6 tasks are mutually
   independent and **good candidates for parallel sub-agent dispatch**.
6. **R5 (4 tasks)** — execute after R4. Cleanup + docs + final push.

**Two execution options:**

**1. Subagent-Driven (recommended for R4)** — dispatch a fresh subagent
per task, review between tasks, fast iteration. R4-T{1..6} run in
parallel; R1/R2/R3/R5 run sequentially within their phase.

**2. Inline Execution** — execute tasks in this session using
`executing-plans`, batch within each phase with checkpoints between
phases.

**Which approach?**
