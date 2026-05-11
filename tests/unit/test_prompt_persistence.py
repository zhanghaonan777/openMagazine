"""Tests for prompt_persistence."""
import json

import pytest

from lib.prompt_persistence import save_prompt, save_manifest


def test_save_storyboard_prompt(tmp_path):
    path = save_prompt(tmp_path, kind="storyboard",
                       prompt_text="hello storyboard")
    assert path == tmp_path / "prompts" / "storyboard.prompt.txt"
    assert path.read_text(encoding="utf-8") == "hello storyboard"


def test_save_upscale_prompt_with_dotted_slot_id(tmp_path):
    """slot_id like 'spread-03.feature_hero' lands at spread-03/feature_hero.prompt.txt."""
    path = save_prompt(tmp_path, kind="upscale",
                       prompt_text="hello hero",
                       slot_id="spread-03.feature_hero")
    assert path == tmp_path / "prompts" / "spread-03" / "feature_hero.prompt.txt"
    assert path.read_text(encoding="utf-8") == "hello hero"


def test_save_upscale_prompt_with_nested_slot_id(tmp_path):
    """slot_id like 'spread-07.portrait_wall.4' splits on FIRST dot only."""
    path = save_prompt(tmp_path, kind="upscale",
                       prompt_text="hello portrait",
                       slot_id="spread-07.portrait_wall.4")
    # First-dot split → spread-07 / portrait_wall.4.prompt.txt
    assert path == tmp_path / "prompts" / "spread-07" / "portrait_wall.4.prompt.txt"


def test_save_upscale_prompt_flat_slot_id(tmp_path):
    """slot_id without a dot lands directly under prompts/."""
    path = save_prompt(tmp_path, kind="upscale",
                       prompt_text="hi", slot_id="single")
    assert path == tmp_path / "prompts" / "single.prompt.txt"


def test_save_upscale_requires_slot_id(tmp_path):
    with pytest.raises(ValueError, match="slot_id"):
        save_prompt(tmp_path, kind="upscale", prompt_text="x")


def test_unknown_kind_raises(tmp_path):
    with pytest.raises(ValueError, match="kind"):
        save_prompt(tmp_path, kind="banana", prompt_text="x")


def test_save_manifest_writes_valid_json(tmp_path):
    path = save_manifest(
        tmp_path,
        spec_slug="test-01",
        pipeline="editorial-16page",
        templates_used={
            "storyboard": "library/templates/storyboard_v2.prompt.md",
            "upscale_portrait": "library/templates/upscale_portrait.prompt.md",
        },
    )
    assert path == tmp_path / "prompts" / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["spec_slug"] == "test-01"
    assert data["pipeline"] == "editorial-16page"
    assert "git_commit" in data
    assert "git_dirty" in data
    assert "timestamp" in data
    assert data["templates_used"]["storyboard"].endswith("storyboard_v2.prompt.md")


def test_save_manifest_handles_missing_templates(tmp_path):
    path = save_manifest(tmp_path, spec_slug="s", pipeline="p")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["templates_used"] == {}


def test_save_prompt_creates_parent_dirs(tmp_path):
    """Even a deeply nested issue_dir should auto-create prompts/spread-NN/."""
    issue = tmp_path / "deep" / "nested" / "issue"
    issue.mkdir(parents=True)
    save_prompt(issue, kind="upscale", prompt_text="x",
                slot_id="spread-01.cover_hero")
    assert (issue / "prompts" / "spread-01" / "cover_hero.prompt.txt").is_file()


def test_save_prompt_utf8(tmp_path):
    """Chinese / non-ASCII content must round-trip cleanly."""
    text = "你好,这是一个测试 prompt 包含中文 ✨"
    path = save_prompt(tmp_path, kind="storyboard", prompt_text=text)
    assert path.read_text(encoding="utf-8") == text
