r"""NJM-128609 — [FLB v3] FLB - Functional (Retention) - Verify Active Full Creation (With Source
Changes).

TWO-PHASE COMBINATION TEST — see test_njm_185029.py's module docstring for the full procedure
rationale (pytest can't drive live WinRM mid-test; the agent runs that step BETWEEN the two
pytest invocations below). Uses the dedicated `ChangeTest_ForFLB/active_with_changes` fixture
folder (seeded 2026-07-20, isolated from every shared fixture and from this suite's other
combination tests) and `full_backup_mode='Active full'` + 'Job runs #'/every_job_runs=1 (see
_helpers.py's build_flb_job() docstring — makes every run a full backup without needing a real
recurring schedule).

⚠ Same scope note as test_retention_full_backup_mode.py: the Options-step calibration found no
UI marker distinguishing an Active-full recovery point from a Synthetic-full one, so this test
verifies the setting is accepted and recovered content correctly reflects the real source change
— not which specific full-backup mechanism executed internally.

Procedure:
  1. `pytest test_njm_128609.py::test_baseline` — builds+runs once. No flb_job_cleanup call — the
     job must survive into phase 2.
  2. Agent runs WinRM to add `added_after_baseline.txt` and modify `modify_me.txt` under
     `active_with_changes`.
  3. `pytest test_njm_128609.py::test_after_source_changes` — reruns the SAME job and asserts the
     new full backup captured the change. Registers flb_job_cleanup.

⚠ If phase 2 is never run, the job LEAKS — check `cleanup_auto_flb_jobs.py` (dry-run) if this
procedure is abandoned mid-way.

⚠ REAL BUG #1 FOUND+FIXED LIVE 2026-07-20: phase 2 must NOT participate in this project's global
pytest-rerunfailures setting (--reruns=1, pyproject.toml). flb_job_cleanup(JOB_NAME) only
REGISTERS the name — the actual jm.delete_job() call happens at fixture TEARDOWN, which fires
after ANY attempt ends, pass or fail (by the fixture's own design, so failed tests don't leak
jobs). If attempt #1 hits a transient failure, its teardown still deletes the job — then pytest's
automatic rerun (attempt #2) runs against a job that's now genuinely gone, failing again with what
LOOKS like the identical error. @pytest.mark.flaky(reruns=0) below overrides the global setting
for this test — a "rerun" can never legitimately help once the first attempt's own cleanup has
already destroyed the shared state it depends on. flb_job_cleanup(JOB_NAME) is also registered
only at the very END of the test now (once every assertion has passed), not at the top — a failed
attempt must never risk deleting phase 1's job before it can be inspected/retried.

⚠ REAL BUG #2 FOUND+FIXED LIVE 2026-07-20 (this is the one that took real live-DOM debugging via
the nbr-ui-pom-builder agent to pin down — see
FileLevelRecoveryPage.wait_for_recovery_point_count()'s own docstring for the full writeup):
that method's poll loop only called click_cancel() BEFORE each reopen, never AFTER the loop once
`min_count` was satisfied — so in the common case (satisfied on the very first reopen), it
returned with the FLR wizard LEFT OPEN. The Jobs sidebar this test's very next action needs to
click doesn't exist in the DOM AT ALL while that wizard is open (the content pane is fully
replaced, not just covered) — confirmed via a live DOM dump, not guessed. Fixed by having
wait_for_recovery_point_count() always close the wizard before returning. Two other real, but
NOT the actual cause of this specific symptom, fixes were made and kept along the way: the
appliance-side recovery-point indexing lag itself (genuine, unrelated — see that method's
CALIBRATED-live-2026-07-16 docstring section) and DataProtectionPage.select_job_row()/
FileLevelRecoveryPage._select_job_and_open_recover_menu() using an unscoped click() (a real,
separate risk of matching a stale hidden ExtJS duplicate row — fixed with BasePage.
click_visible_nth() — that fix is harmless and worth keeping even though it wasn't what caused
this particular failure).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-128609")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-128609_active-full-changes"
DRILL_TO_PARENT = ["Local Disk (C:)", "TestData_ForFLB", "ChangeTest_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "TestData_ForFLB", "ChangeTest_ForFLB", "active_with_changes"]
BASELINE_FILES = {"keep.txt", "modify_me.txt", "delete_me.txt"}
AFTER_CHANGE_FILES = BASELINE_FILES | {"added_after_baseline.txt"}


@allure.title("NJM-128609 phase 1/2 — Active-full baseline run")
def test_baseline(logged_in_page):
    page = logged_in_page
    build_flb_job(
        page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["active_with_changes"],
        full_backup_mode="Active full",
    )
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline run did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == BASELINE_FILES, f"expected the 3 seeded baseline files, got {names}"


@allure.title("NJM-128609 phase 2/2 — Active-full rerun after a real WinRM-driven source change")
@pytest.mark.flaky(reruns=0)
def test_after_source_changes(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    # CHANGED 2026-07-20 (user-directed): flb_job_cleanup(JOB_NAME) now registers at the END,
    # only once every assertion below has actually passed — not at the top of the test. A failed
    # attempt here must never risk deleting the job via its own teardown, since the job is
    # phase 1's, not this test's own, and a failure should leave it in place for inspection/retry
    # rather than for this test's fixture to clean up.
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"post-change run did not succeed: {status}"

    # REAL FINDING live 2026-07-20: a run that just reached 'Successful' can still show only its
    # PREVIOUS recovery point in the FLR picker for 90+ seconds afterward (documented appliance-
    # side indexing lag — see FileLevelRecoveryPage.wait_for_recovery_point_count()'s own
    # docstring, originally found for NJM-70312). Without this wait, flr_browse() below silently
    # browses the STALE (baseline) recovery point instead of the new one, making a genuine change
    # look like it was never captured. Closes+reopens the FLR wizard until 2 points are visible.
    FileLevelRecoveryPage(page).wait_for_recovery_point_count(JOB_NAME, min_count=2)

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == AFTER_CHANGE_FILES, (
        f"expected the new file added_after_baseline.txt in the new Active full, got {names}"
    )

    flb_job_cleanup(JOB_NAME)
