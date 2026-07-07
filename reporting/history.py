"""HistoryManager — preserves Allure history/trends across report generations.

Allure convention: copy the previous report's history/ into the new results dir before
generating. Per-run journals under results/runs/ are additionally kept forever, so history
can always be rebuilt.
"""
from __future__ import annotations

import shutil
from pathlib import Path


def carry_history(allure_report_dir: Path, allure_results_dir: Path) -> bool:
    src = allure_report_dir / "history"
    if not src.is_dir():
        return False
    dst = allure_results_dir / "history"
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.is_file():
            shutil.copyfile(f, dst / f.name)
    return True
