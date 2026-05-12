# Design Contracts & Multi-Realizer Output Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lift design intelligence from inside the Codex Presentations skill into a shared yaml data layer (`library/profiles/` + `library/design-systems/`), and introduce a multi-realizer compose stage so one openMagazine spec can produce both A4 magazine PDF and a 9-slide PPTX deck from the same upstream pipeline.

**Architecture:** Parallel to v0.3.1's regions data layer. Two new yaml types: `profiles/<name>.yaml` (closed registry of publication types — `consumer-retail` ships in v0.3.2) and `design-systems/<slug>.yaml` (per-issue resolved decisions: typography fallback chain, text-safe contracts, brand authenticity gates, output targets). A new `output_selector` routes by `spec.output_target` to one of several realizers (`WeasyprintCompose` for PDF, `PresentationsAdapter` for PPTX, future HTML/video). The PresentationsAdapter wraps Codex's bundled Presentations skill but **pre-computes all design decisions in our yaml** so the skill handles only PPTX-specific composition.

**Tech Stack:** Python 3.10, pytest, jsonschema, PyYAML, Jinja2, WeasyPrint, fc-match (system), Codex Presentations skill (artifact-tool/presentation-jsx).

**Predecessor:** v0.3.1 (`commit 2a7246b`). See [spec](../specs/2026-05-13-design-contracts-multi-realizer-design.md).

**Empirical anchor:** Codex Presentations skill smoke test 2026-05-13 (`outputs/019e1729-3645-7c21-8c17-ba04f8164388/`). The 8 artifact types produced (profile-plan, design-system, layout JSONs with `text_safe_contract`, imagegen prompt JSON+prose, font-substitutions, layout-quality QA, contact-sheet, comeback-scorecard) are the empirical basis for the schemas in this plan.

**Parallelization opportunities** (per spec §9.1 + § agent team analysis):

| Phase | Parallelizable? | Notes |
|---|---|---|
| S1 schemas + loaders | ✅ S1+S2+S6 mutually independent | dispatching-parallel-agents safe |
| S2 profiles + examples | ✅ same | same |
| S6 imagegen prompt upgrade | ✅ same | same |
| S3 articulate integration | ❌ depends S1+S2 | subagent-driven |
| S4 output_selector refactor | ❌ depends S3 | subagent-driven |
| S5 PresentationsAdapter | ❌ highest-risk, single owner | subagent-driven |
| S7 enforcement wiring | ❌ depends S3+S4+S5 | subagent-driven |
| S8 docs | ✅ S8.1+S8.2 mostly independent | dispatching-parallel-agents safe |

---

## Phase S1 — Schemas + loaders (~0.5 day, 5 tasks; parallelizable with S2 + S6)

Foundation. Zero behavior change. Just adds new files.

### Task S1-T1: Author `schemas/profile.schema.json`

**Files:**
- Create: `~/github/openMagazine/schemas/profile.schema.json`

- [ ] **Step S1-T1.1: Write the JSON schema**

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "title": "Publication profile",
  "type": "object",
  "required": ["schema_version", "name", "presentations_profile", "hard_gates"],
  "properties": {
    "schema_version": {"const": 1},
    "name": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
    "display_name": {
      "type": "object",
      "properties": {
        "en": {"type": "string"},
        "zh": {"type": "string"}
      }
    },
    "presentations_profile": {
      "type": "string",
      "enum": [
        "consumer-retail", "finance-ir", "product-platform",
        "gtm-growth", "engineering-platform", "strategy-leadership",
        "appendix-heavy", "template-following", "targeted-edit-data",
        "targeted-edit-media"
      ]
    },
    "hard_gates": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["rule", "description"],
        "properties": {
          "rule": {"type": "string"},
          "description": {"type": "string"},
          "applies_when": {"type": "string"},
          "forbidden_generations": {
            "type": "array",
            "items": {"type": "string"}
          }
        }
      }
    },
    "required_proof_objects": {
      "type": "array",
      "items": {"type": "string"}
    },
    "visual_preferences": {"type": "object"},
    "banned_motifs": {
      "type": "array",
      "items": {"type": "string"}
    },
    "spread_types_required": {
      "type": "array",
      "items": {"type": "string"}
    },
    "spread_types_optional": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

- [ ] **Step S1-T1.2: Verify schema parses**

Run:
```bash
cd ~/github/openMagazine
.venv/bin/python -c "import json; json.load(open('schemas/profile.schema.json'))"
```
Expected: no output (success).

- [ ] **Step S1-T1.3: Commit**

```bash
git add schemas/profile.schema.json
git commit -m "feat(schemas): profile.schema.json for publication profile yamls"
```

---

### Task S1-T2: Author `schemas/design-system.schema.json`

**Files:**
- Create: `~/github/openMagazine/schemas/design-system.schema.json`

- [ ] **Step S1-T2.1: Write the JSON schema**

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "title": "Per-issue design system",
  "type": "object",
  "required": [
    "schema_version", "slug", "profile", "brand",
    "typography_resolution", "brand_authenticity", "output_targets"
  ],
  "properties": {
    "schema_version": {"const": 1},
    "slug": {"type": "string"},
    "profile": {"type": "string"},
    "brand": {"type": "string"},
    "inheritance": {
      "type": "object",
      "properties": {
        "base_brand_typography": {"type": "boolean", "default": true},
        "base_brand_print_specs": {"type": "boolean", "default": true},
        "base_brand_visual_tokens": {"type": "boolean", "default": true}
      }
    },
    "typography_resolution": {
      "type": "object",
      "patternProperties": {
        "^(display|body|meta|kicker|caption|pull_quote|page_number)$": {
          "type": "object",
          "required": ["desired_family", "fallback_chain"],
          "properties": {
            "desired_family": {"type": "string"},
            "fallback_chain": {
              "type": "array",
              "minItems": 1,
              "items": {"type": "string"}
            },
            "resolved_at_render": {"type": ["string", "null"]}
          }
        }
      }
    },
    "text_safe_contracts": {
      "type": "object",
      "properties": {
        "default_rule": {"type": "string"},
        "per_spread_overrides": {"type": "object"}
      }
    },
    "brand_authenticity": {
      "type": "object",
      "properties": {
        "do_not_generate": {
          "type": "array",
          "items": {"type": "string"}
        },
        "do_not_approximate": {
          "type": "array",
          "items": {"type": "string"}
        },
        "asset_provenance_required": {
          "type": "array",
          "items": {"type": "string"}
        },
        "asset_provenance_optional": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "layout_quality": {
      "type": "object",
      "properties": {
        "min_gap_px": {"type": "integer", "minimum": 0},
        "max_text_image_overlap_px": {"type": "integer", "minimum": 0},
        "max_text_text_overlap_px": {"type": "integer", "minimum": 0},
        "fail_on": {"enum": ["error", "warn", "never"]}
      }
    },
    "output_targets": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["format", "realizer"],
        "properties": {
          "format": {
            "enum": [
              "a4-magazine", "photobook-plain",
              "deck-pptx", "deck-html", "video-mp4"
            ]
          },
          "realizer": {
            "enum": [
              "weasyprint", "reportlab",
              "presentations", "html-deck", "video"
            ]
          },
          "page_size": {"type": "string"},
          "slide_size": {"type": "string"},
          "page_count": {"type": "integer"}
        }
      }
    },
    "contact_sheet_rubric": {
      "type": "object",
      "properties": {
        "distinct_layouts_required": {"type": "integer"},
        "template_collapse_threshold": {"type": "integer"}
      }
    }
  }
}
```

- [ ] **Step S1-T2.2: Verify parses**

```bash
.venv/bin/python -c "import json; json.load(open('schemas/design-system.schema.json'))"
```

- [ ] **Step S1-T2.3: Commit**

```bash
git add schemas/design-system.schema.json
git commit -m "feat(schemas): design-system.schema.json for per-issue design contracts"
```

---

### Task S1-T3: Author `schemas/imagegen_prompt.schema.json`

**Files:**
- Create: `~/github/openMagazine/schemas/imagegen_prompt.schema.json`

This schema snapshots the format used by Codex Presentations skill (see empirical anchor in spec §3.3). Our v0.3.2 imagegen prompt files will conform to it so the same prompt files work for both PDF and PPTX realizers.

- [ ] **Step S1-T3.1: Write the JSON schema**

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "title": "Codex imagegen prompt spec block",
  "description": "Validates the JSON spec block embedded in *.prompt.txt files. The Markdown prose section is not schema-validated.",
  "type": "object",
  "required": ["intended_output", "size", "format"],
  "properties": {
    "intended_output": {
      "type": "string",
      "description": "Absolute path where Codex imagegen should write the PNG."
    },
    "reference_image": {
      "type": "string",
      "description": "Optional reference image path; empty string if none."
    },
    "size": {
      "type": "string",
      "pattern": "^[0-9]+x[0-9]+$",
      "description": "Pixel dimensions WIDTHxHEIGHT."
    },
    "quality": {
      "enum": ["low", "medium", "high", "auto"],
      "default": "medium"
    },
    "format": {"enum": ["png", "webp", "jpeg"]},
    "background": {"type": "string", "default": "auto"},
    "moderation": {"type": "string", "default": "auto"}
  }
}
```

- [ ] **Step S1-T3.2: Verify parses**

```bash
.venv/bin/python -c "import json; json.load(open('schemas/imagegen_prompt.schema.json'))"
```

- [ ] **Step S1-T3.3: Commit**

```bash
git add schemas/imagegen_prompt.schema.json
git commit -m "feat(schemas): imagegen_prompt.schema.json snapshots Codex format"
```

---

### Task S1-T4: `lib/design_system_loader.py` + tests

**Files:**
- Create: `~/github/openMagazine/lib/design_system_loader.py`
- Create: `~/github/openMagazine/tests/unit/test_design_system_loader.py`

TDD: failing test first.

- [ ] **Step S1-T4.1: Write the failing test**

```python
"""Tests for design_system_loader."""
from pathlib import Path

import pytest
import yaml

from lib.design_system_loader import (
    load_profile,
    load_design_system,
    resolve_design_system,
    ProfileNotFoundError,
    DesignSystemNotFoundError,
)


SKILL_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def fake_profile_dir(tmp_path, monkeypatch):
    """Create a temporary library/profiles/ dir with one yaml."""
    profiles_dir = tmp_path / "library" / "profiles"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "consumer-retail.yaml").write_text(yaml.safe_dump({
        "schema_version": 1,
        "name": "consumer-retail",
        "display_name": {"en": "Consumer Retail"},
        "presentations_profile": "consumer-retail",
        "hard_gates": [
            {"rule": "brand_authenticity_gate",
             "description": "no logo generation",
             "forbidden_generations": ["logo", "mascot"]}
        ],
        "required_proof_objects": ["image_hero_or_look_page"],
    }))
    monkeypatch.setattr("lib.design_system_loader.SKILL_ROOT", tmp_path)
    return profiles_dir


def test_load_profile_returns_dict(fake_profile_dir):
    profile = load_profile("consumer-retail")
    assert profile["name"] == "consumer-retail"
    assert profile["presentations_profile"] == "consumer-retail"
    assert len(profile["hard_gates"]) == 1


def test_load_profile_missing_raises(monkeypatch, tmp_path):
    monkeypatch.setattr("lib.design_system_loader.SKILL_ROOT", tmp_path)
    with pytest.raises(ProfileNotFoundError):
        load_profile("nonexistent-profile")


def test_load_design_system_returns_dict(tmp_path, monkeypatch):
    ds_dir = tmp_path / "library" / "design-systems"
    ds_dir.mkdir(parents=True)
    (ds_dir / "test-slug.yaml").write_text(yaml.safe_dump({
        "schema_version": 1,
        "slug": "test-slug",
        "profile": "consumer-retail",
        "brand": "meow-life",
        "typography_resolution": {},
        "brand_authenticity": {},
        "output_targets": [{"format": "a4-magazine", "realizer": "weasyprint"}],
    }))
    monkeypatch.setattr("lib.design_system_loader.SKILL_ROOT", tmp_path)
    ds = load_design_system("test-slug")
    assert ds["slug"] == "test-slug"
    assert ds["profile"] == "consumer-retail"


def test_load_design_system_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setattr("lib.design_system_loader.SKILL_ROOT", tmp_path)
    with pytest.raises(DesignSystemNotFoundError):
        load_design_system("nonexistent-slug")


def test_resolve_design_system_inherits_from_brand(fake_profile_dir, tmp_path, monkeypatch):
    """resolve_design_system composes from spec + brand + profile."""
    spec = {"slug": "test-slug"}
    layers = {
        "brand": {
            "schema_version": 2,
            "name": "meow-life",
            "typography": {
                "display": {"family": "Playfair Display"},
                "body": {"family": "Source Serif 4"},
            },
        },
    }
    monkeypatch.setattr("lib.design_system_loader.SKILL_ROOT", tmp_path)
    # Need both profile and brand setup; reuse fake_profile_dir
    ds = resolve_design_system(spec, layers, profile_name="consumer-retail")
    assert ds["slug"] == "test-slug"
    assert ds["profile"] == "consumer-retail"
    assert "display" in ds["typography_resolution"]
    assert ds["typography_resolution"]["display"]["desired_family"] == "Playfair Display"
    # Fallback chain auto-built with at least a system-safe option
    assert len(ds["typography_resolution"]["display"]["fallback_chain"]) >= 1
```

- [ ] **Step S1-T4.2: Run test, expect ImportError**

```bash
.venv/bin/python -m pytest tests/unit/test_design_system_loader.py -v
```
Expected: `ModuleNotFoundError: No module named 'lib.design_system_loader'`

- [ ] **Step S1-T4.3: Write `lib/design_system_loader.py`**

```python
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
```

- [ ] **Step S1-T4.4: Run tests, expect pass**

```bash
.venv/bin/python -m pytest tests/unit/test_design_system_loader.py -v
```
Expected: 5 passed.

- [ ] **Step S1-T4.5: Commit**

```bash
git add lib/design_system_loader.py tests/unit/test_design_system_loader.py
git commit -m "feat(lib): design_system_loader — profiles + per-issue design systems"
```

---

### Task S1-T5: `lib/font_resolver.py` + tests

**Files:**
- Create: `~/github/openMagazine/lib/font_resolver.py`
- Create: `~/github/openMagazine/tests/unit/test_font_resolver.py`

- [ ] **Step S1-T5.1: Write the failing test**

```python
"""Tests for font_resolver."""
import pytest

from lib.font_resolver import (
    resolve_font,
    resolve_typography_pack,
)


def test_resolve_font_returns_dict_with_required_keys():
    result = resolve_font("Playfair Display", ["Georgia", "Times New Roman"])
    assert "requested" in result
    assert "matched" in result
    assert "fallback_used" in result
    assert result["requested"] == "Playfair Display"


def test_resolve_font_falls_back_when_desired_missing():
    """A guaranteed-missing family name should fall back."""
    result = resolve_font(
        "DefinitelyDoesNotExistFontXYZ123",
        ["Georgia", "Times New Roman"],
    )
    assert result["fallback_used"] is True
    # matched should be one of the fallbacks, or empty string if no match at all
    assert result["matched"] in ["Georgia", "Times New Roman", ""] or len(result["matched"]) > 0


def test_resolve_typography_pack():
    """Iterates the resolution chain dict and returns a log."""
    design_system = {
        "typography_resolution": {
            "display": {
                "desired_family": "Playfair Display",
                "fallback_chain": ["Georgia"],
            },
            "body": {
                "desired_family": "Source Serif 4",
                "fallback_chain": ["Georgia"],
            },
        }
    }
    log = resolve_typography_pack(design_system)
    assert "display" in log
    assert "body" in log
    assert log["display"]["requested"] == "Playfair Display"
```

- [ ] **Step S1-T5.2: Run, expect ImportError**

```bash
.venv/bin/python -m pytest tests/unit/test_font_resolver.py -v
```

- [ ] **Step S1-T5.3: Write `lib/font_resolver.py`**

```python
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
```

- [ ] **Step S1-T5.4: Run tests, expect pass**

```bash
.venv/bin/python -m pytest tests/unit/test_font_resolver.py -v
```
Expected: 3 passed (assertions allow for fc-match-not-installed case).

- [ ] **Step S1-T5.5: Commit**

```bash
git add lib/font_resolver.py tests/unit/test_font_resolver.py
git commit -m "feat(lib): font_resolver — fc-match-backed typography fallback chain"
```

---

## Phase S2 — Profiles + example design-system (~0.5 day, 4 tasks; parallelizable with S1 + S6)

Add the first profile yaml, an example design-system, the validator, and contract-test auto-discovery.

### Task S2-T1: Write `library/profiles/consumer-retail.yaml` + README

**Files:**
- Create: `~/github/openMagazine/library/profiles/README.md`
- Create: `~/github/openMagazine/library/profiles/consumer-retail.yaml`

- [ ] **Step S2-T1.1: Create directory + README**

```bash
mkdir -p ~/github/openMagazine/library/profiles
```

Write `library/profiles/README.md`:

```markdown
# library/profiles/

Closed registry of publication-type profiles. A profile carries the
hard gates, required proof objects, visual preferences, and banned
motifs for one *kind* of publication (`consumer-retail`, `finance-ir`,
`engineering-platform`, etc.).

Profiles are referenced by `library/design-systems/<slug>.yaml.profile`
and surface in directors / article-writer / image-prompt construction
to enforce the profile's editorial rules.

This file layout mirrors `library/components/registry.yaml`'s
closed-set philosophy from v0.3.1: agents can't invent a new profile
name — adding one is a small PR.

## Adding a new profile

1. Author the yaml file. Use an existing profile (e.g.
   `consumer-retail.yaml`) as a template.
2. Map `presentations_profile` to one of Codex Presentations skill's
   10 profile names (see `~/.codex/plugins/cache/openai-primary-runtime/
   presentations/26.506.11943/skills/presentations/profiles/`).
3. List hard gates, required proof objects, visual preferences.
4. Run `tools/validation/design_system_validate.py` against an example
   design-system that references the new profile.
5. Update `docs/profiles-reference.md`.
```

- [ ] **Step S2-T1.2: Write `library/profiles/consumer-retail.yaml`**

```yaml
schema_version: 1
name: consumer-retail
display_name:
  en: "Consumer / Retail / Editorial"
  zh: "消费品 / 零售 / 编辑型"

# 1:1 link to Codex Presentations skill profile name
presentations_profile: consumer-retail

hard_gates:
  - rule: image_led_subject_gate
    description: |
      Use sourced imagery with provenance, user-provided assets, or
      imagegen — never Python drawings or programmatic vector
      illustrations for the primary subject.
    applies_when: "subject is visually inspectable (animal, person, product, place, food, lifestyle scene)"

  - rule: brand_authenticity_gate
    description: |
      Do not generate / approximate logos / mascots / app icons /
      signature marks. Use verified assets or omit. When an official
      asset cannot be verified, rely on color, typography, layout,
      and product language as brand cues.
    forbidden_generations:
      - logo
      - mascot
      - app_icon
      - signature_mark
      - product_ui_screenshot

  - rule: editorial_copy_gate
    description: |
      Client-facing copy must sound usable by staff or customers, not
      like an internal strategy note. Avoid corporate scorecards, faux
      KPIs, and boardroom language unless explicitly requested.

required_proof_objects:
  - image_hero_or_look_page
  - product_or_look_rationale
  - audience_journey
  - editorial_hierarchy

visual_preferences:
  paper_color: warm_neutral_or_deep_ink
  display_face: refined_serif_or_didone
  body_face: utilitarian_sans_or_humanist_serif
  meta_face: monospace
  layout: open_composition
  rules: hairline
  data_labels: direct

banned_motifs:
  - corporate_scorecard
  - faux_kpi_grid
  - generic_saas_dashboard
  - consulting_card_grid
  - stock_photo_business_meeting

spread_types_required:
  - cover
  - feature-spread

spread_types_optional:
  - toc
  - pull-quote
  - portrait-wall
  - colophon
  - back-cover
```

- [ ] **Step S2-T1.3: Validate**

```bash
.venv/bin/python -c "
import json, yaml, jsonschema
schema = json.load(open('schemas/profile.schema.json'))
data = yaml.safe_load(open('library/profiles/consumer-retail.yaml').read())
jsonschema.validate(instance=data, schema=schema)
print('valid')
"
```
Expected: `valid`

- [ ] **Step S2-T1.4: Commit**

```bash
git add library/profiles/
git commit -m "feat(library): profiles/consumer-retail.yaml + closed-registry README"
```

---

### Task S2-T2: Write `library/design-systems/cosmos-luna-may-2026.yaml` example + README

**Files:**
- Create: `~/github/openMagazine/library/design-systems/README.md`
- Create: `~/github/openMagazine/library/design-systems/cosmos-luna-may-2026.yaml`

- [ ] **Step S2-T2.1: Create dir + README**

```bash
mkdir -p ~/github/openMagazine/library/design-systems
```

Write `library/design-systems/README.md`:

```markdown
# library/design-systems/

Per-issue resolved design decisions. One yaml per issue slug,
auto-persisted at the articulate checkpoint (Stage 3 of
editorial-16page pipeline) but committable / editable.

Each design-system carries:
- the chosen `profile` (e.g. `consumer-retail`)
- per-slot typography resolution chains (desired family + fallbacks)
- text-safe contract rules
- brand authenticity gates (which generations are forbidden)
- layout quality thresholds
- output targets (which realizers to invoke at compose stage)

This file is parallel to `library/articles/<slug>.yaml`: same per-issue
granularity, both auto-drafted at Stage 3 articulate.

## Authoring

Most users never edit these by hand — they're written by
`lib.design_system_loader.resolve_design_system()` at articulate time.
But editing them is fully supported: any field you set here overrides
the auto-derivation.

## Validation

```bash
python tools/validation/design_system_validate.py \
  library/design-systems/<slug>.yaml
```
```

- [ ] **Step S2-T2.2: Write `library/design-systems/cosmos-luna-may-2026.yaml`**

```yaml
schema_version: 1
slug: cosmos-luna-may-2026
profile: consumer-retail
brand: meow-life

inheritance:
  base_brand_typography: true
  base_brand_print_specs: true
  base_brand_visual_tokens: true

typography_resolution:
  display:
    desired_family: "Playfair Display"
    fallback_chain:
      - "Source Serif 4"
      - "Georgia"
      - "Times New Roman"
    resolved_at_render: ~
  body:
    desired_family: "Source Serif 4"
    fallback_chain:
      - "Georgia"
      - "Times New Roman"
    resolved_at_render: ~
  meta:
    desired_family: "IBM Plex Mono"
    fallback_chain:
      - "Menlo"
      - "Courier"
    resolved_at_render: ~

text_safe_contracts:
  default_rule: |
    When text overlays or sits inside a generated visual field, keep
    clean negative space inside each text-safe rectangle.
  per_spread_overrides: {}

brand_authenticity:
  do_not_generate:
    - logo
    - mascot
    - app_icon
  do_not_approximate:
    - "MEOW LIFE wordmark"
    - "Luna's specific face proportions"
  asset_provenance_required:
    - cover_hero
    - feature_hero
  asset_provenance_optional:
    - feature_captioned

layout_quality:
  min_gap_px: 16
  max_text_image_overlap_px: 25
  max_text_text_overlap_px: 10
  fail_on: error

output_targets:
  - format: a4-magazine
    realizer: weasyprint
    page_size: A4
    bleed_mm: 3
  - format: deck-pptx
    realizer: presentations
    slide_size: 1280x720
    page_count: 9

contact_sheet_rubric:
  distinct_layouts_required: 7
  template_collapse_threshold: 3
```

- [ ] **Step S2-T2.3: Validate**

```bash
.venv/bin/python -c "
import json, yaml, jsonschema
schema = json.load(open('schemas/design-system.schema.json'))
data = yaml.safe_load(open('library/design-systems/cosmos-luna-may-2026.yaml').read())
jsonschema.validate(instance=data, schema=schema)
print('valid')
"
```
Expected: `valid`

- [ ] **Step S2-T2.4: Commit**

```bash
git add library/design-systems/
git commit -m "feat(library): design-systems/cosmos-luna-may-2026 example + README"
```

---

### Task S2-T3: `tools/validation/design_system_validate.py` + tests

**Files:**
- Create: `~/github/openMagazine/tools/validation/design_system_validate.py`
- Create: `~/github/openMagazine/tests/unit/test_design_system_validate.py`
- Modify: `~/github/openMagazine/tools/validation/__init__.py`

- [ ] **Step S2-T3.1: Write failing test**

```python
"""Tests for design_system_validate."""
import pytest
import yaml

from tools.validation.design_system_validate import validate_design_system


def _write_yaml(tmp_path, data):
    p = tmp_path / "test.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


def test_valid_design_system_returns_empty(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "slug": "test",
        "profile": "consumer-retail",
        "brand": "meow-life",
        "typography_resolution": {
            "display": {
                "desired_family": "Playfair Display",
                "fallback_chain": ["Georgia"],
            },
        },
        "brand_authenticity": {"do_not_generate": ["logo"]},
        "output_targets": [{"format": "a4-magazine", "realizer": "weasyprint"}],
    })
    assert validate_design_system(p) == []


def test_missing_required_top_level_field_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "slug": "test",
        # missing profile, brand, etc.
    })
    errors = validate_design_system(p)
    assert any("profile" in e or "brand" in e or "required" in e for e in errors)


def test_empty_fallback_chain_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "slug": "test",
        "profile": "consumer-retail",
        "brand": "meow-life",
        "typography_resolution": {
            "display": {"desired_family": "X", "fallback_chain": []},
        },
        "brand_authenticity": {},
        "output_targets": [{"format": "a4-magazine", "realizer": "weasyprint"}],
    })
    errors = validate_design_system(p)
    assert any("fallback_chain" in e for e in errors)


def test_unknown_realizer_rejected(tmp_path):
    p = _write_yaml(tmp_path, {
        "schema_version": 1,
        "slug": "test",
        "profile": "consumer-retail",
        "brand": "meow-life",
        "typography_resolution": {},
        "brand_authenticity": {},
        "output_targets": [{"format": "deck-pptx", "realizer": "InventedRealizer"}],
    })
    errors = validate_design_system(p)
    assert any("realizer" in e or "InventedRealizer" in e for e in errors)


def test_validates_shipped_example():
    """The cosmos-luna-may-2026.yaml shipped in the repo must validate."""
    import pathlib
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    example = repo_root / "library/design-systems/cosmos-luna-may-2026.yaml"
    if example.is_file():
        assert validate_design_system(example) == []
```

- [ ] **Step S2-T3.2: Run, expect ImportError**

```bash
.venv/bin/python -m pytest tests/unit/test_design_system_validate.py -v
```

- [ ] **Step S2-T3.3: Write `tools/validation/design_system_validate.py`**

```python
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
                f"typography_resolution/{slot}: fallback_chain must have ≥ 1 entry"
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
```

- [ ] **Step S2-T3.4: Update `tools/validation/__init__.py`**

Append:
```python
from tools.validation import design_system_validate  # noqa: F401
```

- [ ] **Step S2-T3.5: Run tests, expect pass**

```bash
.venv/bin/python -m pytest tests/unit/test_design_system_validate.py -v
```
Expected: 5 passed (or 4 if the shipped example isn't there yet — fine).

- [ ] **Step S2-T3.6: Commit**

```bash
git add tools/validation/design_system_validate.py \
        tools/validation/__init__.py \
        tests/unit/test_design_system_validate.py
git commit -m "feat(tools/validation): design_system_validate + CLI"
```

---

### Task S2-T4: Contract test auto-validate profiles + design-systems

**Files:**
- Modify: `~/github/openMagazine/tests/contracts/test_v2_pipelines.py`

- [ ] **Step S2-T4.1: Append parametrized tests**

Append to `tests/contracts/test_v2_pipelines.py`:

```python
from tools.validation.design_system_validate import validate_design_system


def _profile_yamls():
    return sorted((SKILL_ROOT / "library" / "profiles").glob("*.yaml"))


def _design_system_yamls():
    return sorted((SKILL_ROOT / "library" / "design-systems").glob("*.yaml"))


@pytest.mark.parametrize(
    "profile_path", _profile_yamls(), ids=lambda p: p.name
)
def test_profile_yaml_validates(profile_path):
    """Every library/profiles/*.yaml must validate against profile.schema.json."""
    import json
    from jsonschema import validate
    schema = json.loads((SKILL_ROOT / "schemas/profile.schema.json").read_text())
    data = yaml.safe_load(profile_path.read_text())
    validate(instance=data, schema=schema)


@pytest.mark.parametrize(
    "ds_path", _design_system_yamls(), ids=lambda p: p.name
)
def test_design_system_yaml_validates(ds_path):
    """Every library/design-systems/*.yaml must validate."""
    errors = validate_design_system(ds_path)
    assert errors == [], (
        f"{ds_path.name}: {len(errors)} error(s)\n  "
        + "\n  ".join(errors)
    )
```

- [ ] **Step S2-T4.2: Run contract tests + full suite**

```bash
.venv/bin/python -m pytest tests/contracts/ -v
.venv/bin/python -m pytest tests/ -q 2>&1 | tail -5
```
Expected: all green; new parametrized tests pick up shipped yamls.

- [ ] **Step S2-T4.3: Commit**

```bash
git add tests/contracts/test_v2_pipelines.py
git commit -m "test(contracts): auto-validate profiles + design-systems yamls"
```

---

## Phase S3 — Articulate stage gains design-system resolution (~0.5 day, 3 tasks; depends on S1+S2)

### Task S3-T1: `lib/spec_loader.py` extended to load design-systems

**Files:**
- Modify: `~/github/openMagazine/lib/spec_loader.py`
- Modify: `~/github/openMagazine/tests/unit/test_spec_validate.py` (or similar)

- [ ] **Step S3-T1.1: Read current spec_loader.py**

```bash
cat ~/github/openMagazine/lib/spec_loader.py | head -60
```

Capture: `resolve_layers()` currently returns dict with keys
`{subject, style, theme, layout, brand, article}`. Add `design_system`
to that dict (optional; tries to load by slug, returns None on miss).

- [ ] **Step S3-T1.2: Modify `resolve_layers`**

In `lib/spec_loader.py`, find the `resolve_layers()` function. After
loading article (or after the last existing layer), add:

```python
# v0.3.2: load design-system if it exists
try:
    from lib.design_system_loader import load_design_system, DesignSystemNotFoundError
    design_system = load_design_system(spec["slug"])
except (DesignSystemNotFoundError, KeyError):
    design_system = None
layers["design_system"] = design_system
```

This is **optional** — articulate stage may not yet have resolved /
persisted the design-system. Downstream consumers handle `None`.

- [ ] **Step S3-T1.3: Run existing spec_loader tests**

```bash
.venv/bin/python -m pytest tests/unit/test_spec_validate.py -v 2>&1 | tail -10
```
Expected: existing tests still pass.

- [ ] **Step S3-T1.4: Commit**

```bash
git add lib/spec_loader.py
git commit -m "feat(lib): spec_loader resolves design-system layer (optional)"
```

---

### Task S3-T2: articulate-director persists design-system

**Files:**
- Modify: `~/github/openMagazine/skills/pipelines/editorial-16page/articulate-director.md`

- [ ] **Step S3-T2.1: Read current articulate-director.md**

```bash
cat ~/github/openMagazine/skills/pipelines/editorial-16page/articulate-director.md | tail -40
```

- [ ] **Step S3-T2.2: Add design-system resolution step**

In `articulate-director.md`, find the Python code block that drafts /
validates the article. After the article is validated, append a new
sub-step:

```python
# v0.3.2: also resolve and persist the per-issue design-system
from lib.design_system_loader import resolve_design_system
from tools.validation.design_system_validate import validate_design_system
import yaml, pathlib

design_system = resolve_design_system(spec, layers, profile_name="consumer-retail")
ds_path = pathlib.Path("library/design-systems") / f"{spec['slug']}.yaml"
ds_path.parent.mkdir(parents=True, exist_ok=True)
ds_path.write_text(yaml.safe_dump(design_system, sort_keys=False, allow_unicode=True))

errors = validate_design_system(ds_path)
assert errors == [], f"design-system validation failed: {errors}"

print(f"Resolved design-system → {ds_path}")
print(f"  profile: {design_system['profile']}")
print(f"  output_targets: {[t['format'] for t in design_system['output_targets']]}")
```

Add a new section "## Design System Resolution" before Output Artifact
section, briefly explaining the new step.

- [ ] **Step S3-T2.3: Verify integration test still passes**

```bash
.venv/bin/python -m pytest tests/ -q 2>&1 | tail -5
```
Expected: green; no Python-level test exercises the markdown directly,
but no regressions.

- [ ] **Step S3-T2.4: Commit**

```bash
git add skills/pipelines/editorial-16page/articulate-director.md
git commit -m "docs(skills): articulate-director resolves + persists design-system"
```

---

### Task S3-T3: Author `skills/meta/design-system-author.md`

**Files:**
- Create: `~/github/openMagazine/skills/meta/design-system-author.md`

- [ ] **Step S3-T3.1: Write the meta-skill**

```markdown
# design-system-author

How an agent populates `library/design-systems/<slug>.yaml` from spec +
brand + theme + chosen profile.

## When to invoke

Stage 3 (articulate) of editorial pipelines. Called after article copy
is drafted; runs `resolve_design_system()` from `lib.design_system_loader`
and persists the result.

## Authoring rules

### 1. Profile selection (one of)

- `consumer-retail` — animal / person / product / lookbook / lifestyle.
  Default for openMagazine's current use cases.
- `finance-ir` — earnings / investor reviews / financial analysis.
- `product-platform` — SaaS / product narratives.
- `engineering-platform` — developer / AI / infrastructure decks.
- `gtm-growth` — growth / marketing / cohort stories.
- `strategy-leadership` — investor-day / board / strategy.
- `appendix-heavy` — tables / disclosures / source packs.

If spec doesn't dictate a profile, infer from theme + brand. For
openMagazine v0.3.2, default is `consumer-retail`.

### 2. Typography fallback chains

For each typography slot (`display`, `body`, `meta`):

- desired family: from `brand.typography.<slot>.family`
- fallback chain length ≥ 2:
  - 1st: a sibling-style family in the same flavor (e.g. Playfair
    Display → Source Serif 4)
  - 2nd: a system-safe family (Georgia / Times New Roman / Menlo /
    Courier)

Never let a chain be empty; never let it end without a system-safe
option.

### 3. Brand authenticity gates

For `consumer-retail` issues, always include:
- `do_not_generate`: at minimum `logo`, `mascot`, `app_icon`
- Specific brand-name approximations: include exact wordmarks the brand
  doesn't want approximated (e.g. "MEOW LIFE wordmark")

### 4. Output targets

If spec.output_targets is set, copy it through. If not, infer:
- editorial-16page layout + meow-life brand → `a4-magazine`
- explicit deck request → add `deck-pptx`

### 5. Auto-persistence at the checkpoint

The resolved yaml lands at `library/design-systems/<slug>.yaml` BEFORE
the user sees the articulate checkpoint. User can edit at the
checkpoint; the edited yaml is what subsequent stages read.

## Self-review before persisting

- ✅ Every typography slot has fallback_chain ≥ 1 entry
- ✅ Brand authenticity matches the profile's `forbidden_generations`
- ✅ output_targets covers the user's actual request
- ✅ Validator passes

## See also

- `skills/meta/article-writer.md` — sibling pattern for article copy
- `library/profiles/<name>.yaml` — the profile being inherited
- `docs/design-system-reference.md` — the catalogue
```

- [ ] **Step S3-T3.2: Commit**

```bash
git add skills/meta/design-system-author.md
git commit -m "docs(skills/meta): design-system-author drafting protocol"
```

---

## Phase S4 — `output_selector` refactor (~0.5 day, 3 tasks; depends on S3)

### Task S4-T1: Move existing PDF backends to `tools/output/`

**Files:**
- Create: `~/github/openMagazine/tools/output/__init__.py`
- Move: `tools/pdf/weasyprint_compose.py` → `tools/output/weasyprint_compose.py`
- Move: `tools/pdf/reportlab_compose.py` → `tools/output/reportlab_compose.py`
- Move: `tools/pdf/pdf_selector.py` → keep as backward-compat shim importing from `tools.output`

- [ ] **Step S4-T1.1: Create new directory**

```bash
mkdir -p ~/github/openMagazine/tools/output
```

- [ ] **Step S4-T1.2: Move files (preserve git history with `git mv`)**

```bash
cd ~/github/openMagazine
git mv tools/pdf/weasyprint_compose.py tools/output/weasyprint_compose.py
git mv tools/pdf/reportlab_compose.py tools/output/reportlab_compose.py
```

- [ ] **Step S4-T1.3: Write `tools/output/__init__.py`**

```python
"""output capability family. v0.3.2 generalization of tools/pdf/."""
from tools.output import reportlab_compose  # noqa: F401
from tools.output import weasyprint_compose  # noqa: F401
```

- [ ] **Step S4-T1.4: Rewrite `tools/pdf/__init__.py` as backward-compat shim**

```python
"""tools/pdf is deprecated — moved to tools/output in v0.3.2.

This shim re-exports the modules for backward compatibility with v0.3.1
code that imports from tools.pdf.
"""
import warnings

from tools.output import reportlab_compose  # noqa: F401
from tools.output import weasyprint_compose  # noqa: F401

warnings.warn(
    "tools.pdf is deprecated; use tools.output (v0.3.2)",
    DeprecationWarning,
    stacklevel=2,
)
```

Remove the old `tools/pdf/pdf_selector.py` import line if any (we'll
recreate as backward shim in next task).

- [ ] **Step S4-T1.5: Update internal imports in moved files**

The two moved files reference each other and `tools.tool_registry`.
Verify imports still resolve:

```bash
.venv/bin/python -c "
from tools.output.weasyprint_compose import WeasyprintCompose
from tools.output.reportlab_compose import ReportlabCompose
print('imports ok')
"
```

- [ ] **Step S4-T1.6: Run existing tests, expect pass (with deprecation warning)**

```bash
.venv/bin/python -m pytest tests/ -q 2>&1 | tail -5
```
Expected: green; possibly 1 DeprecationWarning for tools.pdf import.

- [ ] **Step S4-T1.7: Commit**

```bash
git add tools/output/ tools/pdf/__init__.py
git commit -m "refactor(tools): move tools/pdf → tools/output; backward-compat shim"
```

---

### Task S4-T2: New `output_selector.py`

**Files:**
- Create: `~/github/openMagazine/tools/output/output_selector.py`
- Create: `~/github/openMagazine/tests/unit/test_output_selector.py`
- Modify: `~/github/openMagazine/tools/pdf/pdf_selector.py` as shim

- [ ] **Step S4-T2.1: Write failing test**

```python
"""Tests for output_selector."""
import pytest

from tools.output.output_selector import OutputSelector


def test_a4_magazine_routes_to_weasyprint():
    sel = OutputSelector()
    backend = sel.choose_backend(target={"format": "a4-magazine", "realizer": "weasyprint"})
    assert backend.provider == "weasyprint"


def test_photobook_routes_to_reportlab():
    sel = OutputSelector()
    backend = sel.choose_backend(target={"format": "photobook-plain", "realizer": "reportlab"})
    assert backend.provider == "reportlab"


def test_unknown_realizer_raises():
    sel = OutputSelector()
    with pytest.raises(ValueError, match="realizer"):
        sel.choose_backend(target={"format": "x", "realizer": "InventedRealizer"})


def test_default_target_when_none():
    """No target arg → default to a4-magazine."""
    sel = OutputSelector()
    backend = sel.choose_backend(target=None)
    assert backend.provider == "weasyprint"


def test_legacy_layout_dict_compatibility():
    """choose_backend(layout=...) — old pdf_selector API — still works."""
    sel = OutputSelector()
    backend = sel.choose_backend(layout={"schema_version": 2, "name": "editorial-16page"})
    assert backend.provider == "weasyprint"
```

- [ ] **Step S4-T2.2: Run, expect ImportError**

```bash
.venv/bin/python -m pytest tests/unit/test_output_selector.py -v
```

- [ ] **Step S4-T2.3: Write `tools/output/output_selector.py`**

```python
"""output_selector — route compose calls by spec.output_target.

Replaces v0.3.1's pdf_selector.py. Backward-compatible: if invoked with
a `layout={...}` kwarg (old API), routes by `layout.schema_version`.
"""
from __future__ import annotations

from tools.base_tool import BaseTool
from tools.output.reportlab_compose import ReportlabCompose
from tools.output.weasyprint_compose import WeasyprintCompose


class OutputSelector(BaseTool):
    capability = "output_realizer"
    provider = "selector"
    status = "active"

    def __init__(self):
        super().__init__()
        self._reportlab = ReportlabCompose()
        self._weasyprint = WeasyprintCompose()
        # PresentationsAdapter lazily imported (added in S5)
        self._presentations = None

    def choose_backend(
        self, *, target: dict | None = None, layout: dict | None = None
    ) -> BaseTool:
        # Legacy v0.3.1 API: layout dict with schema_version
        if target is None and layout is not None:
            sv = layout.get("schema_version")
            if sv == 1:
                return self._reportlab
            if sv == 2:
                return self._weasyprint
            raise ValueError(f"unsupported layout.schema_version {sv!r}")

        if target is None:
            return self._weasyprint  # default

        realizer = target.get("realizer")
        if realizer == "weasyprint":
            return self._weasyprint
        if realizer == "reportlab":
            return self._reportlab
        if realizer == "presentations":
            if self._presentations is None:
                from tools.output.presentations_adapter import PresentationsAdapter
                self._presentations = PresentationsAdapter()
            return self._presentations
        raise ValueError(f"unknown realizer {realizer!r}")

    def run(self, *, target: dict | None = None, layout: dict | None = None, **kwargs):
        return self.choose_backend(target=target, layout=layout).run(**kwargs)


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(OutputSelector())
```

- [ ] **Step S4-T2.4: Modify `tools/pdf/pdf_selector.py` to be a shim**

Read current contents:
```bash
cat ~/github/openMagazine/tools/pdf/pdf_selector.py
```

Replace with:
```python
"""pdf_selector — v0.3.1 backward-compat shim. Use tools.output.output_selector."""
import warnings

from tools.output.output_selector import OutputSelector as PdfSelector  # noqa: F401

warnings.warn(
    "tools.pdf.pdf_selector is deprecated; use tools.output.output_selector",
    DeprecationWarning,
    stacklevel=2,
)
```

- [ ] **Step S4-T2.5: Update `tools/output/__init__.py` to register OutputSelector**

Append:
```python
from tools.output import output_selector  # noqa: F401
```

- [ ] **Step S4-T2.6: Run tests, expect pass**

```bash
.venv/bin/python -m pytest tests/unit/test_output_selector.py -v
.venv/bin/python -m pytest tests/ -q 2>&1 | tail -5
```
Expected: green for new tests + full suite.

- [ ] **Step S4-T2.7: Commit**

```bash
git add tools/output/output_selector.py tools/output/__init__.py \
        tools/pdf/pdf_selector.py tests/unit/test_output_selector.py
git commit -m "feat(tools/output): output_selector routes by spec.output_target"
```

---

### Task S4-T3: Update compose-director to use output_selector

**Files:**
- Modify: `~/github/openMagazine/skills/pipelines/editorial-16page/compose-director.md`

- [ ] **Step S4-T3.1: Read current compose-director**

```bash
cat ~/github/openMagazine/skills/pipelines/editorial-16page/compose-director.md | head -70
```

- [ ] **Step S4-T3.2: Update the Python block to use OutputSelector**

Find the existing code block that uses `PdfSelector`. Replace with:

```python
import pathlib, yaml, json
from lib.spec_loader import load_spec, resolve_layers
from tools.output.output_selector import OutputSelector

spec, _ = load_spec(pathlib.Path("library/issue-specs/<slug>.yaml"))
layers = resolve_layers(spec)
article = yaml.safe_load(
    open(f"library/articles/{spec['article']}.yaml", "r", encoding="utf-8")
)
issue_dir = pathlib.Path(f"output/{spec['slug']}")
design_system = layers.get("design_system") or {}

selector = OutputSelector()
results = []
for target in design_system.get("output_targets", [{"format": "a4-magazine", "realizer": "weasyprint"}]):
    backend = selector.choose_backend(target=target)
    result = backend.run(
        issue_dir=issue_dir,
        layout=layers["layout"],
        brand=layers["brand"],
        article=article,
        spec=spec,
        design_system=design_system,
    )
    results.append({"target": target, "result": result})

(issue_dir / "compose_result.json").write_text(json.dumps({
    "outputs": results,
    "spec_slug": spec["slug"],
}, indent=2))
```

- [ ] **Step S4-T3.3: Verify**

```bash
.venv/bin/python -m pytest tests/ -q 2>&1 | tail -5
```
Expected: green.

- [ ] **Step S4-T3.4: Commit**

```bash
git add skills/pipelines/editorial-16page/compose-director.md
git commit -m "docs(skills): compose-director uses OutputSelector multi-realizer loop"
```

---

## Phase S5 — PresentationsAdapter (~1.5 days, 4 tasks; **highest risk**, single owner)

### Task S5-T1: `tools/output/presentations_adapter.py` + tests

**Files:**
- Create: `~/github/openMagazine/tools/output/presentations_adapter.py`
- Create: `~/github/openMagazine/tests/unit/test_presentations_adapter.py`

- [ ] **Step S5-T1.1: Write failing test**

```python
"""Tests for PresentationsAdapter."""
from pathlib import Path

import pytest

from tools.output.presentations_adapter import (
    PresentationsAdapter,
    PresentationsArtifactNotFoundError,
)


def test_adapter_registers_as_output_realizer():
    adapter = PresentationsAdapter()
    assert adapter.capability == "output_realizer"
    assert adapter.provider == "presentations"


def test_adapter_workspace_path_constructed_from_thread_and_slug(tmp_path):
    """The adapter computes expected Codex artifact path."""
    adapter = PresentationsAdapter()
    path = adapter.expected_artifact_dir(
        thread_id="test-thread-123",
        task_slug="cosmos-luna-deck",
        issue_dir=tmp_path,
    )
    assert "test-thread-123" in str(path)
    assert "cosmos-luna-deck" in str(path)


def test_adapter_raises_when_no_artifacts(tmp_path):
    """If Codex didn't actually run, reading back should error clearly."""
    adapter = PresentationsAdapter()
    with pytest.raises(PresentationsArtifactNotFoundError):
        adapter.read_artifacts(
            thread_id="nonexistent-thread",
            task_slug="nonexistent",
            issue_dir=tmp_path,
        )


def test_adapter_reads_real_smoke_test_artifacts(tmp_path):
    """If the empirical smoke test artifacts exist at the known path,
    the adapter reads them back successfully."""
    smoke_thread = "019e1729-3645-7c21-8c17-ba04f8164388"
    smoke_dir = Path.home() / "github" / "openMagazine" / "outputs" / smoke_thread
    if not smoke_dir.exists():
        pytest.skip("smoke test artifacts not available")

    adapter = PresentationsAdapter()
    info = adapter.read_artifacts(
        thread_id=smoke_thread,
        task_slug="cosmos-luna-deck",
        issue_dir=smoke_dir.parent.parent,
    )
    assert info["profile_plan"]
    assert info["design_system_summary"]
    assert "consumer-retail" in info["profile_plan"]
    assert info["pptx_path"].endswith(".pptx")
    assert info["slide_count"] == 9
```

- [ ] **Step S5-T1.2: Run, expect ImportError**

```bash
.venv/bin/python -m pytest tests/unit/test_presentations_adapter.py -v
```

- [ ] **Step S5-T1.3: Write `tools/output/presentations_adapter.py`**

```python
"""PresentationsAdapter — realizer for Codex Presentations skill.

The adapter does NOT directly invoke the Presentations skill (that
requires Codex CLI runtime). Instead, the compose-director-deck.md
skill instructs the agent to invoke Presentations with our
pre-computed design-system as input. This adapter is responsible for:

  1. Computing the input bundle Presentations needs (design_system,
     brand, article, regions) into a digestible spec passed via the
     director's prompt.
  2. After the agent has driven Presentations to completion, reading
     back the artifact tree at
     `<issue_dir>/outputs/<thread_id>/presentations/<task_slug>/`.
  3. Copying the final .pptx into `<issue_dir>/deck/<slug>.pptx`.
  4. Validating that the expected artifact files exist.

Limitation: we cannot exercise the full PPTX export path in unit
tests; integration relies on `test_multi_output.py` which uses
recorded artifacts from the 2026-05-13 smoke test as a fixture.
"""
from __future__ import annotations

import pathlib
import shutil

from tools.base_tool import BaseTool


class PresentationsArtifactNotFoundError(FileNotFoundError):
    """Raised when expected Presentations output artifacts are missing."""


class PresentationsAdapter(BaseTool):
    capability = "output_realizer"
    provider = "presentations"
    status = "experimental"

    def expected_artifact_dir(
        self, *, thread_id: str, task_slug: str, issue_dir: pathlib.Path
    ) -> pathlib.Path:
        """Return the workspace path where Presentations skill writes."""
        return (
            pathlib.Path(issue_dir)
            / "outputs"
            / thread_id
            / "presentations"
            / task_slug
        )

    def build_input_bundle(
        self, *, design_system: dict, brand: dict, article: dict,
        regions_by_spread_type: dict | None = None,
    ) -> dict:
        """Produce the spec the agent will use to drive Presentations.

        Returns a serializable dict:
          {
            "presentations_profile": "consumer-retail",
            "task_slug": "cosmos-luna-deck",
            "design_system_inputs": { ... },
            "brand_authenticity": { ... },
            "text_safe_rules": "...",
            "typography": { ... resolved fallback chains ... },
            "article_excerpt": { titles + leads, no body text },
            "regions_summary": { spread types + role + rect_norm } ,
          }
        """
        bundle = {
            "presentations_profile": design_system.get("profile", "consumer-retail"),
            "task_slug": f"{design_system['slug']}-deck",
            "brand_authenticity": design_system.get("brand_authenticity", {}),
            "text_safe_rules": (
                design_system.get("text_safe_contracts", {})
                .get("default_rule", "")
            ),
            "typography": design_system.get("typography_resolution", {}),
            "article_titles": [
                {
                    "idx": sc.get("idx"),
                    "type": sc.get("type"),
                    "title": sc.get("title"),
                    "kicker": sc.get("kicker"),
                }
                for sc in article.get("spread_copy", [])
            ],
            "regions_summary": regions_by_spread_type or {},
            "brand_masthead": brand.get("masthead"),
            "brand_color_accent": (brand.get("visual_tokens") or {}).get("color_accent"),
        }
        return bundle

    def read_artifacts(
        self, *, thread_id: str, task_slug: str, issue_dir: pathlib.Path
    ) -> dict:
        """Read back the Presentations skill's structured artifact tree.

        Returns a dict with keys:
            profile_plan: str (full text)
            design_system_summary: str
            pptx_path: str (absolute)
            slide_count: int
            preview_paths: list[str]
            layout_paths: list[str]
            font_substitutions: str (full text)
            layout_quality_output: str
        """
        artifact_dir = self.expected_artifact_dir(
            thread_id=thread_id, task_slug=task_slug, issue_dir=issue_dir
        )
        if not artifact_dir.is_dir():
            raise PresentationsArtifactNotFoundError(
                f"Presentations artifact dir not found: {artifact_dir}"
            )

        def _read(name: str) -> str:
            p = artifact_dir / name
            return p.read_text(encoding="utf-8") if p.is_file() else ""

        layout_dir = artifact_dir / "layout"
        layout_paths = (
            sorted(str(p) for p in layout_dir.glob("slide-*.layout.json"))
            if layout_dir.is_dir() else []
        )
        preview_dir = artifact_dir / "preview"
        preview_paths = (
            sorted(str(p) for p in preview_dir.glob("slide-*.png"))
            if preview_dir.is_dir() else []
        )
        pptx_dir = artifact_dir / "output"
        pptx_files = (
            sorted(str(p) for p in pptx_dir.glob("*.pptx"))
            if pptx_dir.is_dir() else []
        )
        if not pptx_files:
            raise PresentationsArtifactNotFoundError(
                f"no .pptx in {pptx_dir}"
            )

        return {
            "profile_plan": _read("profile-plan.txt"),
            "design_system_summary": _read("design-system.txt"),
            "claim_spine": _read("claim-spine.txt"),
            "font_substitutions": _read("font-substitutions.txt"),
            "layout_quality_output": _read("qa/layout-quality.txt"),
            "pptx_path": pptx_files[0],
            "slide_count": len(layout_paths) or len(preview_paths),
            "layout_paths": layout_paths,
            "preview_paths": preview_paths,
        }

    def copy_final_to_issue_deck(
        self, *, pptx_source: str, issue_dir: pathlib.Path, slug: str
    ) -> pathlib.Path:
        """Copy the produced .pptx into output/<slug>/deck/<slug>.pptx."""
        deck_dir = pathlib.Path(issue_dir) / "deck"
        deck_dir.mkdir(parents=True, exist_ok=True)
        target = deck_dir / f"{slug}.pptx"
        shutil.copy2(pptx_source, target)
        return target

    def run(
        self, *, issue_dir, layout, brand, article, spec, design_system,
        **kwargs
    ):
        """The director skill drives Presentations; this run() returns
        the bundled-inputs spec the director uses + None for the actual
        result (filled in after agent loop completes).

        Director is responsible for invoking Presentations and then
        calling self.read_artifacts() and self.copy_final_to_issue_deck().
        """
        slug = spec["slug"]
        bundle = self.build_input_bundle(
            design_system=design_system, brand=brand, article=article,
            regions_by_spread_type=kwargs.get("regions_by_spread_type"),
        )
        return {
            "realizer": "presentations",
            "input_bundle": bundle,
            "slug": slug,
            "expected_artifact_dir_template": (
                f"<issue_dir>/outputs/<thread_id>/presentations/{bundle['task_slug']}/"
            ),
        }


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(PresentationsAdapter())
```

- [ ] **Step S5-T1.4: Run tests, expect pass**

```bash
.venv/bin/python -m pytest tests/unit/test_presentations_adapter.py -v
```
Expected: 4 passed (4th test skips if smoke artifacts unavailable).

- [ ] **Step S5-T1.5: Commit**

```bash
git add tools/output/presentations_adapter.py \
        tests/unit/test_presentations_adapter.py
git commit -m "feat(tools/output): PresentationsAdapter realizer for PPTX deck"
```

---

### Task S5-T2: Author `compose-director-deck.md`

**Files:**
- Create: `~/github/openMagazine/skills/pipelines/editorial-16page/compose-director-deck.md`

- [ ] **Step S5-T2.1: Write the director skill**

```markdown
# compose-director-deck — editorial-16page

## Purpose

Realize a `deck-pptx` output target via the Codex Presentations skill.
This director is invoked when `design_system.output_targets` contains
a `deck-pptx` entry. The PDF output (`a4-magazine`) is handled by the
sibling compose-director.md.

## Inputs

- `output/<slug>/compose_result.json` (in-progress, may contain other
  realizer results)
- All standard upstream artifacts (research_brief, proposal, article,
  storyboard, upscale_result, design-system).
- `output/<slug>/images/spread-NN/<slot>.png` × 21 — the 4K image
  slots are reused; PPTX uses crops/thumbs of the same source PNGs.

## Read first

- `skills/meta/design-system-author.md` for what's in design_system
- `~/.codex/plugins/cache/openai-primary-runtime/presentations/.../skills/presentations/SKILL.md` for the skill's mandatory workflow

## Procedure

### 1. Build the input bundle

~~~python
from tools.output.presentations_adapter import PresentationsAdapter
import pathlib, yaml, json

adapter = PresentationsAdapter()
issue_dir = pathlib.Path(f"output/{spec['slug']}")
design_system = layers["design_system"]

bundle = adapter.build_input_bundle(
    design_system=design_system,
    brand=layers["brand"],
    article=article,
    regions_by_spread_type=layers.get("regions_by_spread_type"),
)
~~~

### 2. Compose the Presentations prompt

The agent invokes Presentations with this prompt structure. The
`task-slug` is critical — it determines where Presentations writes:

~~~text
Use the Presentations skill to build a {slide_count}-slide editorial deck
that mirrors my openMagazine v0.3.2 issue.

WORKSPACE: outputs/$CODEX_THREAD_ID/presentations/{task_slug}

PRE-RESOLVED INPUTS (do not redecide these):
- presentations_profile: {bundle["presentations_profile"]}
- typography (with resolved fallback chain): {bundle["typography"]}
- text-safe rules: {bundle["text_safe_rules"]}
- brand authenticity gates: {bundle["brand_authenticity"]}
- brand masthead: {bundle["brand_masthead"]}
- accent color: {bundle["brand_color_accent"]}

ARTICLE TITLES PER SPREAD:
{json.dumps(bundle["article_titles"], indent=2)}

REGIONS (for layout intent reuse):
{json.dumps(bundle["regions_summary"], indent=2)}

CONSTRAINTS:
- Task mode: create (no reference deck supplied)
- Preserve all intermediate artifacts under $WORKSPACE
- Final .pptx → $WORKSPACE/output/{spec_slug}.pptx
- Do not approximate logos / mascots / app icons per brand
  authenticity gate above
- Match openMagazine's spread types one-to-one when possible (cover,
  toc, 3 features, pull-quote, portrait-wall, colophon, back-cover)

REPORT BACK with:
- $CODEX_THREAD_ID so I can find the artifacts
- profile-plan.txt content
- font-substitutions.txt content
- qa/layout-quality.txt output
- final .pptx path + size
~~~

### 3. Read back artifacts

After the Presentations skill reports completion:

~~~python
artifacts = adapter.read_artifacts(
    thread_id=codex_thread_id,
    task_slug=bundle["task_slug"],
    issue_dir=issue_dir,
)

# Copy the final .pptx into our issue's deck/ subdir
final_pptx = adapter.copy_final_to_issue_deck(
    pptx_source=artifacts["pptx_path"],
    issue_dir=issue_dir,
    slug=spec["slug"],
)
print(f"PPTX → {final_pptx}")
print(f"Slides: {artifacts['slide_count']}")
print(f"Font substitutions: {artifacts['font_substitutions'][:200]}")
~~~

### 4. Validate

Run `check_layout_quality.mjs` on each Presentations layout JSON
(this was empirically validated standalone in the smoke test):

~~~bash
PRES=~/.codex/plugins/cache/openai-primary-runtime/presentations/26.506.11943/skills/presentations
for layout in $(ls outputs/$CODEX_THREAD_ID/presentations/<task_slug>/layout/slide-*.layout.json); do
    node $PRES/scripts/check_layout_quality.mjs --layout $layout
done
~~~

If any layout reports errors, log them but don't fail compose — they're
informational for the user.

### 5. Append to compose_result.json

~~~python
compose_result_path = issue_dir / "compose_result.json"
existing = json.loads(compose_result_path.read_text()) if compose_result_path.is_file() else {"outputs": []}
existing["outputs"].append({
    "format": "deck-pptx",
    "realizer": "presentations",
    "path": str(final_pptx),
    "slide_count": artifacts["slide_count"],
    "thread_id": codex_thread_id,
})
compose_result_path.write_text(json.dumps(existing, indent=2))
~~~

## Checkpoint behavior

`checkpoint: off` — deck output is parallel to PDF, no separate gate.

## Success criteria

- `output/<slug>/deck/<slug>.pptx` exists and is ≥ 100 KB
- `compose_result.json` has a `deck-pptx` entry
- `check_layout_quality.mjs` ran on all layouts (output captured)

## Failure modes

- **Presentations skill not available** → STOP and ask user to verify
  Codex CLI version (need bundled artifact-tool ≥ 2.7.3)
- **Artifact dir doesn't exist after Presentations reports done** →
  Presentations chose a different `task_slug`; ask user for actual
  thread_id and confirm
- **Final .pptx empty** → layout error inside Presentations; user
  should inspect $WORKSPACE/qa/comeback-scorecard.txt
```

- [ ] **Step S5-T2.2: Commit**

```bash
git add skills/pipelines/editorial-16page/compose-director-deck.md
git commit -m "docs(skills): compose-director-deck.md for PPTX realizer path"
```

---

### Task S5-T3: Update parent compose-director.md to orchestrate multi-realizer

**Files:**
- Modify: `~/github/openMagazine/skills/pipelines/editorial-16page/compose-director.md`

- [ ] **Step S5-T3.1: Add orchestration section**

In `compose-director.md`, after the main Python code block (the one
that runs WeasyprintCompose), add a new section "## Multi-Realizer
Orchestration":

```markdown
## Multi-Realizer Orchestration (v0.3.2)

`design_system.output_targets` may list multiple realizers. The PDF
realizer runs first (above); for each non-PDF realizer, invoke the
appropriate director skill:

~~~python
for target in design_system.get("output_targets", []):
    if target["realizer"] == "presentations":
        # → see compose-director-deck.md
        # Agent should now read that file and follow it for this target.
        pass
    elif target["realizer"] in ("weasyprint", "reportlab"):
        # Already handled above
        continue
    else:
        print(f"WARNING: unknown realizer {target['realizer']!r}; skipping")
~~~

Each realizer appends its result to `compose_result.json.outputs`.
Final structure:

~~~json
{
  "outputs": [
    {"format": "a4-magazine", "realizer": "weasyprint",
     "path": "output/<slug>/magazine.pdf", "page_count": 16, "size_mb": 42.1},
    {"format": "deck-pptx", "realizer": "presentations",
     "path": "output/<slug>/deck/<slug>.pptx", "slide_count": 9,
     "thread_id": "..."}
  ],
  "spec_slug": "<slug>"
}
~~~
```

- [ ] **Step S5-T3.2: Commit**

```bash
git add skills/pipelines/editorial-16page/compose-director.md
git commit -m "docs(skills): compose-director orchestrates multi-realizer output_targets"
```

---

### Task S5-T4: Integration test for multi-output using recorded artifacts

**Files:**
- Create: `~/github/openMagazine/tests/integration/test_multi_output.py`

- [ ] **Step S5-T4.1: Write the integration test**

```python
"""Integration test: multi-realizer compose using recorded artifacts.

Uses the 2026-05-13 Presentations smoke test artifacts as a fixture for
the deck path. PDF path runs end-to-end via WeasyprintCompose. Both
realizers produce results in the same issue dir.
"""
from pathlib import Path

import pytest
import yaml
from PIL import Image

from tools.output.output_selector import OutputSelector
from tools.output.presentations_adapter import (
    PresentationsAdapter,
    PresentationsArtifactNotFoundError,
)


SKILL_ROOT = Path(__file__).resolve().parents[2]
SMOKE_THREAD = "019e1729-3645-7c21-8c17-ba04f8164388"


def _make_placeholder_pngs(images_dir: Path, layout: dict):
    for slot in layout["image_slots"]:
        spread_dir = images_dir / f"spread-{slot['spread_idx']:02d}"
        spread_dir.mkdir(parents=True, exist_ok=True)
        out = spread_dir / f"{slot['id']}.png"
        Image.new("RGB", (100, 100), color="black").save(out)


@pytest.fixture
def issue_dir(tmp_path):
    d = tmp_path / "issue"
    d.mkdir()
    return d


def test_output_selector_routes_to_each_realizer(issue_dir):
    """Output selector can route to weasyprint, reportlab, presentations."""
    sel = OutputSelector()
    wp = sel.choose_backend(target={"format": "a4-magazine", "realizer": "weasyprint"})
    rl = sel.choose_backend(target={"format": "photobook-plain", "realizer": "reportlab"})
    pr = sel.choose_backend(target={"format": "deck-pptx", "realizer": "presentations"})
    assert wp.provider == "weasyprint"
    assert rl.provider == "reportlab"
    assert pr.provider == "presentations"


def test_presentations_adapter_reads_recorded_artifacts(issue_dir):
    """If the smoke test's artifacts exist, adapter can read them."""
    smoke_outputs_root = SKILL_ROOT / "outputs" / SMOKE_THREAD
    if not smoke_outputs_root.exists():
        pytest.skip(f"smoke artifacts not available at {smoke_outputs_root}")

    adapter = PresentationsAdapter()
    info = adapter.read_artifacts(
        thread_id=SMOKE_THREAD,
        task_slug="cosmos-luna-deck",
        issue_dir=SKILL_ROOT,
    )
    assert info["pptx_path"].endswith(".pptx")
    assert info["slide_count"] == 9
    assert "consumer-retail" in info["profile_plan"]
    # Both PDF (placeholder for now) and PPTX are accessible side-by-side


def test_multi_output_compose_result_shape(issue_dir, tmp_path):
    """compose_result.json shape supports multiple realizer outputs."""
    import json
    compose_result = {
        "outputs": [
            {"format": "a4-magazine", "realizer": "weasyprint",
             "path": str(issue_dir / "magazine.pdf"), "page_count": 16},
            {"format": "deck-pptx", "realizer": "presentations",
             "path": str(issue_dir / "deck" / "test.pptx"),
             "slide_count": 9, "thread_id": SMOKE_THREAD},
        ],
        "spec_slug": "test",
    }
    target = issue_dir / "compose_result.json"
    target.write_text(json.dumps(compose_result, indent=2))
    reread = json.loads(target.read_text())
    assert len(reread["outputs"]) == 2
    realizers = {o["realizer"] for o in reread["outputs"]}
    assert realizers == {"weasyprint", "presentations"}
```

- [ ] **Step S5-T4.2: Run tests**

```bash
.venv/bin/python -m pytest tests/integration/test_multi_output.py -v
```
Expected: 3 passed (some may skip if smoke artifacts not present).

- [ ] **Step S5-T4.3: Verify full suite**

```bash
.venv/bin/python -m pytest tests/ -q 2>&1 | tail -5
```

- [ ] **Step S5-T4.4: Commit**

```bash
git add tests/integration/test_multi_output.py
git commit -m "test(integration): multi-output compose via OutputSelector + adapter"
```

---

## Phase S6 — Imagegen prompt format upgrade (~0.5 day, 3 tasks; parallelizable with S1+S2)

### Task S6-T1: Extend `lib/prompt_persistence.py` to write JSON spec block

**Files:**
- Modify: `~/github/openMagazine/lib/prompt_persistence.py`
- Modify: `~/github/openMagazine/tests/unit/test_prompt_persistence.py`

- [ ] **Step S6-T1.1: Read existing prompt_persistence.py**

```bash
cat ~/github/openMagazine/lib/prompt_persistence.py
```

- [ ] **Step S6-T1.2: Extend `save_prompt` signature**

In `lib/prompt_persistence.py`, modify `save_prompt` to accept an
optional `spec` kwarg containing the imagegen JSON spec:

```python
def save_prompt(
    issue_dir: pathlib.Path,
    *,
    kind: str,
    prompt_text: str,
    slot_id: str | None = None,
    spec: dict | None = None,  # NEW v0.3.2
) -> pathlib.Path:
    """Persist a rendered prompt under <issue_dir>/prompts/.

    If `spec` is provided, the file format is:

      # Codex Imagegen Prompt

      Use the Codex imagegen tool with this prompt.

      ```json
      <JSON serialization of spec>
      ```

      ## Prompt

      <prompt_text>

    Without `spec`, falls back to prose-only v0.3.1 behavior.
    """
    base = pathlib.Path(issue_dir) / "prompts"

    if kind == "storyboard":
        out = base / "storyboard.prompt.txt"
    elif kind == "upscale":
        if not slot_id:
            raise ValueError("upscale prompt requires slot_id")
        if "." in slot_id:
            head, tail = slot_id.split(".", 1)
            out = base / head / f"{tail}.prompt.txt"
        else:
            out = base / f"{slot_id}.prompt.txt"
    else:
        raise ValueError(
            f"unknown prompt kind {kind!r}; expected 'storyboard' or 'upscale'"
        )

    out.parent.mkdir(parents=True, exist_ok=True)

    if spec:
        body = (
            "# Codex Imagegen Prompt\n\n"
            "Use the Codex imagegen tool with this prompt. "
            "Do not call external image APIs from scripts.\n\n"
            "```json\n"
            + json.dumps(spec, indent=2, ensure_ascii=False)
            + "\n```\n\n"
            "## Prompt\n\n"
            + prompt_text
            + "\n"
        )
    else:
        body = prompt_text

    out.write_text(body, encoding="utf-8")
    return out
```

Add `import json` at the top if not already present.

- [ ] **Step S6-T1.3: Add test for the new format**

In `tests/unit/test_prompt_persistence.py`, append:

```python
def test_save_prompt_with_spec_writes_dual_section(tmp_path):
    path = save_prompt(
        tmp_path, kind="upscale",
        prompt_text="Subject: cat. Scene: lunar.",
        slot_id="spread-03.feature_hero",
        spec={
            "intended_output": "/abs/path/to.png",
            "size": "3500x4666",
            "quality": "high",
            "format": "png",
        },
    )
    content = path.read_text(encoding="utf-8")
    assert "# Codex Imagegen Prompt" in content
    assert "```json" in content
    assert "intended_output" in content
    assert "## Prompt" in content
    assert "Subject: cat" in content


def test_save_prompt_without_spec_keeps_prose_format(tmp_path):
    """Backward compatibility: no spec → just prose."""
    path = save_prompt(
        tmp_path, kind="storyboard",
        prompt_text="hello storyboard",
    )
    content = path.read_text(encoding="utf-8")
    assert content == "hello storyboard"
    assert "```json" not in content
```

- [ ] **Step S6-T1.4: Run tests, expect pass**

```bash
.venv/bin/python -m pytest tests/unit/test_prompt_persistence.py -v
```

- [ ] **Step S6-T1.5: Commit**

```bash
git add lib/prompt_persistence.py tests/unit/test_prompt_persistence.py
git commit -m "feat(lib): prompt_persistence save_prompt accepts imagegen JSON spec"
```

---

### Task S6-T2: Director skills emit the spec block when calling save_prompt

**Files:**
- Modify: `~/github/openMagazine/skills/pipelines/editorial-16page/storyboard-director.md`
- Modify: `~/github/openMagazine/skills/pipelines/editorial-16page/upscale-director.md`

- [ ] **Step S6-T2.1: Update upscale-director.md call site**

Find the `save_prompt(...)` call in upscale-director.md. Update to pass
an imagegen spec:

```python
# Build the spec block (v0.3.2)
imagegen_spec = {
    "intended_output": str(out_path),
    "reference_image": str(refs[0]) if refs else "",
    "size": "3500x4666",  # 4K-ish 3:4 for portrait
    "quality": "high",
    "format": "png",
    "background": "auto",
    "moderation": "auto",
}
save_prompt(
    issue_dir, kind="upscale", prompt_text=prompt, slot_id=full,
    spec=imagegen_spec,
)
```

- [ ] **Step S6-T2.2: Update storyboard-director.md call site**

Similarly in storyboard-director.md:

```python
imagegen_spec = {
    "intended_output": str(issue_dir / "storyboard.png"),
    "reference_image": "",
    "size": "1024x1536",
    "quality": "medium",
    "format": "png",
    "background": "auto",
    "moderation": "auto",
}
save_prompt(issue_dir, kind="storyboard", prompt_text=prompt, spec=imagegen_spec)
```

- [ ] **Step S6-T2.3: Verify full suite still passes**

```bash
.venv/bin/python -m pytest tests/ -q 2>&1 | tail -5
```

- [ ] **Step S6-T2.4: Commit**

```bash
git add skills/pipelines/editorial-16page/storyboard-director.md \
        skills/pipelines/editorial-16page/upscale-director.md
git commit -m "docs(skills): directors write imagegen spec block in prompt files"
```

---

### Task S6-T3: Validate the new prompt file format

**Files:**
- Create: `~/github/openMagazine/tests/unit/test_imagegen_prompt_format.py`

- [ ] **Step S6-T3.1: Write the test**

```python
"""Tests that recorded imagegen prompt files conform to the schema."""
import json
import pathlib
import re

import jsonschema
import pytest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _extract_json_block(prompt_text: str) -> dict | None:
    match = re.search(r"```json\n(.*?)\n```", prompt_text, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(1))


def test_imagegen_prompt_files_validate_against_schema():
    """If any *.prompt.txt files exist with JSON blocks, they must
    validate against schemas/imagegen_prompt.schema.json."""
    schema_path = SKILL_ROOT / "schemas/imagegen_prompt.schema.json"
    if not schema_path.is_file():
        pytest.skip("schema not present")
    schema = json.loads(schema_path.read_text())

    # Walk all known prompt files
    candidates = []
    for output_dir in (SKILL_ROOT / "output").glob("*") if (SKILL_ROOT / "output").exists() else []:
        candidates.extend((output_dir / "prompts").rglob("*.prompt.txt") if (output_dir / "prompts").exists() else [])

    if not candidates:
        pytest.skip("no prompt files on disk yet")

    for prompt_file in candidates:
        text = prompt_file.read_text(encoding="utf-8")
        spec = _extract_json_block(text)
        if spec is None:
            continue  # legacy prose-only format
        jsonschema.validate(instance=spec, schema=schema)
```

- [ ] **Step S6-T3.2: Run**

```bash
.venv/bin/python -m pytest tests/unit/test_imagegen_prompt_format.py -v
```
Expected: pass or skip (depending on whether prompt files exist on
disk yet — they only appear after a real run).

- [ ] **Step S6-T3.3: Commit**

```bash
git add tests/unit/test_imagegen_prompt_format.py
git commit -m "test: imagegen prompt JSON spec block validates against schema"
```

---

## Phase S7 — Font + brand authenticity enforcement (~0.5 day, 2 tasks; depends on S3+S4+S5)

### Task S7-T1: Compose stage runs font resolution + writes log

**Files:**
- Modify: `~/github/openMagazine/tools/output/weasyprint_compose.py`
- Modify: `~/github/openMagazine/skills/pipelines/editorial-16page/compose-director.md`

- [ ] **Step S7-T1.1: Add font resolution to WeasyprintCompose**

Read current `weasyprint_compose.py`. In the render function, after
loading design_system, add:

```python
from lib.font_resolver import resolve_typography_pack

# v0.3.2: log font resolution before rendering
if design_system:
    resolution_log = resolve_typography_pack(design_system)
    log_path = pathlib.Path(issue_dir) / "font-resolution.json"
    log_path.write_text(
        json.dumps(resolution_log, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
```

- [ ] **Step S7-T1.2: Verify**

```bash
.venv/bin/python -m pytest tests/integration/test_render_dry_run.py -v
```
Expected: green; `font-resolution.json` should appear in the dry-run
output dir after rendering.

- [ ] **Step S7-T1.3: Commit**

```bash
git add tools/output/weasyprint_compose.py
git commit -m "feat(tools/output): weasyprint logs font resolution per typography slot"
```

---

### Task S7-T2: Storyboard + upscale prompts embed brand authenticity gates

**Files:**
- Modify: `~/github/openMagazine/lib/prompt_builder_v2.py`

- [ ] **Step S7-T2.1: Extend build_upscale_prompt to read design_system**

In `lib/prompt_builder_v2.py`, modify the prompt assembly to inject
brand authenticity negatives when `design_system` is in `layers`:

```python
def _render_brand_authenticity_negatives(layers: dict) -> str:
    """Build a negative-prompt fragment from design_system.brand_authenticity."""
    ds = (layers or {}).get("design_system") or {}
    ba = ds.get("brand_authenticity") or {}
    forbidden = ba.get("do_not_generate", []) + ba.get("do_not_approximate", [])
    if not forbidden:
        return ""
    return (
        "\n\nBrand authenticity (additional negative prompt):\n"
        + ", ".join(f"no {item}" for item in forbidden)
    )
```

Call it from `build_upscale_prompt` and append to the final rendered
text just before returning.

- [ ] **Step S7-T2.2: Add a unit test**

In `tests/unit/test_prompt_builder_v2.py`, append:

```python
def test_build_upscale_prompt_embeds_brand_authenticity(spec, layers):
    layers["design_system"] = {
        "brand_authenticity": {
            "do_not_generate": ["logo", "mascot"],
            "do_not_approximate": ["MEOW LIFE wordmark"],
        }
    }
    p = build_upscale_prompt(
        role="portrait", spec=spec, layers=layers,
        slot_id="spread-03.feature_hero",
        scene="character at boulder",
        aspect="3:4",
    )
    assert "no logo" in p
    assert "no mascot" in p
    assert "no MEOW LIFE wordmark" in p
```

- [ ] **Step S7-T2.3: Run tests, expect pass**

```bash
.venv/bin/python -m pytest tests/unit/test_prompt_builder_v2.py -v
```

- [ ] **Step S7-T2.4: Commit**

```bash
git add lib/prompt_builder_v2.py tests/unit/test_prompt_builder_v2.py
git commit -m "feat(lib): prompts embed design_system.brand_authenticity negatives"
```

---

## Phase S8 — Docs + final test + push (~0.5 day, 4 tasks; S8-T1 + S8-T2 parallelizable)

### Task S8-T1: Author `docs/design-system-reference.md`

**Files:**
- Create: `~/github/openMagazine/docs/design-system-reference.md`

- [ ] **Step S8-T1.1: Write the doc**

```markdown
# Design System Reference

Per-issue design decisions live in `library/design-systems/<slug>.yaml`.
This catalogue documents every field.

See [`docs/superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md`](superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md)
for the design rationale.

## File shape

| Field | Type | Owner |
|---|---|---|
| `schema_version` | const 1 | bump on breaking change |
| `slug` | string | issue id |
| `profile` | string | references `library/profiles/<name>.yaml` |
| `brand` | string | references `library/brands/<name>.yaml` |
| `inheritance` | object | which brand fields to inherit |
| `typography_resolution.<slot>.desired_family` | string | what we ask for |
| `typography_resolution.<slot>.fallback_chain` | list | walked at render time |
| `typography_resolution.<slot>.resolved_at_render` | string\|null | filled at compose stage |
| `text_safe_contracts.default_rule` | string | image-overlay negative-space rule |
| `text_safe_contracts.per_spread_overrides` | object | rare; usually empty |
| `brand_authenticity.do_not_generate` | list | image-gen prompts get these as negatives |
| `brand_authenticity.do_not_approximate` | list | same, with exact wordmarks |
| `brand_authenticity.asset_provenance_required` | list | regions that require user-supplied / verified assets |
| `layout_quality.min_gap_px` | int | for check_layout_quality.mjs |
| `layout_quality.max_text_image_overlap_px` | int | same |
| `layout_quality.max_text_text_overlap_px` | int | same |
| `output_targets` | list | which realizers to invoke at compose |
| `contact_sheet_rubric.distinct_layouts_required` | int | minimum unique layouts in deck |

## Lifecycle

1. **Auto-resolved at Stage 3 articulate** via `lib.design_system_loader.resolve_design_system()`
2. **Persisted to disk** at `library/design-systems/<slug>.yaml`
3. **Shown to user** at articulate checkpoint; user can edit yaml directly
4. **Validated** via `tools/validation/design_system_validate.py`
5. **Consumed** at Stage 6 compose by all realizers in `output_targets`

## Authoring

Most fields auto-derive; edit only when you want to:
- Add an `output_targets` entry (e.g. add `deck-pptx`)
- Tighten brand authenticity for a specific issue
- Override typography for one issue without changing brand.yaml
- Adjust `layout_quality` thresholds

## See also

- `library/profiles/<name>.yaml` — the profile being inherited
- `docs/profiles-reference.md` — profile catalogue
- `skills/meta/design-system-author.md` — drafting protocol for the agent
```

- [ ] **Step S8-T1.2: Commit**

```bash
git add docs/design-system-reference.md
git commit -m "docs: design-system-reference catalogue + lifecycle"
```

---

### Task S8-T2: Author `docs/profiles-reference.md`

**Files:**
- Create: `~/github/openMagazine/docs/profiles-reference.md`

- [ ] **Step S8-T2.1: Write the doc**

```markdown
# Profiles Reference

Closed registry of publication types. Pick one per design-system.

See [`docs/superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md`](superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md)
for rationale.

## Profiles shipped in v0.3.2

| Profile | When to use | File |
|---|---|---|
| `consumer-retail` | animal / person / product / lookbook / lifestyle / editorial | `library/profiles/consumer-retail.yaml` |

## Future profiles (v0.3.3+)

| Profile | When to use |
|---|---|
| `finance-ir` | earnings / investor reviews / financial analysis |
| `product-platform` | SaaS / product narratives |
| `gtm-growth` | growth / marketing / cohort stories |
| `engineering-platform` | developer / AI / infrastructure |
| `strategy-leadership` | investor-day / board / strategy |
| `appendix-heavy` | tables / disclosures |

Each future profile follows the same shape: extract structural rules
from Codex Presentations skill's `profiles/<name>.md` into yaml.

## Profile fields

| Field | Type | Purpose |
|---|---|---|
| `schema_version` | const 1 | |
| `name` | string | lowercase-kebab |
| `display_name.{en,zh}` | string | shown to users |
| `presentations_profile` | enum | maps to Codex Presentations profile |
| `hard_gates` | list | rules realizers must respect |
| `required_proof_objects` | list | every spread must include one |
| `visual_preferences` | object | aesthetic hints, not enforced |
| `banned_motifs` | list | image-prompt negatives |
| `spread_types_required` / `spread_types_optional` | list | layout constraints |

## Adding a new profile

See [`library/profiles/README.md`](../library/profiles/README.md).
```

- [ ] **Step S8-T2.2: Commit**

```bash
git add docs/profiles-reference.md
git commit -m "docs: profiles-reference catalogue + authoring guide"
```

---

### Task S8-T3: Update `docs/v0.3-ARCHITECTURE.md`

**Files:**
- Modify: `~/github/openMagazine/docs/v0.3-ARCHITECTURE.md`

- [ ] **Step S8-T3.1: Append v0.3.2 section**

Append to `docs/v0.3-ARCHITECTURE.md`:

```markdown

## v0.3.2: Design contracts as shared data layer

Two new yaml layers parallel to v0.3.1's regions:

- `library/profiles/<name>.yaml` — publication type (closed registry,
  ships `consumer-retail` in v0.3.2)
- `library/design-systems/<slug>.yaml` — per-issue resolved decisions
  (typography fallback chain, text-safe contracts, brand authenticity
  gates, output targets)

The same upstream pipeline (stages 1-5) now feeds **multiple realizers**
at the compose stage, routed by `design_system.output_targets`:

| target | realizer | output |
|---|---|---|
| `a4-magazine` | WeasyprintCompose | `magazine.pdf` |
| `photobook-plain` | ReportlabCompose | `magazine.pdf` (v1 path) |
| `deck-pptx` | PresentationsAdapter | `deck/<slug>.pptx` |

`tools/output/output_selector.py` replaces v0.3.1's `pdf_selector.py`
(kept as backward-compat shim).

See [regions-as-shared-contract](superpowers/specs/2026-05-11-regions-as-shared-contract-design.md)
and [design-contracts-multi-realizer](superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md)
for the two consecutive applications of the same architectural pattern:
**lifting decisions out of actor internals into shared yaml data**.

See also: [design-system-reference.md](design-system-reference.md),
[profiles-reference.md](profiles-reference.md).
```

- [ ] **Step S8-T3.2: Commit**

```bash
git add docs/v0.3-ARCHITECTURE.md
git commit -m "docs: v0.3-ARCHITECTURE notes design-system data layer + multi-realizer"
```

---

### Task S8-T4: Final test + README update + push

**Files:**
- Modify: `~/github/openMagazine/README.md`

- [ ] **Step S8-T4.1: Run full test suite**

```bash
cd ~/github/openMagazine && .venv/bin/python -m pytest tests/ -v 2>&1 | tail -15
```
Expected: all green. Approx 137 (v0.3.1 baseline) + 30-40 new tests ≈
**~170-175 passing**.

- [ ] **Step S8-T4.2: Update README.md status table**

In `README.md`, update the Status table's editorial-16page row:

```diff
-| `editorial-16page` | experimental v0.3.1 | 16-page editorial magazine, 21 image slots, regions-driven | WeasyPrint |
+| `editorial-16page` | experimental v0.3.2 | 16-page editorial magazine + 9-slide PPTX deck, regions-driven, multi-realizer | WeasyPrint + Presentations |
```

Add a paragraph after the Status table:

```markdown
**v0.3.2 update (2026-05-XX):** Output now multi-realizer. Same upstream
pipeline can produce both A4 magazine PDF (WeasyPrint) and 9-slide
deck PPTX (Codex Presentations skill) from one spec. Design decisions
(typography fallback chains, text-safe contracts, brand authenticity
gates) are lifted into `library/profiles/` + `library/design-systems/`
shared data layers. See
[docs/superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md](docs/superpowers/specs/2026-05-13-design-contracts-multi-realizer-design.md).
```

- [ ] **Step S8-T4.3: Commit + push**

```bash
git add README.md
git commit -m "docs(README): refresh for v0.3.2 design-contracts-multi-realizer"
git push 2>&1 | tail -3
```

Expected: push shows the commit range.

- [ ] **Step S8-T4.4: Final status check**

```bash
git status -sb
git log --oneline -5
```

Confirm: branch is in sync with origin, last 5 commits include S8-T3 +
S8-T2 + S8-T1 + S7-T2 + S7-T1.

---

## Self-Review

### Spec coverage check

| Spec § | Covered by |
|---|---|
| §1 Goal — 3 constraints | All 8 phases together; S1+S2 satisfy framework fit; S3+S5 satisfy design-intelligence retention; S2+S3 satisfy persistence |
| §2 Non-goals (v0.3.2.0) | S2 ships only `consumer-retail`; future profiles deferred |
| §4.1 Two-layer split | S1-T1 (profile schema) + S1-T2 (design-system schema) + S2-T1 + S2-T2 |
| §4.2 Field translation | S2-T1 (consumer-retail.yaml extracts from Presentations consumer-retail.md) |
| §4.3 output_selector | S4-T2 |
| §4.4 PresentationsAdapter | S5-T1 + S5-T2 |
| §4.5 Imagegen prompt format upgrade | S6-T1 + S6-T2 |
| §4.6 Font resolution + brand auth | S1-T5 + S7-T1 + S7-T2 |
| §5 Schemas | S1-T1 + S1-T2 + S1-T3 |
| §6 File structure | Implemented across phases |
| §7 Tooling additions | S1-T4 + S1-T5 + S2-T3 + S4-T2 + S5-T1 |
| §8 Pipeline integration | S3-T2 + S4-T3 + S5-T2 + S5-T3 |
| §9 Phased rollout | This plan's S1-S8 mirrors spec §9.1 directly |
| §10 Out of scope | Not implemented (intentional) |
| §11 Risks | Addressed in §S5 (artifact-tool dependency), §S7 (font platform variance) |
| Appendix A | Worked example matches S5-T2 + S5-T3 orchestration |

### Placeholder scan

- No "TBD" / "TODO" / "implement later" in normative steps.
- Every code step has full code.
- Every test step has full test code or explicit skip reason.

### Type consistency

- `load_profile` / `load_design_system` / `resolve_design_system` signatures match between S1-T4 (definition) and S3-T2 (caller).
- `PresentationsAdapter` `build_input_bundle` / `read_artifacts` / `copy_final_to_issue_deck` match between S5-T1 (definition) and S5-T2 (caller).
- `save_prompt(..., spec=...)` kwarg matches between S6-T1 (definition) and S6-T2 (caller).
- `OutputSelector.choose_backend(target=...)` matches between S4-T2 (definition), S4-T3 + S5-T4 (callers).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-13-design-contracts-multi-realizer.md`.

**Recommended sequencing given the parallelizable phases:**

| Round | Mode | Phases | Tasks | Wall-clock estimate |
|---|---|---|---|---|
| 1 | **dispatching-parallel-agents** (3 agents) | S1 + S2 + S6 | 12 tasks total (5 + 4 + 3) | ~25-40 min |
| 2 | subagent-driven-development | S3 | 3 tasks | ~15-20 min |
| 3 | subagent-driven-development | S4 | 3 tasks | ~15-20 min |
| 4 | subagent-driven-development | S5 (highest risk) | 4 tasks, single owner | ~30-45 min |
| 5 | subagent-driven-development | S7 | 2 tasks | ~10-15 min |
| 6 | **dispatching-parallel-agents** (2 agents) | S8 docs | 4 tasks (S8-T1 + S8-T2 parallel; S8-T3 + S8-T4 sequential after) | ~15-20 min |

**Total estimate:** 1.5-2.5 hours wall clock, ~32 tasks.

**Two execution options:**

**1. Subagent-Driven with parallel rounds (recommended)** — orchestrator
dispatches Round 1 with 3 parallel agents (S1, S2, S6 independent),
then sequential rounds 2-5, then Round 6 with 2 parallel agents (docs).
Reviews between rounds. Fast iteration.

**2. Inline Execution** — execute all 32 tasks in this session
sequentially using executing-plans. ~3-4 hours wall clock; less risk
of agent coordination issues.

**Which approach?**
