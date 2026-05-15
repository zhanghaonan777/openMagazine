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
  3. Copying the final .pptx into the issue output directory.
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
        self,
        *,
        design_system: dict,
        brand: dict,
        article: dict,
        target: dict | None = None,
        regions_by_spread_type: dict | None = None,
    ) -> dict:
        """Produce the spec the agent will use to drive Presentations.

        Returns a serializable dict:
          {
            "presentations_profile": "consumer-retail",
            "task_slug": "cosmos-luna-magazine-pptx",
            "output_format": "magazine-pptx",
            "slide_size": "720x1080",
            "page_count": 16,
            "purpose": "editable-portrait-magazine",
            "design_system_inputs": { ... },
            "brand_authenticity": { ... },
            "text_safe_rules": "...",
            "typography": { ... resolved fallback chains ... },
            "article_excerpt": { titles + leads, no body text },
            "regions_summary": { spread types + role + rect_norm } ,
          }
        """
        target = target or {
            "format": "magazine-pptx",
            "slide_size": "720x1080",
            "page_count": 16,
            "purpose": "editable-portrait-magazine",
        }
        output_format = target.get("format", "magazine-pptx")
        suffix = "magazine-pptx" if output_format == "magazine-pptx" else "deck"

        bundle = {
            "presentations_profile": design_system.get("profile", "consumer-retail"),
            "task_slug": f"{design_system['slug']}-{suffix}",
            "output_format": output_format,
            "slide_size": target.get("slide_size", "720x1080"),
            "page_count": target.get("page_count", 16),
            "purpose": target.get(
                "purpose",
                "editable-portrait-magazine"
                if output_format == "magazine-pptx"
                else "pitch-deck",
            ),
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
            claim_spine: str
            font_substitutions: str
            layout_quality_output: str
            pptx_path: str (absolute)
            slide_count: int
            layout_paths: list[str]
            preview_paths: list[str]
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
            if layout_dir.is_dir()
            else []
        )
        preview_dir = artifact_dir / "preview"
        preview_paths = (
            sorted(str(p) for p in preview_dir.glob("slide-*.png"))
            if preview_dir.is_dir()
            else []
        )
        pptx_dir = artifact_dir / "output"
        pptx_files = (
            sorted(str(p) for p in pptx_dir.glob("*.pptx"))
            if pptx_dir.is_dir()
            else []
        )
        if not pptx_files:
            raise PresentationsArtifactNotFoundError(
                f"no .pptx found in {pptx_dir}"
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
        self,
        *,
        pptx_source: str,
        issue_dir: pathlib.Path,
        slug: str,
        output_format: str = "deck-pptx",
    ) -> pathlib.Path:
        """Copy the produced .pptx into the issue's target-specific subdir."""
        subdir = "magazine-pptx" if output_format == "magazine-pptx" else "deck"
        out_dir = pathlib.Path(issue_dir) / subdir
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"{slug}.pptx"
        shutil.copy2(pptx_source, target)
        return target

    def run(
        self,
        *,
        issue_dir,
        layout,
        brand,
        article,
        spec,
        design_system,
        target=None,
        **kwargs,
    ):
        """The director skill drives Presentations; this run() returns
        the bundled-inputs spec the director uses.

        Director is responsible for invoking Presentations and then
        calling self.read_artifacts() and self.copy_final_to_issue_deck().
        """
        slug = spec["slug"]
        bundle = self.build_input_bundle(
            design_system=design_system,
            brand=brand,
            article=article,
            target=target,
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
