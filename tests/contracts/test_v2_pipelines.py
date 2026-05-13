"""Contract tests for v2 (editorial) pipelines.

Auto-discovers every `pipeline_defs/*.yaml` with `schema_version: 2` and:
  1. validates it against `schemas/pipelines/pipeline.schema.json`,
  2. checks article ↔ layout consistency for the bundled example article,
  3. asserts the editorial-16page layout's image_slot count matches the
     21-slot budget the directors and pipeline manifest assume.
"""
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import validate

from tools.validation.article_validate import validate_article
from tools.validation.regions_validate import validate_regions


SKILL_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def pipeline_schema():
    return json.loads(
        (SKILL_ROOT / "schemas/pipelines/pipeline.schema.json").read_text()
    )


def _v2_pipelines() -> list[Path]:
    return [
        p for p in (SKILL_ROOT / "pipeline_defs").glob("*.yaml")
        if yaml.safe_load(p.read_text()).get("schema_version") == 2
    ]


@pytest.mark.parametrize(
    "pipeline_path", _v2_pipelines(), ids=lambda p: p.name
)
def test_v2_pipeline_validates(pipeline_path, pipeline_schema):
    data = yaml.safe_load(pipeline_path.read_text())
    validate(instance=data, schema=pipeline_schema)


def test_editorial_16page_layout_article_consistency():
    layout_path = SKILL_ROOT / "library/layouts/editorial-16page.yaml"
    article_path = SKILL_ROOT / "library/articles/cosmos-luna-may-2026.yaml"
    errors = validate_article(article_path, layout_path)
    assert errors == [], f"unexpected errors: {errors}"


def test_editorial_16page_image_slots_count():
    layout = yaml.safe_load(
        (SKILL_ROOT / "library/layouts/editorial-16page.yaml").read_text()
    )
    # image_slots may declare per-entry `count` (e.g. feature_hero count: 3,
    # feature_captioned count: 9, portrait_wall count: 6) — flatten before
    # comparing to the 21-slot budget.
    flat = []
    for s in layout["image_slots"]:
        n = s.get("count", 1)
        for _ in range(n):
            flat.append(s)
    assert len(flat) == 21, (
        f"editorial-16page expects 21 image slots after flattening count=*, "
        f"got {len(flat)}"
    )


def test_editorial_16page_director_files_exist():
    """Every required_skills entry that points to a director must have a
    corresponding markdown file under skills/."""
    pipeline = yaml.safe_load(
        (SKILL_ROOT / "pipeline_defs/editorial-16page.yaml").read_text()
    )
    missing = []
    for skill_ref in pipeline.get("required_skills", []):
        path = SKILL_ROOT / "skills" / f"{skill_ref}.md"
        if not path.is_file():
            missing.append(skill_ref)
    assert missing == [], f"missing director skill files: {missing}"


def _regions_yamls():
    return sorted(
        (SKILL_ROOT / "library" / "layouts" / "_components")
        .glob("*.regions.yaml")
    )


@pytest.mark.parametrize(
    "regions_path", _regions_yamls(), ids=lambda p: p.name
)
def test_regions_yaml_validates(regions_path):
    errors = validate_regions(regions_path)
    assert errors == [], (
        f"{regions_path.name}: {len(errors)} error(s)\n  "
        + "\n  ".join(errors)
    )


from tools.validation.design_system_validate import validate_design_system


def _profile_yamls():
    return sorted((SKILL_ROOT / "library" / "profiles").glob("*.yaml"))


def _design_system_yamls():
    return sorted((SKILL_ROOT / "library" / "design-systems").glob("*.yaml"))


@pytest.mark.parametrize(
    "profile_path", _profile_yamls(), ids=lambda p: p.name
)
def test_profile_yaml_validates(profile_path):
    """Every library/profiles/*.yaml must validate against profile.schema.json."""
    import json
    from jsonschema import validate
    schema = json.loads((SKILL_ROOT / "schemas/profile.schema.json").read_text())
    data = yaml.safe_load(profile_path.read_text())
    validate(instance=data, schema=schema)


@pytest.mark.parametrize(
    "ds_path", _design_system_yamls(), ids=lambda p: p.name
)
def test_design_system_yaml_validates(ds_path):
    """Every library/design-systems/*.yaml must validate."""
    errors = validate_design_system(ds_path)
    assert errors == [], (
        f"{ds_path.name}: {len(errors)} error(s)\n  "
        + "\n  ".join(errors)
    )
