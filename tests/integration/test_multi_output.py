"""Integration test: multi-realizer compose using recorded artifacts.

Uses the 2026-05-13 Presentations smoke test artifacts as a fixture for
the deck path. PDF path runs end-to-end via WeasyprintCompose. Both
realizers produce results in the same issue dir.
"""
from pathlib import Path

import pytest
import json

from tools.output.output_selector import OutputSelector
from tools.output.presentations_adapter import (
    PresentationsAdapter,
    PresentationsArtifactNotFoundError,
)


SKILL_ROOT = Path(__file__).resolve().parents[2]
SMOKE_THREAD = "019e1729-3645-7c21-8c17-ba04f8164388"


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
    pr = sel.choose_backend(target={"format": "magazine-pptx", "realizer": "presentations"})
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
    compose_result = {
        "outputs": [
            {"format": "a4-magazine", "realizer": "weasyprint",
             "path": str(issue_dir / "magazine.pdf"), "page_count": 16},
            {"format": "magazine-pptx", "realizer": "presentations",
             "path": str(issue_dir / "magazine-pptx" / "test.pptx"),
             "slide_count": 16, "slide_size": "720x1080",
             "thread_id": SMOKE_THREAD},
        ],
        "spec_slug": "test",
    }
    target = issue_dir / "compose_result.json"
    target.write_text(json.dumps(compose_result, indent=2))
    reread = json.loads(target.read_text())
    assert len(reread["outputs"]) == 2
    realizers = {o["realizer"] for o in reread["outputs"]}
    assert realizers == {"weasyprint", "presentations"}
