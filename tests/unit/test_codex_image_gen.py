"""Tests for CodexImageGen BEFORE/AFTER PNG capture."""
import pathlib
import time

import pytest


@pytest.fixture
def fake_gen_dir(tmp_path, monkeypatch):
    """Replace CODEX_GEN_DIR with a tmp_path so we can simulate generated_images/."""
    from tools.image import codex_image_gen as mod
    fake_dir = tmp_path / "generated_images"
    fake_dir.mkdir()
    monkeypatch.setattr(mod, "CODEX_GEN_DIR", fake_dir)
    return fake_dir


def test_run_returns_before_snapshot_when_dir_empty(fake_gen_dir):
    from tools.image.codex_image_gen import CodexImageGen
    tool = CodexImageGen()
    state = tool.run()
    assert state["before_path"] is None
    assert "ts" in state


def test_run_rejects_non_storyboard_mode(fake_gen_dir):
    from tools.image.codex_image_gen import CodexImageGen
    tool = CodexImageGen()
    with pytest.raises(ValueError):
        tool.run(mode="upscale")


def test_capture_new_png_finds_new_file(fake_gen_dir, tmp_path):
    from tools.image.codex_image_gen import CodexImageGen
    tool = CodexImageGen()
    before = tool.run()  # before_path is None
    # Simulate codex producing a new PNG
    session = fake_gen_dir / "uuid-1234"
    session.mkdir()
    new_png = session / "ig_abcd.png"
    new_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"fake-png-bytes")
    out = tmp_path / "out" / "storyboard.png"
    result = tool.capture_new_png(before, out, timeout_seconds=2)
    assert result == out
    assert out.read_bytes() == new_png.read_bytes()


def test_capture_new_png_times_out_when_no_new_file(fake_gen_dir, tmp_path):
    from tools.image.codex_image_gen import CodexImageGen
    tool = CodexImageGen()
    # Pre-existing PNG that becomes the BEFORE state
    session = fake_gen_dir / "uuid-old"
    session.mkdir()
    old_png = session / "ig_old.png"
    old_png.write_bytes(b"old")
    before = tool.run()
    assert before["before_path"] == old_png
    # No new PNG appears
    out = tmp_path / "out" / "storyboard.png"
    with pytest.raises(RuntimeError, match="no new file"):
        tool.capture_new_png(before, out, timeout_seconds=1)


def test_tool_auto_registers():
    from tools.tool_registry import registry
    from tools.image.codex_image_gen import CodexImageGen
    # Just importing the module should have registered it.
    image_tools = registry.tools_by_capability("image_generation")
    codex_tools = [t for t in image_tools if isinstance(t, CodexImageGen)]
    assert len(codex_tools) >= 1, "CodexImageGen did not auto-register on import"
