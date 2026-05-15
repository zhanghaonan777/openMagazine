"""Contract tests — each pipeline manifest validates against the schema, and
each declared stage's `produces` artifact has a corresponding schema file."""
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator


SKILL_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def pipeline_schema():
    schema_path = SKILL_ROOT / "schemas" / "pipelines" / "pipeline.schema.json"
    return json.loads(schema_path.read_text())


def _all_pipelines():
    return list((SKILL_ROOT / "pipeline_defs").glob("*.yaml"))


@pytest.mark.parametrize("pipeline_path", _all_pipelines(), ids=lambda p: p.name)
def test_pipeline_manifest_valid(pipeline_path, pipeline_schema):
    """Each pipeline_defs/*.yaml must validate against pipeline.schema.json."""
    data = yaml.safe_load(pipeline_path.read_text())
    Draft7Validator(pipeline_schema).validate(data)


@pytest.mark.parametrize("pipeline_path", _all_pipelines(), ids=lambda p: p.name)
def test_each_stage_produces_existing_schema(pipeline_path):
    """Every stage.produces artifact name should have a schema file."""
    data = yaml.safe_load(pipeline_path.read_text())
    artifacts_dir = SKILL_ROOT / "schemas" / "artifacts"
    for stage in data["stages"]:
        produces = stage["produces"]
        if isinstance(produces, str):
            produces = [produces]
        for artifact in produces:
            # Strip directory components, e.g., "cells/cell-NN.png" → not a JSON artifact
            if not artifact.endswith(".json"):
                continue
            name = artifact.replace(".json", "")
            schema_path = artifacts_dir / f"{name}.schema.json"
            assert schema_path.is_file(), f"no schema for artifact {artifact} (in {pipeline_path.name})"
