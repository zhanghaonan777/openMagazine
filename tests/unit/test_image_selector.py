"""Tests for ImageSelector — routing by mode."""
from pathlib import Path

import pytest
from tools.image.image_selector import ImageSelector


def test_storyboard_mode_routes_to_codex(monkeypatch):
    sel = ImageSelector()
    backend = sel.choose_backend(mode="storyboard")
    assert backend.provider == "codex"


def test_upscale_4k_routes_to_vertex(monkeypatch):
    sel = ImageSelector()
    backend = sel.choose_backend(mode="upscale_4k")
    assert backend.provider == "vertex"


def test_unknown_mode_raises():
    sel = ImageSelector()
    with pytest.raises(ValueError, match="mode"):
        sel.choose_backend(mode="weird-unknown-mode")
