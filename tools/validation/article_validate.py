"""Validate articles/<slug>.yaml against the matching layout's spread_plan."""
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

CLAIM_SPINE_SCHEMA_PATH = SKILL_ROOT / "schemas" / "claim_spine.schema.json"

# Proof-object kinds that point to images. For these, proof_object.ref is
# checked (loosely) against layout.image_slots[*].id — exact id OR a pattern
# like "portrait_wall.[1-6]" where we match the base prefix only.
_IMAGE_KINDS = {"image_slot", "image_grid", "portrait_grid"}
_TEXT_KINDS = {"pull_quote_text", "text_block"}


def _load_yaml(p: pathlib.Path) -> dict:
    return yaml.safe_load(pathlib.Path(p).read_text(encoding="utf-8")) or {}


def _load_claim_spine_schema() -> dict:
    return json.loads(CLAIM_SPINE_SCHEMA_PATH.read_text(encoding="utf-8"))


def _ref_prefix(ref: str) -> str:
    """Return the prefix of an image-slot ref before any bracket pattern.

    'portrait_wall.[1-6]' -> 'portrait_wall'
    'feature_captioned.[1-3]' -> 'feature_captioned'
    'feature_hero' -> 'feature_hero'
    """
    if not isinstance(ref, str):
        return ""
    bracket = ref.find("[")
    head = ref if bracket < 0 else ref[:bracket]
    # Trim a trailing dot left behind by patterns like 'portrait_wall.[1-6]'.
    return head.rstrip(".")


def _slot_id_prefix(slot_id: str) -> str:
    """Return the prefix of an image_slot id before any '.N' suffix."""
    if not isinstance(slot_id, str):
        return ""
    dot = slot_id.find(".")
    return slot_id if dot < 0 else slot_id[:dot]


def _validate_claim_spine(article: dict, layout: dict) -> list[str]:
    """Validate article.claim_spine (when present) and cross-check with the
    article's spread_copy + layout's image_slots.

    Returns a list of error messages prefixed with 'claim_spine: '. Empty when
    claim_spine is absent or fully valid.
    """
    errors: list[str] = []
    spine = article.get("claim_spine")
    if spine is None:
        return errors

    # 1. Schema validation.
    schema = _load_claim_spine_schema()
    for e in Draft7Validator(schema).iter_errors(spine):
        path = "/".join(str(p) for p in e.path) or "<root>"
        errors.append(f"claim_spine: {path}: {e.message}")

    spread_claims = spine.get("spread_claims") or []
    spread_copy = article.get("spread_copy") or []
    image_slots = layout.get("image_slots") or []

    # Build lookup tables.
    copy_by_idx: dict[int, dict] = {}
    for c in spread_copy:
        if isinstance(c, dict) and "idx" in c:
            copy_by_idx[c["idx"]] = c
    # Per-spread + global slot lookups so we can tell apart
    # "ref doesn't exist anywhere" from "ref exists on a different spread".
    slots_by_spread: dict[int, set[str]] = {}
    prefixes_by_spread: dict[int, set[str]] = {}
    spread_of_slot: dict[str, set[int]] = {}
    for s in image_slots:
        if not isinstance(s, dict):
            continue
        sid = s.get("id")
        sidx = s.get("spread_idx")
        if not (isinstance(sid, str) and isinstance(sidx, int)):
            continue
        slots_by_spread.setdefault(sidx, set()).add(sid)
        prefixes_by_spread.setdefault(sidx, set()).add(_slot_id_prefix(sid))
        spread_of_slot.setdefault(sid, set()).add(sidx)
    slot_ids: set[str] = set().union(*slots_by_spread.values()) if slots_by_spread else set()
    slot_prefixes: set[str] = (
        set().union(*prefixes_by_spread.values()) if prefixes_by_spread else set()
    )
    slot_prefixes.discard("")

    claimed_idxs: set[int] = set()

    # 2. Per-claim cross-checks.
    for i, claim in enumerate(spread_claims):
        if not isinstance(claim, dict):
            continue
        idx = claim.get("spread_idx")
        ctype = claim.get("spread_type")
        if isinstance(idx, int):
            claimed_idxs.add(idx)
            match = copy_by_idx.get(idx)
            if match is None:
                errors.append(
                    f"claim_spine: spread_claims[{i}]: spread_idx {idx} not "
                    f"found in article.spread_copy"
                )
            else:
                copy_type = match.get("type")
                if ctype is not None and copy_type is not None and ctype != copy_type:
                    errors.append(
                        f"claim_spine: spread_claims[{i}] (idx {idx}): "
                        f"spread_type {ctype!r} does not match "
                        f"spread_copy.type {copy_type!r}"
                    )

        # proof_object ref checks (only when present + not exempt).
        if claim.get("exempt"):
            continue
        proof = claim.get("proof_object")
        if not isinstance(proof, dict):
            continue
        kind = proof.get("kind")
        ref = proof.get("ref")

        if kind in _IMAGE_KINDS:
            if not isinstance(ref, str) or not ref:
                errors.append(
                    f"claim_spine: spread_claims[{i}] (idx {idx}): "
                    f"proof_object.ref must be a non-empty string for kind "
                    f"{kind!r}"
                )
            else:
                prefix = _ref_prefix(ref)
                # 1. Try same-spread match first (the strict case): claim on
                #    spread N must reference an image_slot also on spread N.
                idx_known = isinstance(idx, int)
                on_this_spread = idx_known and (
                    ref in slots_by_spread.get(idx, set())
                    or prefix in prefixes_by_spread.get(idx, set())
                )
                # 2. Fall back to global existence (any spread).
                exists_anywhere = (ref in slot_ids) or (prefix in slot_prefixes)

                if on_this_spread:
                    pass  # OK
                elif idx_known and exists_anywhere:
                    # Slot exists in the layout but on a different spread —
                    # a claim on spread N pointing at a slot on spread M.
                    where = sorted(spread_of_slot.get(ref, set()))
                    if not where:
                        # Match was by prefix only; report spreads that share
                        # the prefix.
                        where = sorted(
                            sidx for sidx, prefixes in prefixes_by_spread.items()
                            if prefix in prefixes
                        )
                    errors.append(
                        f"claim_spine: spread_claims[{i}] (idx {idx}): "
                        f"proof_object.ref {ref!r} refers to an image_slot on "
                        f"spread(s) {where} but this claim is on spread {idx}"
                    )
                elif not exists_anywhere:
                    errors.append(
                        f"claim_spine: spread_claims[{i}] (idx {idx}): "
                        f"proof_object.ref {ref!r} does not match any "
                        f"layout image_slot id (looked up exact id and "
                        f"prefix {prefix!r})"
                    )
        elif kind in _TEXT_KINDS:
            if not isinstance(ref, str) or not ref:
                errors.append(
                    f"claim_spine: spread_claims[{i}] (idx {idx}): "
                    f"proof_object.ref must be a non-empty string for kind "
                    f"{kind!r}"
                )

    # 3. Every spread_copy idx must have a matching claim when spine is present.
    for c in spread_copy:
        if not isinstance(c, dict):
            continue
        cidx = c.get("idx")
        if isinstance(cidx, int) and cidx not in claimed_idxs:
            errors.append(
                f"claim_spine: spread_copy idx {cidx} has no matching entry "
                f"in claim_spine.spread_claims"
            )

    return errors


def _resolve_layout(layout_arg: pathlib.Path) -> pathlib.Path:
    """Accept either a layout yaml path or a library layout slug."""
    if layout_arg.is_file():
        return layout_arg
    if layout_arg.suffix:
        return layout_arg
    candidate = SKILL_ROOT / "library" / "layouts" / f"{layout_arg}.yaml"
    if candidate.is_file():
        return candidate
    return layout_arg


def validate_article(article_path: pathlib.Path, layout_path: pathlib.Path) -> list[str]:
    """Return list of error messages. Empty list = valid."""
    errors: list[str] = []
    a = _load_yaml(article_path)
    layout = _load_yaml(layout_path)

    if a.get("schema_version") != 1:
        errors.append(f"article schema_version must be 1, got {a.get('schema_version')!r}")
    for field in ("slug", "display_title", "issue_label", "cover_line",
                  "cover_kicker", "spread_copy"):
        if field not in a:
            errors.append(f"article: required field {field!r} missing")

    plan = layout.get("spread_plan") or []
    copy = a.get("spread_copy") or []
    image_slots = layout.get("image_slots") or []

    if len(plan) != len(copy):
        errors.append(
            f"spread count mismatch: layout.spread_plan has {len(plan)} entries, "
            f"article.spread_copy has {len(copy)}"
        )

    required = layout.get("text_slots_required") or {}
    n = min(len(plan), len(copy))
    for i in range(n):
        p_entry = plan[i]
        c_entry = copy[i]
        if p_entry.get("idx") != c_entry.get("idx"):
            errors.append(
                f"spread idx mismatch at position {i}: "
                f"layout.idx={p_entry.get('idx')}, article.idx={c_entry.get('idx')}"
            )
        if p_entry.get("type") != c_entry.get("type"):
            errors.append(
                f"spread type mismatch at idx {p_entry.get('idx')}: "
                f"layout.type={p_entry.get('type')!r}, article.type={c_entry.get('type')!r}"
            )
        # required text fields per type
        spread_type = p_entry.get("type")
        for field in required.get(spread_type, []):
            if field not in c_entry:
                errors.append(
                    f"spread {p_entry.get('idx')} ({spread_type}): "
                    f"required field {field!r} missing"
                )
        overrides = c_entry.get("image_slot_overrides") or {}
        if overrides and not isinstance(overrides, dict):
            errors.append(
                f"spread {p_entry.get('idx')} ({spread_type}): "
                "image_slot_overrides must be a mapping"
            )
            overrides = {}
        expected_slots = [
            slot["id"] for slot in image_slots
            if slot.get("spread_idx") == p_entry.get("idx")
        ]
        for slot_id in expected_slots:
            if slot_id not in overrides:
                errors.append(
                    f"spread {p_entry.get('idx')} ({spread_type}): "
                    f"image_slot_overrides missing slot {slot_id!r}"
                )

    errors.extend(_validate_claim_spine(a, layout))

    return errors


class ArticleValidate(BaseTool):
    capability = "validation"
    provider = "local"
    status = "active"
    agent_skills = ["spec-validate-usage"]

    def run(self, article_path: pathlib.Path, layout_path: pathlib.Path) -> list[str]:
        return validate_article(article_path, layout_path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("article", type=pathlib.Path)
    p.add_argument("--layout", type=pathlib.Path, required=True)
    a = p.parse_args(argv)
    layout_path = _resolve_layout(a.layout)
    errs = validate_article(a.article, layout_path)
    if not errs:
        print(f"✓ {a.article.name}: valid against {layout_path.name}", file=sys.stderr)
        return 0
    print(f"✗ {a.article.name}: {len(errs)} error(s)", file=sys.stderr)
    for e in errs:
        print(f"  {e}", file=sys.stderr)
    return 1


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(ArticleValidate())


if __name__ == "__main__":
    sys.exit(main())
