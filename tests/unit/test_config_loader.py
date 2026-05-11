"""Tests for lib.config_loader."""
import os
import pytest

from lib.config_loader import load_config, get_parallelism


def test_load_config_returns_dict():
    cfg = load_config()
    assert isinstance(cfg, dict)
    # config.yaml ships with defaults.parallelism = 3
    assert cfg.get("defaults", {}).get("parallelism") == 3


def test_get_parallelism_default_from_config():
    # No env override → reads config.yaml's 3
    for k in ("OPENMAGAZINE_PARALLELISM", "OPEN_ZAZHI_PARALLELISM"):
        os.environ.pop(k, None)
    assert get_parallelism() == 3


def test_get_parallelism_env_override(monkeypatch):
    monkeypatch.setenv("OPENMAGAZINE_PARALLELISM", "5")
    assert get_parallelism() == 3


def test_get_parallelism_legacy_env(monkeypatch):
    monkeypatch.delenv("OPENMAGAZINE_PARALLELISM", raising=False)
    monkeypatch.setenv("OPEN_ZAZHI_PARALLELISM", "2")
    assert get_parallelism() == 2


def test_get_parallelism_clamps_to_min_1(monkeypatch):
    monkeypatch.setenv("OPENMAGAZINE_PARALLELISM", "0")
    assert get_parallelism() == 1


def test_get_parallelism_handles_garbage_env(monkeypatch):
    monkeypatch.setenv("OPENMAGAZINE_PARALLELISM", "abc")
    # Falls through to config.yaml's value
    assert get_parallelism() == 3
