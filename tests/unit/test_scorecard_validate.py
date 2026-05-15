"""Tests for scorecard validator (schema + anti-spoof gate_result recompute)."""
from __future__ import annotations

import copy
import json
import pathlib

import pytest

from tools.validation.scorecard_validate import (
    compute_gate_result,
    validate_scorecard,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

_REQUIRED_DIMS = (
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


def _dim(score: int, name: str = "concrete evidence string longer than ten chars") -> dict:
    return {"score": score, "evidence": f"{name} for score={score}"}


def _build_scorecard(
    *,
    reference_supplied: bool = False,
    scores: dict | None = None,
    reference_delta: dict | None = None,
    profile_gates: list | None = None,
    anti_patterns: list | None = None,
    claimed_pass: bool = True,
    claimed_raw_total: int | None = None,
    claimed_max_total: int | None = None,
    thresholds: dict | None = None,
) -> dict:
    """Hand-build a scorecard dict. Defaults to an all-5s passing card."""
    scores = scores or {}
    dimensions = {name: _dim(scores.get(name, 5)) for name in _REQUIRED_DIMS}
    if reference_delta is not None:
        dimensions["reference_delta"] = reference_delta

    int_scores = [d["score"] for d in dimensions.values() if isinstance(d.get("score"), int)]
    raw_total = claimed_raw_total if claimed_raw_total is not None else sum(int_scores)

    if claimed_max_total is not None:
        max_total = claimed_max_total
    else:
        ref_is_int = (
            reference_delta is not None
            and isinstance(reference_delta.get("score"), int)
        )
        max_total = 50 if (reference_supplied and ref_is_int) else 45

    dims_scored = 10 if "reference_delta" in dimensions else 9

    th = thresholds or {
        "min_total": 44 if reference_supplied else 40,
        "min_per_dimension": 4,
    }

    return {
        "schema_version": 1,
        "spec_slug": "test-slug",
        "scored_at": "2026-05-15T12:00:00Z",
        "reference_supplied": reference_supplied,
        "dimensions": dimensions,
        "totals": {
            "raw_total": raw_total,
            "max_total": max_total,
            "dimensions_scored": dims_scored,
        },
        "profile_gates": profile_gates or [],
        "anti_patterns_detected": anti_patterns or [],
        "iteration_targets": [],
        "gate_result": {
            "pass": claimed_pass,
            "min_dimension_score": min(int_scores) if int_scores else 0,
            "any_dimension_below_4": any(s < 4 for s in int_scores),
            "any_profile_gate_failed": any(
                isinstance(g, dict) and g.get("result") == "fail"
                for g in (profile_gates or [])
            ),
            "blocking_anti_patterns": sum(
                1 for p in (anti_patterns or [])
                if isinstance(p, dict) and p.get("severity") == "block"
            ),
            "thresholds_used": th,
        },
    }


def _write(tmp_path: pathlib.Path, data: dict, name: str = "scorecard.json") -> pathlib.Path:
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_valid_scorecard_passes(tmp_path):
    """All 9 required dims at score 5; gate_result.pass=True; no errors."""
    data = _build_scorecard()
    path = _write(tmp_path, data)
    assert validate_scorecard(path) == []


def test_dim_below_4_fails_gate(tmp_path):
    """One dim at 3, but claim pass=True -> validator surfaces disagreement."""
    data = _build_scorecard(scores={"rhythm": 3}, claimed_pass=True)
    # The hand-built helper recomputes min_dimension_score honestly, so fix
    # the claim to be plausibly schema-valid but the `pass` field is the lie.
    path = _write(tmp_path, data)
    errs = validate_scorecard(path)
    assert any("gate_result.pass" in e for e in errs), errs
    assert any("claimed True but recomputed False" in e for e in errs), errs


def test_blocking_anti_pattern_fails_gate(tmp_path):
    """All-5s deck but one severity=block anti-pattern -> gate must fail."""
    anti = [{
        "pattern": "rounded-cards-as-default",
        "where": "spread 3",
        "severity": "block",
    }]
    data = _build_scorecard(anti_patterns=anti, claimed_pass=True)
    # Honest schema would set blocking_anti_patterns=1, but the recompute
    # check looks at the claimed `pass` field specifically.
    path = _write(tmp_path, data)
    errs = validate_scorecard(path)
    assert any("gate_result.pass" in e and "blocking anti-pattern" in e for e in errs), errs


def test_profile_gate_fail_fails_gate(tmp_path):
    """All-5s deck but one profile gate result=fail -> gate must fail."""
    gates = [{
        "rule": "brand_authenticity_gate",
        "result": "fail",
        "evidence": "fabricated logo on spread 1",
    }]
    data = _build_scorecard(profile_gates=gates, claimed_pass=True)
    path = _write(tmp_path, data)
    errs = validate_scorecard(path)
    assert any("gate_result.pass" in e and "profile_gate" in e for e in errs), errs


def test_reference_supplied_threshold(tmp_path):
    """reference_supplied=true, raw_total=43, claim pass=True -> below 44 threshold."""
    # 8 dims at 5 = 40, then one at 3 to get to 43; we use a different shape:
    # 8 dims at 5 (=40) + image_clarity=4 (=44? no we want 43). 7 dims at 5
    # (35) + 2 dims at 4 (8) = 43.
    scores = {
        "story": 5, "specificity": 5, "rhythm": 5, "whitespace": 5,
        "image_clarity": 4, "typography": 5, "restraint": 5,
        "precision": 5, "coherence": 4,
    }
    # No reference_delta -> max_total stays 45, total 43, threshold 44 -> fail.
    data = _build_scorecard(
        reference_supplied=True,
        scores=scores,
        claimed_pass=True,
    )
    path = _write(tmp_path, data)
    errs = validate_scorecard(path)
    assert any("gate_result.pass" in e for e in errs), errs
    assert any("raw_total 43 < min_total 44" in e for e in errs), errs


def test_n_a_reference_delta(tmp_path):
    """reference_supplied=false + reference_delta.score='n/a' -> max_total=45."""
    data = _build_scorecard(
        reference_supplied=False,
        reference_delta={"score": "n/a", "evidence": "no reference supplied"},
    )
    # _build_scorecard already set max_total=45 because the ref score is not int.
    assert data["totals"]["max_total"] == 45
    path = _write(tmp_path, data)
    assert validate_scorecard(path) == []


def test_missing_required_field_schema_error(tmp_path):
    """Drop a required top-level field -> schema error prefix appears."""
    data = _build_scorecard()
    del data["scored_at"]
    path = _write(tmp_path, data)
    errs = validate_scorecard(path)
    assert any(e.startswith("scorecard:") and "scored_at" in e for e in errs), errs


def test_compute_gate_result_pure():
    """Directly exercise the pure function with several shapes."""
    all5 = {name: {"score": 5, "evidence": "x" * 10} for name in _REQUIRED_DIMS}
    r = compute_gate_result(
        dimensions=all5,
        reference_supplied=False,
        anti_patterns=[],
        profile_gates=[],
    )
    assert r["pass"] is True
    assert r["min_dimension_score"] == 5
    assert r["any_dimension_below_4"] is False
    assert r["any_profile_gate_failed"] is False
    assert r["blocking_anti_patterns"] == 0
    assert r["thresholds_used"] == {"min_total": 40, "min_per_dimension": 4}

    # One dim at 3 -> fail (below 4 + total dropped).
    one_low = copy.deepcopy(all5)
    one_low["rhythm"]["score"] = 3
    r2 = compute_gate_result(
        dimensions=one_low,
        reference_supplied=False,
        anti_patterns=[],
        profile_gates=[],
    )
    assert r2["pass"] is False
    assert r2["any_dimension_below_4"] is True
    assert r2["min_dimension_score"] == 3

    # Reference supplied with int reference_delta -> max_total scales (44 threshold).
    with_ref = copy.deepcopy(all5)
    with_ref["reference_delta"] = {"score": 4, "evidence": "beats reference"}
    r3 = compute_gate_result(
        dimensions=with_ref,
        reference_supplied=True,
        anti_patterns=[],
        profile_gates=[],
    )
    assert r3["pass"] is True  # 9*5 + 4 = 49 >= 44
    assert r3["thresholds_used"]["min_total"] == 44

    # Blocking anti-pattern alone flips pass to False.
    r4 = compute_gate_result(
        dimensions=all5,
        reference_supplied=False,
        anti_patterns=[{"pattern": "x", "where": "y", "severity": "block"}],
        profile_gates=[],
    )
    assert r4["pass"] is False
    assert r4["blocking_anti_patterns"] == 1

    # warn-severity does NOT flip pass.
    r5 = compute_gate_result(
        dimensions=all5,
        reference_supplied=False,
        anti_patterns=[{"pattern": "x", "where": "y", "severity": "warn"}],
        profile_gates=[],
    )
    assert r5["pass"] is True
    assert r5["blocking_anti_patterns"] == 0

    # Failing profile gate flips pass.
    r6 = compute_gate_result(
        dimensions=all5,
        reference_supplied=False,
        anti_patterns=[],
        profile_gates=[{"rule": "x", "result": "fail"}],
    )
    assert r6["pass"] is False
    assert r6["any_profile_gate_failed"] is True

    # n/a reference_delta is excluded from total; max stays 45.
    na_ref = copy.deepcopy(all5)
    na_ref["reference_delta"] = {"score": "n/a", "evidence": "no ref"}
    r7 = compute_gate_result(
        dimensions=na_ref,
        reference_supplied=False,
        anti_patterns=[],
        profile_gates=[],
    )
    assert r7["pass"] is True
    # Only the 9 required dims contribute to min/total -> min still 5.
    assert r7["min_dimension_score"] == 5


def test_tool_registers():
    """ScorecardValidate registers itself with the global tool registry."""
    from tools.tool_registry import registry
    names = {type(t).__name__ for t in registry.all_tools()}
    assert "ScorecardValidate" in names
