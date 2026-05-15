"""Validate output/<slug>/qa/scorecard.json against schemas/artifacts/qa/scorecard.schema.json.

Performs three checks:
  1. JSON Schema (Draft7) validation of the file.
  2. Recompute `gate_result` from dimensions + anti_patterns + profile_gates and
     compare with the claimed `gate_result`. Disagreement is an error — this is
     the anti-spoof check that stops an agent from claiming `pass=true` while
     the data says fail.
  3. Surface schema errors with a stable `"scorecard: <path>: <message>"` prefix.

See skills/meta/comeback-scorer.md for the rubric, anti-pattern catalogue, and
iteration rule.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

import yaml
from jsonschema import Draft7Validator

SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from tools.base_tool import BaseTool

SCORECARD_SCHEMA_PATH = SKILL_ROOT / "schemas" / "artifacts" / "qa" / "scorecard.schema.json"

# Dimensions counted toward the numeric rubric. `reference_delta` is optional
# and joins the total only when its score is an int (not "n/a").
_REQUIRED_DIMENSIONS = (
    "story",
    "specificity",
    "rhythm",
    "whitespace",
    "image_clarity",
    "typography",
    "restraint",
    "precision",
    "coherence",
)


def _load_scorecard(path: pathlib.Path) -> dict:
    """Load scorecard from JSON (default) or YAML (by .yaml/.yml extension)."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(text) or {}
    return json.loads(text)


def _load_schema() -> dict:
    return json.loads(SCORECARD_SCHEMA_PATH.read_text(encoding="utf-8"))


def compute_gate_result(
    dimensions: dict,
    reference_supplied: bool,
    anti_patterns: list,
    profile_gates: list,
    thresholds: dict | None = None,
) -> dict:
    """Pure function. Recompute gate_result from raw scorecard parts.

    Returns a dict matching schemas/artifacts/scorecard.schema.json#/properties/gate_result.
    """
    if thresholds is None:
        thresholds = {
            "min_total": 44 if reference_supplied else 40,
            "min_per_dimension": 4,
        }
    min_total = int(thresholds.get("min_total", 44 if reference_supplied else 40))
    min_per_dim = int(thresholds.get("min_per_dimension", 4))

    int_scores: list[int] = []
    for name in _REQUIRED_DIMENSIONS:
        dim = (dimensions or {}).get(name) or {}
        score = dim.get("score")
        if isinstance(score, bool):
            # Defensive: bools are ints in Python. Treat as not-an-int.
            continue
        if isinstance(score, int):
            int_scores.append(score)

    ref_delta = (dimensions or {}).get("reference_delta") or {}
    ref_score = ref_delta.get("score")
    ref_is_int = isinstance(ref_score, int) and not isinstance(ref_score, bool)
    if reference_supplied and ref_is_int:
        int_scores_for_total = int_scores + [ref_score]
        max_total = 50
    else:
        int_scores_for_total = int_scores
        max_total = 45

    raw_total = sum(int_scores_for_total)
    min_dim_score = min(int_scores_for_total) if int_scores_for_total else 0
    any_below_4 = any(s < min_per_dim for s in int_scores_for_total)

    any_gate_failed = any(
        isinstance(g, dict) and g.get("result") == "fail"
        for g in (profile_gates or [])
    )
    blocking = sum(
        1 for p in (anti_patterns or [])
        if isinstance(p, dict) and p.get("severity") == "block"
    )

    passed = (
        raw_total >= min_total
        and not any_below_4
        and not any_gate_failed
        and blocking == 0
    )

    return {
        "pass": passed,
        "min_dimension_score": int(min_dim_score),
        "any_dimension_below_4": bool(any_below_4),
        "any_profile_gate_failed": bool(any_gate_failed),
        "blocking_anti_patterns": int(blocking),
        "thresholds_used": {
            "min_total": min_total,
            "min_per_dimension": min_per_dim,
        },
    }


def _why_pass_disagrees(claimed: dict, recomputed: dict, raw_total: int) -> str:
    """Human-readable reason list for a gate_result.pass disagreement."""
    reasons: list[str] = []
    if recomputed["any_dimension_below_4"]:
        reasons.append(
            f"min dimension {recomputed['min_dimension_score']} < "
            f"{recomputed['thresholds_used']['min_per_dimension']}"
        )
    if recomputed["any_profile_gate_failed"]:
        reasons.append("a profile_gate result=fail")
    if recomputed["blocking_anti_patterns"] > 0:
        reasons.append(
            f"{recomputed['blocking_anti_patterns']} blocking anti-pattern(s)"
        )
    if raw_total < recomputed["thresholds_used"]["min_total"]:
        reasons.append(
            f"raw_total {raw_total} < min_total "
            f"{recomputed['thresholds_used']['min_total']}"
        )
    if not reasons and not recomputed["pass"]:
        reasons.append("unknown")
    return "; ".join(reasons) if reasons else "none"


def validate_scorecard(scorecard_path: pathlib.Path) -> list[str]:
    """Return list of error messages. Empty list = valid."""
    errors: list[str] = []

    try:
        data = _load_scorecard(scorecard_path)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        return [f"scorecard: {scorecard_path}: failed to parse: {e}"]

    if not isinstance(data, dict):
        return [f"scorecard: {scorecard_path}: root must be a mapping"]

    schema = _load_schema()
    for e in Draft7Validator(schema).iter_errors(data):
        path = "/".join(str(p) for p in e.path) or "<root>"
        errors.append(f"scorecard: {scorecard_path}: {path}: {e.message}")

    # Even on schema errors, attempt the recompute when the shape allows it —
    # this surfaces both classes of error in one pass.
    dimensions = data.get("dimensions") if isinstance(data.get("dimensions"), dict) else {}
    reference_supplied = bool(data.get("reference_supplied"))
    anti_patterns = data.get("anti_patterns_detected") or []
    profile_gates = data.get("profile_gates") or []
    claimed_gate = data.get("gate_result") or {}

    # If gate_result.thresholds_used is present and valid, honor it; this lets
    # callers override the default thresholds intentionally.
    thresholds = None
    claimed_thresh = claimed_gate.get("thresholds_used") if isinstance(claimed_gate, dict) else None
    if isinstance(claimed_thresh, dict) \
            and isinstance(claimed_thresh.get("min_total"), int) \
            and isinstance(claimed_thresh.get("min_per_dimension"), int):
        thresholds = {
            "min_total": claimed_thresh["min_total"],
            "min_per_dimension": claimed_thresh["min_per_dimension"],
        }

    recomputed = compute_gate_result(
        dimensions=dimensions,
        reference_supplied=reference_supplied,
        anti_patterns=anti_patterns,
        profile_gates=profile_gates,
        thresholds=thresholds,
    )

    # Recompute raw_total for the reason string (compute_gate_result doesn't
    # return it; the schema's `totals.raw_total` is the canonical place).
    int_scores: list[int] = []
    for name in _REQUIRED_DIMENSIONS:
        dim = (dimensions or {}).get(name) or {}
        s = dim.get("score")
        if isinstance(s, int) and not isinstance(s, bool):
            int_scores.append(s)
    ref_delta = (dimensions or {}).get("reference_delta") or {}
    ref_score = ref_delta.get("score")
    if reference_supplied and isinstance(ref_score, int) and not isinstance(ref_score, bool):
        int_scores.append(ref_score)
    recomputed_total = sum(int_scores)

    if isinstance(claimed_gate, dict) and "pass" in claimed_gate:
        claimed_pass = bool(claimed_gate.get("pass"))
        if claimed_pass != recomputed["pass"]:
            reasons = _why_pass_disagrees(claimed_gate, recomputed, recomputed_total)
            errors.append(
                f"scorecard.gate_result.pass: claimed {claimed_pass} but "
                f"recomputed {recomputed['pass']} (reasons: {reasons})"
            )

    # Also cross-check totals.raw_total / max_total when present.
    totals = data.get("totals") or {}
    if isinstance(totals, dict):
        claimed_raw = totals.get("raw_total")
        if isinstance(claimed_raw, int) and claimed_raw != recomputed_total:
            errors.append(
                f"scorecard.totals.raw_total: claimed {claimed_raw} but "
                f"recomputed {recomputed_total} from dimension scores"
            )
        claimed_max = totals.get("max_total")
        expected_max = 50 if (
            reference_supplied
            and isinstance(ref_score, int) and not isinstance(ref_score, bool)
        ) else 45
        if isinstance(claimed_max, int) and claimed_max != expected_max:
            errors.append(
                f"scorecard.totals.max_total: claimed {claimed_max} but "
                f"expected {expected_max} (reference_supplied={reference_supplied}, "
                f"reference_delta score is int={isinstance(ref_score, int) and not isinstance(ref_score, bool)})"
            )

    return errors


class ScorecardValidate(BaseTool):
    capability = "validation"
    provider = "local"
    status = "active"
    agent_skills = ["comeback-scorer"]

    def run(self, scorecard_path: pathlib.Path) -> list[str]:
        return validate_scorecard(pathlib.Path(scorecard_path))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("scorecard", type=pathlib.Path)
    a = p.parse_args(argv)
    errs = validate_scorecard(a.scorecard)
    if not errs:
        print(f"✓ {a.scorecard.name}: scorecard passes", file=sys.stderr)
        return 0
    print(f"✗ {a.scorecard.name}: {len(errs)} error(s)", file=sys.stderr)
    for e in errs:
        print(f"  {e}", file=sys.stderr)
    return 1


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(ScorecardValidate())


if __name__ == "__main__":
    sys.exit(main())
