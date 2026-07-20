r"""NJM-128608 — [FLB v3] FLB - Functional (Retention) - Verify Synthetic Full Creation (With
Source Changes).

TWO-PHASE COMBINATION TEST — see test_njm_185029.py's module docstring for the full procedure
rationale. Uses the dedicated `ChangeTest_ForFLB/synthetic_with_changes` fixture folder (seeded
2026-07-20) and `full_backup_mode='Synthetic full'` + 'Job runs #'/every_job_runs=1.

⚠ Same scope note as test_retention_full_backup_mode.py: no UI marker distinguishes a
Synthetic-full recovery point from an Active-full one — this verifies the setting is accepted and
recovered content correctly reflects the real source change, not the internal mechanism.

Procedure:
  1. `pytest test_njm_128608.py::test_baseline` — builds+runs once. No flb_job_cleanup — the job
     must survive into phase 2.
  2. Agent runs WinRM to add `added_after_baseline.txt` and modify `modify_me.txt` under
     `synthetic_with_changes`.
  3. `pytest test_njm_128608.py::test_after_source_changes` — reruns the SAME job and asserts the
     new full backup captured the change. Registers flb_job_cleanup.

⚠ If phase 2 is never run, the job LEAKS — check `cleanup_auto_flb_jobs.py` (dry-run) if this
procedure is abandoned mid-way.

⚠ REAL BUG FOUND+FIXED LIVE 2026-07-20 — see test_njm_185029.py's module docstring for the full
writeup: phase 2 must NOT participate in this project's global pytest-rerunfailures setting, since
a failed attempt #1's own flb_job_cleanup teardown deletes the job (by design, so failed tests
don't leak), leaving nothing for the automatic rerun to work with. @pytest.mark.flaky(reruns=0)
below overrides the global setting for this test.

⚠ SECOND REAL FINDING, live 2026-07-20 — also see test_njm_185029.py's docstring: a run that just
reached 'Successful' can still show only its PREVIOUS recovery point in the FLR picker for 90+
seconds afterward (documented appliance-side indexing lag). Phase 2 waits for the new point to
actually appear before browsing it, or it silently reads stale (baseline) content.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-128608")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-128608_synthetic-full-changes"
DRILL_TO_PARENT = ["Local Disk (C:)", "TestData_ForFLB", "ChangeTest_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "TestData_ForFLB", "ChangeTest_ForFLB", "synthetic_with_changes"]
BASELINE_FILES = {"keep.txt", "modify_me.txt", "delete_me.txt"}
AFTER_CHANGE_FILES = BASELINE_FILES | {"added_after_baseline.txt"}


@allure.title("NJM-128608 phase 1/2 — Synthetic-full baseline run")
def test_baseline(logged_in_page):
    page = logged_in_page
    build_flb_job(
        page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["synthetic_with_changes"],
        full_backup_mode="Synthetic full",
    )
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline run did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == BASELINE_FILES, f"expected the 3 seeded baseline files, got {names}"


@allure.title("NJM-128608 phase 2/2 — Synthetic-full rerun after a real WinRM-driven source change")
@pytest.mark.flaky(reruns=0)
def test_after_source_changes(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    # CHANGED 2026-07-20 (user-directed): flb_job_cleanup(JOB_NAME) now registers at the END,
    # only once every assertion below has actually passed — see test_njm_128609.py's comment.
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"post-change run did not succeed: {status}"

    FileLevelRecoveryPage(page).wait_for_recovery_point_count(JOB_NAME, min_count=2)
    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == AFTER_CHANGE_FILES, (
        f"expected the new file added_after_baseline.txt in the new Synthetic full, got {names}"
    )

    flb_job_cleanup(JOB_NAME)
