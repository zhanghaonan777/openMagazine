"""Validate articles/<slug>.yaml against the matching layout's spread_plan."""
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any

import yaml

from tools.base_tool import BaseTool


def _load_yaml(p: pathlib.Path) -> dict:
    return yaml.safe_load(pathlib.Path(p).read_text(encoding="utf-8")) or {}


def validate_article(article_path: pathlib.Path, layout_path: pathlib.Path) -> list[str]:
    """Return list of error messages. Empty list = valid."""
    errors: list[str] = []
    a = _load_yaml(article_path)
    layout = _load_yaml(layout_path)

    if a.get("schema_version") != 1:
        errors.append(f"article schema_version must be 1, got {a.get('schema_version')!r}")

    plan = layout.get("spread_plan") or []
    copy = a.get("spread_copy") or []

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
    errs = validate_article(a.article, a.layout)
    if not errs:
        print(f"✓ {a.article.name}: valid against {a.layout.name}", file=sys.stderr)
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
