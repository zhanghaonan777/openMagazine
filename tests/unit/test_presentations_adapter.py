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
