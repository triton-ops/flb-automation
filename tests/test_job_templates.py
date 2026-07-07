"""Validate the canonical job templates (test-data/job-templates/*.json) that recipe R4c builds
every FLB/FSB job from. A corrupted or drifted template silently breaks every generated runbook,
so this is checked directly rather than only exercised indirectly through execution.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _REPO_ROOT / "test-data" / "job-templates"
_TEMPLATES = sorted(_TEMPLATES_DIR.glob("*.json"))

_REQUIRED_TOP_LEVEL_KEYS = {"name", "hvType", "type", "schedules", "options", "objects"}
_REQUIRED_OBJECT_KEYS = {"sourceVid", "targetStorageVid", "mappings", "targetName"}


def test_at_least_one_job_template_exists():
    assert _TEMPLATES, f"expected canonical job templates under {_TEMPLATES_DIR}"


@pytest.mark.parametrize("path", _TEMPLATES, ids=lambda p: p.stem)
def test_template_is_valid_json_with_required_shape(path):
    doc = json.loads(path.read_text(encoding="utf-8"))

    missing = _REQUIRED_TOP_LEVEL_KEYS - doc.keys()
    assert not missing, f"{path.name}: missing top-level keys {missing}"

    assert doc["id"] is None, f"{path.name}: template must have id=null (saveJob creates, never edits)"
    assert doc["type"] in {"FILE_LEVEL", "BACKUP"}, f"{path.name}: unexpected job type {doc['type']!r}"

    objects = doc["objects"]
    assert isinstance(objects, list) and len(objects) == 1, f"{path.name}: expected exactly one object"
    obj = objects[0]
    missing_obj = _REQUIRED_OBJECT_KEYS - obj.keys()
    assert not missing_obj, f"{path.name}: objects[0] missing keys {missing_obj}"
    assert obj["mappings"] == [], f"{path.name}: template's default mappings must be empty (patched at build time)"


@pytest.mark.parametrize("path", _TEMPLATES, ids=lambda p: p.stem)
def test_template_documents_its_substitution_contract(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc.get("_SUBSTITUTION"), f"{path.name}: missing _SUBSTITUTION documentation block"

    # the four fields recipe R4c is told to patch must actually still be placeholders in the
    # shipped template — if one were accidentally filled in with a real live-appliance value,
    # every runbook built from this template would silently target the wrong thing.
    obj = doc["objects"][0]
    for field, value in (
        ("name", doc["name"]),
        ("objects[0].sourceVid", obj["sourceVid"]),
        ("objects[0].targetName", obj["targetName"]),
        ("objects[0].targetStorageVid", obj["targetStorageVid"]),
    ):
        assert isinstance(value, str) and value.startswith("__") and value.endswith("__"), (
            f"{path.name}: {field} = {value!r} is not a placeholder — "
            "template must ship with generic substitution tokens, never a real value"
        )
