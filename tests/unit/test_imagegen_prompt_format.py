"""Tests that recorded imagegen prompt files conform to the schema."""
import json
import pathlib
import re

import jsonschema
import pytest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _extract_json_block(prompt_text: str) -> dict | None:
    match = re.search(r"```json\n(.*?)\n```", prompt_text, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(1))


def test_imagegen_prompt_files_validate_against_schema():
    """If any *.prompt.txt files exist with JSON blocks, they must
    validate against schemas/imagegen_prompt.schema.json."""
    schema_path = SKILL_ROOT / "schemas/imagegen_prompt.schema.json"
    if not schema_path.is_file():
        pytest.skip("schema not present")
    schema = json.loads(schema_path.read_text())

    # Walk all known prompt files
    candidates = []
    for output_dir in (SKILL_ROOT / "output").glob("*") if (SKILL_ROOT / "output").exists() else []:
        candidates.extend((output_dir / "prompts").rglob("*.prompt.txt") if (output_dir / "prompts").exists() else [])

    if not candidates:
        pytest.skip("no prompt files on disk yet")

    for prompt_file in candidates:
        text = prompt_file.read_text(encoding="utf-8")
        spec = _extract_json_block(text)
        if spec is None:
            continue  # legacy prose-only format
        jsonschema.validate(instance=spec, schema=schema)
