"""Tests for tools.validation.verify_4k."""
from PIL import Image

from tools.validation.verify_4k import _classify_aspect, verify


def test_classifies_editorial_aspects():
    assert _classify_aspect(3000, 4000) == "3:4 portrait"
    assert _classify_aspect(3200, 2000) == "16:10 landscape"


def test_verify_finds_nested_editorial_images(tmp_path):
    issue_dir = tmp_path / "issue"
    spread = issue_dir / "images" / "spread-01"
    spread.mkdir(parents=True)
    # Save with little compression so the file clears verify_4k's 5 MB floor.
    Image.new("RGB", (3000, 4000), color=(128, 128, 128)).save(
        spread / "cover_hero.png",
        compress_level=0,
    )

    assert verify(issue_dir) == 0
