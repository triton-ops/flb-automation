"""Shared pytest fixtures for the flb-automation test suite."""
from __future__ import annotations

from pathlib import Path

import pytest

from reporting.config import ReportConfig


@pytest.fixture
def repo_root() -> Path:
    """The real repo root (three levels up from this file) — used to validate real, committed
    artifacts (cases/, test-data/job-templates/), never to write into them."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def tmp_cfg(tmp_path: Path) -> ReportConfig:
    """A ReportConfig rooted in a throwaway tmp_path — isolates every reporting-pipeline test
    from the real results/ tree (no pollution of results/runs/, no reliance on it either)."""
    return ReportConfig(repo_root=tmp_path)
