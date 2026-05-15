"""HtmlInteractiveCompose — manifest -> editable HTML realizer.

Produces output/<slug>/magazine-interactive/index.html. Text regions are
contenteditable; a floating toolbar lets the user download an
article-patch.json with every edit keyed by bind_field. The patch can be
applied back to library/articles/<slug>.yaml via
`python -m lib.article_patch apply <article.yaml> <patch.json>`.

This is the second realizer that consumes slide_manifest (after
WeasyprintCompose.render_from_manifest). It demonstrates that the
manifest contract supports both PDF (final-output) and HTML
(round-trippable, editable) realizations from the same upstream data.

No native dependencies; pure Python + emitted vanilla JS.
"""
from __future__ import annotations

import json
import pathlib

from lib.manifest_to_html import manifest_to_html
from tools.base_tool import BaseTool


class HtmlInteractiveCompose(BaseTool):
    capability = "output_realizer"
    provider = "html-interactive"
    cost_per_call_usd = 0.0
    status = "experimental"

    def run(
        self,
        *,
        manifest: dict,
        issue_dir: pathlib.Path,
        out_dir: pathlib.Path | None = None,
        **_kwargs,
    ) -> dict:
        """Render manifest to an editable HTML doc.

        out_dir defaults to ``issue_dir / "magazine-interactive"``. The
        directory is created if absent. Returns metadata about the
        produced artifact (path + size + edit-region count).
        """
        issue_dir = pathlib.Path(issue_dir)
        out_dir = pathlib.Path(out_dir) if out_dir else issue_dir / "magazine-interactive"
        out_dir.mkdir(parents=True, exist_ok=True)
        index_path = out_dir / "index.html"

        html = manifest_to_html(manifest, issue_dir=issue_dir, interactive=True)
        index_path.write_text(html, encoding="utf-8")

        # Count editable regions for the run metadata — useful in
        # compose_result.json and downstream contact_sheet rubrics.
        editable_count = html.count('contenteditable="true"')
        size_kb = index_path.stat().st_size / 1024.0

        meta: dict = {
            "html_path": str(index_path),
            "size_kb": round(size_kb, 1),
            "editable_regions": editable_count,
            "slide_count": len(manifest.get("slides", [])),
            "spec_slug": manifest.get("spec_slug", ""),
            "locale": manifest.get("locale", "en"),
        }
        # Sidecar JSON: lets other tools find the manifest path that
        # produced this HTML without re-running the builder.
        (out_dir / "compose_result.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return meta


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(HtmlInteractiveCompose())
