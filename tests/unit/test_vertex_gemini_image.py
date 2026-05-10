"""Tests for VertexGeminiImage — verify multi-ref passthrough."""
from pathlib import Path

import pytest
from tools.image.vertex_gemini_image import VertexGeminiImage


def test_run_requires_refs(tmp_path):
    tool = VertexGeminiImage()
    with pytest.raises(ValueError, match="at least one reference"):
        tool.run("p", tmp_path / "out.png", refs=[], aspect="2:3", size="4K")


def test_should_skip_existing_large_file(tmp_path):
    tool = VertexGeminiImage()
    f = tmp_path / "page-01.png"
    f.write_bytes(b"X" * (6 * 1024 * 1024))   # 6 MB — passes 5 MB threshold
    assert tool._should_skip(f, skip_existing=True) is True


def test_should_not_skip_small_file(tmp_path):
    tool = VertexGeminiImage()
    f = tmp_path / "page-01.png"
    f.write_bytes(b"X" * 1024)   # 1 KB — fails 5 MB threshold
    assert tool._should_skip(f, skip_existing=True) is False


def test_should_not_skip_when_flag_off(tmp_path):
    tool = VertexGeminiImage()
    f = tmp_path / "page-01.png"
    f.write_bytes(b"X" * (6 * 1024 * 1024))
    assert tool._should_skip(f, skip_existing=False) is False
