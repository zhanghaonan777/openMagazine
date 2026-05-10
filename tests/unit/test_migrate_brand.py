"""Tests for tools.meta.migrate_brand_v1_to_v2."""
import yaml
import pytest

from tools.meta.migrate_brand_v1_to_v2 import migrate, V1_TO_V2_DEFAULTS


def test_migrate_keeps_v1_fields(tmp_path):
    src = tmp_path / "brand.yaml"
    src.write_text(yaml.safe_dump({
        "schema_version": 1,
        "name": "test-brand",
        "masthead": "TEST MAG",
        "display_name": {"en": "Test Magazine"},
    }))
    out = migrate(src, preset="editorial-classic", dry_run=True)
    assert out["schema_version"] == 2
    assert out["name"] == "test-brand"
    assert out["masthead"] == "TEST MAG"
    assert out["display_name"] == {"en": "Test Magazine"}


def test_migrate_adds_typography(tmp_path):
    src = tmp_path / "brand.yaml"
    src.write_text(yaml.safe_dump({
        "schema_version": 1,
        "name": "x",
        "masthead": "X",
    }))
    out = migrate(src, preset="editorial-classic", dry_run=True)
    assert "typography" in out
    assert out["typography"]["display"]["family"] == "Playfair Display"
    assert out["typography"]["body"]["size_pt"] == 10


def test_migrate_adds_print_specs(tmp_path):
    src = tmp_path / "brand.yaml"
    src.write_text(yaml.safe_dump({"schema_version": 1, "name": "x", "masthead": "X"}))
    out = migrate(src, preset="editorial-classic", dry_run=True)
    assert out["print_specs"]["page_size"] == "A4"
    assert out["print_specs"]["bleed_mm"] == 3


def test_migrate_writes_file(tmp_path):
    src = tmp_path / "brand.yaml"
    src.write_text(yaml.safe_dump({"schema_version": 1, "name": "x", "masthead": "X"}))
    migrate(src, preset="editorial-classic", dry_run=False)
    after = yaml.safe_load(src.read_text())
    assert after["schema_version"] == 2
    assert "typography" in after


def test_migrate_idempotent_on_v2(tmp_path):
    src = tmp_path / "brand.yaml"
    src.write_text(yaml.safe_dump({"schema_version": 2, "name": "x", "typography": {}}))
    with pytest.raises(ValueError, match="already v2"):
        migrate(src, preset="editorial-classic")
