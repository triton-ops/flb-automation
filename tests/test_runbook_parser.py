"""Regression test: every REAL, committed runbook under cases/ must parse cleanly.

This exercises reporting.runbook_parser against the actual artifacts in the repo (not just
synthetic fixtures) — if a future runbook edit breaks the metadata block format, this fails.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from reporting.runbook_parser import RunbookMeta, parse_runbook

_VALID_ALLURE_SEVERITIES = {"blocker", "critical", "normal", "minor", "trivial"}
_REPO_ROOT = Path(__file__).resolve().parent.parent
_RUNBOOKS = sorted(
    p for p in _REPO_ROOT.joinpath("cases").rglob("*.md") if p.name != "TEMPLATE.md"
)


def test_at_least_one_runbook_exists():
    assert _RUNBOOKS, "expected generated runbooks under cases/**/*.md"


@pytest.mark.parametrize("path", _RUNBOOKS, ids=lambda p: p.stem)
def test_every_committed_runbook_parses_cleanly(path):
    meta = parse_runbook(path)
    assert isinstance(meta, RunbookMeta)
    assert meta.test_id != "UNKNOWN", f"{path}: could not extract a test_id"
    assert meta.test_id == path.stem, f"{path}: test_id {meta.test_id!r} != filename {path.stem!r}"
    assert meta.owner, f"{path}: no owner/author extracted"
    assert meta.severity in _VALID_ALLURE_SEVERITIES, f"{path}: severity {meta.severity!r} invalid"
    assert meta.suite, f"{path}: no suite (parent dir name) resolved"
