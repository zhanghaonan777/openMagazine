"""Contract test: every sample slide_manifest in examples/ validates against
schemas/artifacts/slide_manifest.schema.json. Guards against schema drift as
new realizer targets or region shapes are added.
"""
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator


SKILL_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = SKILL_ROOT / "schemas" / "artifacts" / "slide_manifest.schema.json"
EXAMPLES_GLOB = "examples/**/slide_manifest*.json"


def _all_sample_manifests():
    return sorted(SKILL_ROOT.glob(EXAMPLES_GLOB))


def test_schema_is_valid_draft7():
    schema = json.loads(SCHEMA_PATH.read_text())
    Draft7Validator.check_schema(schema)


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


@pytest.mark.parametrize(
    "manifest_path",
    _all_sample_manifests(),
    ids=lambda p: str(p.relative_to(SKILL_ROOT)),
)
def test_sample_manifest_validates(manifest_path, schema):
    """Every checked-in slide_manifest sample must validate against schema."""
    data = json.loads(manifest_path.read_text())
    errors = list(Draft7Validator(schema).iter_errors(data))
    assert errors == [], (
        f"{manifest_path.relative_to(SKILL_ROOT)} has {len(errors)} error(s):\n"
        + "\n".join(f"  {list(e.absolute_path)}: {e.message}" for e in errors)
    )


def test_at_least_one_sample_exists():
    """Catches regressions where examples/ is emptied or globbed wrong."""
    assert _all_sample_manifests(), (
        f"no slide_manifest samples found under {SKILL_ROOT}/examples/"
    )
