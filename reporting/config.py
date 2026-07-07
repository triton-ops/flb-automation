"""ReportConfig — dependency-injected paths with self-healing discovery.

Nothing here is hard-coded to an absolute location: the repo root is discovered by walking up
from this file until the framework markers (CLAUDE.md + cases/) are found, and every directory
derives from it. Components take a ReportConfig instance (constructor injection) — no globals.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Walk upward until the framework root markers are found (self-healing, no hard-coded path)."""
    p = (start or Path(__file__).resolve().parent).resolve()
    for cand in (p, *p.parents):
        if (cand / "CLAUDE.md").exists() and (cand / "cases").is_dir():
            return cand
    # graceful fallback: parent of this package
    return Path(__file__).resolve().parent.parent


@dataclass
class ReportConfig:
    repo_root: Path = field(default_factory=find_repo_root)

    @property
    def results_dir(self) -> Path:
        return self.repo_root / "results"

    @property
    def runs_dir(self) -> Path:
        """Per-run journals + raw artifacts. Never overwritten -> history preserved."""
        return self.results_dir / "runs"

    @property
    def allure_results_dir(self) -> Path:
        return self.results_dir / "allure-results"

    @property
    def allure_report_dir(self) -> Path:
        return self.results_dir / "allure-report"

    @property
    def cases_dir(self) -> Path:
        return self.repo_root / "cases"

    def latest_run_dir(self) -> Path | None:
        if not self.runs_dir.is_dir():
            return None
        runs = sorted(d for d in self.runs_dir.iterdir() if (d / "journal.jsonl").exists())
        return runs[-1] if runs else None
