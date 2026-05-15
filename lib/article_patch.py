"""article_patch — apply browser-edited HTML patches back to article.yaml.

The HtmlInteractiveCompose realizer renders manifest -> editable HTML.
When the user edits text and clicks Save, the browser downloads an
article-patch.json:

    {
      "generated_at": "2026-05-15T16:00:00Z",
      "spec_slug": "cosmos-luna-may-2026",
      "locale": "en",
      "patches": {
        "spread.3.title": "Four billion years of silence",
        "cover_line": "An astronaut who never came back."
      }
    }

This module reads that patch and merges the edits into
library/articles/<slug>.yaml. bind_field syntax:

  - "<field>"             -> article[field] (set or bilingual)
  - "spread.<idx>.<field>" -> article.spread_copy[i where idx==<idx>].field

Locale is patch-level: a single patch applies to ONE language. The
other language survives untouched. This matches how the browser
interactive renderer works: one manifest per locale, one set of edits
per locale.

CLI:
    python -m lib.article_patch library/articles/<slug>.yaml \\
        output/<slug>/article-patch.json --output - > new-article.yaml
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
from typing import Any

import yaml


class PatchError(ValueError):
    """Raised when a patch can't be applied (bad bind_field, missing target)."""


def apply_patch(article: dict, patch: dict, *, strict: bool = True) -> dict:
    """Return a new article dict with the patches applied.

    strict=True (default): unknown bind_fields raise PatchError. Set to
    False to skip them silently — useful when iterating on the manifest
    builder before article.yaml fields catch up.
    """
    if not isinstance(patch, dict):
        raise PatchError(f"patch must be a dict, got {type(patch).__name__}")
    patches = patch.get("patches") or {}
    if not isinstance(patches, dict):
        raise PatchError("patch.patches must be a dict of bind_field -> string")
    locale = patch.get("locale") or "en"

    result = copy.deepcopy(article)
    applied: list[tuple[str, str]] = []
    for bind_field, value in patches.items():
        if not isinstance(value, str):
            if strict:
                raise PatchError(
                    f"patch value for {bind_field!r} must be a string"
                )
            continue
        try:
            _set_by_bind_field(result, bind_field, value, locale=locale)
            applied.append((bind_field, value))
        except PatchError:
            if strict:
                raise
    return result


def _set_by_bind_field(article: dict, bind_field: str, value: str, *, locale: str) -> None:
    if not isinstance(bind_field, str) or not bind_field:
        raise PatchError("bind_field must be a non-empty string")
    parts = bind_field.split(".")

    if parts[0] == "spread":
        if len(parts) < 3:
            raise PatchError(
                f"bind_field {bind_field!r}: spread form is 'spread.<idx>.<field>'"
            )
        try:
            idx = int(parts[1])
        except ValueError:
            raise PatchError(
                f"bind_field {bind_field!r}: spread idx must be an int, got {parts[1]!r}"
            )
        field_path = parts[2:]
        spread_copy = article.get("spread_copy")
        if not isinstance(spread_copy, list):
            raise PatchError("article has no spread_copy list")
        for entry in spread_copy:
            if isinstance(entry, dict) and entry.get("idx") == idx:
                _set_nested_bilingual(entry, field_path, value, locale)
                return
        raise PatchError(
            f"bind_field {bind_field!r}: no spread_copy entry with idx={idx}"
        )

    # Top-level field: e.g. cover_line, cover_kicker.
    _set_nested_bilingual(article, parts, value, locale)


def _set_nested_bilingual(container: dict, path: list[str], value: str, locale: str) -> None:
    """Walk path inside container. The leaf becomes either a string or a
    bilingual dict whose `locale` key holds the value, preserving any other
    locales already there."""
    if not path:
        raise PatchError("empty field path")
    *intermediate, leaf = path
    cursor: Any = container
    for key in intermediate:
        if not isinstance(cursor, dict):
            raise PatchError(f"cannot traverse non-dict at {key!r}")
        cursor = cursor.setdefault(key, {})
    if not isinstance(cursor, dict):
        raise PatchError(f"cannot set field {leaf!r}: parent is not a dict")

    existing = cursor.get(leaf)
    if isinstance(existing, dict):
        # Bilingual dict: set just the locale key.
        existing[locale] = value
    elif isinstance(existing, str) or existing is None:
        # Either uninitialised or a plain string. Always promote to a
        # bilingual dict so we don't accidentally clobber a future second
        # locale. If the original was a plain string in some locale != ours,
        # we preserve it under the patch's locale only.
        cursor[leaf] = {locale: value}
    else:
        raise PatchError(
            f"cannot set field {leaf!r}: existing value is {type(existing).__name__}"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("article", type=pathlib.Path, help="library/articles/<slug>.yaml")
    p.add_argument("patch", type=pathlib.Path, help="article-patch.json")
    p.add_argument(
        "--output", "-o", default="-",
        help="Output path for the patched article (default: stdout)",
    )
    p.add_argument(
        "--lenient", action="store_true",
        help="Skip patches whose bind_field can't be resolved instead of failing",
    )
    args = p.parse_args(argv)

    article = yaml.safe_load(args.article.read_text(encoding="utf-8"))
    patch = json.loads(args.patch.read_text(encoding="utf-8"))
    try:
        out = apply_patch(article, patch, strict=not args.lenient)
    except PatchError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    text = yaml.safe_dump(out, allow_unicode=True, sort_keys=False)
    if args.output == "-":
        sys.stdout.write(text)
    else:
        pathlib.Path(args.output).write_text(text, encoding="utf-8")
        print(f"wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
