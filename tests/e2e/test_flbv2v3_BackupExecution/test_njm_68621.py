r"""NJM-68621 — [FLB v1] FLB - Functional - Verify Job Behavior After Manually Deleting Recovery
Points.

⚠ REAL PRODUCT-BEHAVIOR FINDING, confirmed live 2026-07-20 (delegated to nbr-ui-pom-builder,
2 independent investigation rounds): the Jira TC's own step 3 ("Manually delete all recovery
points from the repository" while the job itself remains) is **not achievable via the Director UI
on this NBR build, through any available path**:

1. The backup detail page's own '...' -> Delete action operates on the WHOLE backup object, not
   on whichever recovery points are checked in the grid — selecting 1-of-2 or 2-of-2 produced the
   IDENTICAL result: 'Cannot delete the backup. This backup is used by the following item(s):
   <job name>'. NBR blocks deletion outright while any job still references the backup.
2. The only other delete surface, the repository-level 'Delete backups in bulk' dialog (Settings
   -> Repositories -> <repo> -> '...'), was confirmed to have NO per-backup/per-job picker at
   all — only global age/criteria radios ('All backups not belonging to any job', 'All recovery
   points older than N days', etc.) that would act across the WHOLE repository's matching
   backups. Using it to isolate just one job's backup is not possible, and doing so anyway would
   violate this project's safety fence (never touch another job's data) — so it was deliberately
   NOT used to force a deletion.

This means the TC's own premise (delete all RPs, keep the job, rerun it against zero prior
recovery points) cannot be set up at all while respecting the safety fence — not an automation
gap, a genuine product-UI limitation. Per CLAUDE.md Golden Rule 7 ("if a step's precondition
fails, stop and report BLOCKED rather than pushing ahead"), this TC is BLOCKED at step 3's
precondition. `test_setup_multiple_recovery_points` below still demonstrates steps 1-2 (build a
job, produce multiple real recovery points) since those work fine and are useful regression
coverage on their own; `test_deleting_recovery_points_while_job_active_is_blocked` documents the
actual, repeatable blocked behavior found for step 3 as a real (negative) assertion — if NBR ever
changes this, the test will notice — then cleans up the job, since steps 4-6 (rerun against zero
prior recovery points) can never be reached from here.

New POM added for this investigation (`browser/pom/common/repository_management_page.py`):
`open_backup_by_job()` (job-scoped backup opener — `open_backup()` alone is ambiguous whenever a
repo has multiple jobs sharing the same source machine display name, e.g. Onboard repository's
~7 'Window11'-named backups), `recovery_point_count()`, `delete_all_recovery_points()`. See each
method's own docstring for the full live-calibration writeup. Reusable diagnostic:
`browser/checks/check_delete_all_recovery_points.py`.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.repository_management_page import RepositoryManagementPage

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-68621")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-68621_rerun-after-rp-delete"
DRILL_TO_PARENT = ["Local Disk (C:)", "TestData_ForFLB", "ChangeTest_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "TestData_ForFLB", "ChangeTest_ForFLB", "rp_delete_test"]
BASELINE_FILES = {"keep.txt", "remove_me.txt"}
REPOSITORY = "Onboard repository"


@allure.title("NJM-68621 step 1-2 — build the job and produce 2 recovery points")
def test_setup_multiple_recovery_points(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["rp_delete_test"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"1st run did not succeed: {status}"

    status2 = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status2 == "Successful", f"2nd run did not succeed: {status2}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == BASELINE_FILES, f"expected the 2 seeded baseline files, got {names}"


@allure.title("NJM-68621 step 3 — deleting a job's recovery points while it's still active is "
               "blocked by NBR itself (documented product-UI limitation, not an automation gap)")
def test_deleting_recovery_points_while_job_active_is_blocked(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    repo = RepositoryManagementPage(page)
    repo.open().open_repository(REPOSITORY)

    before = repo.recovery_point_count(JOB_NAME)
    assert before == 2, f"expected the 2 recovery points from step 1-2, got {before}"

    repo.go_back()  # backup detail -> repo detail's Backups grid, required before re-navigating
    repo.delete_all_recovery_points(JOB_NAME)

    repo.go_back()  # same requirement before the final recovery_point_count() re-navigation
    after = repo.recovery_point_count(JOB_NAME)
    assert after == before, (
        f"expected NBR to BLOCK deletion while the job still exists (count unchanged at "
        f"{before}), but the count changed to {after} — either the product now allows this "
        f"(re-scope this TC to actually exercise steps 4-6) or this test's own assumption is stale"
    )

    # REQUIRED (Golden Rule 8): flb_job_cleanup's teardown calls JobManagementPage.delete_job(),
    # which needs the Data Protection dashboard's Jobs sidebar on-screen — this test ends on a
    # Settings -> Repositories drilldown page instead, where the sidebar doesn't exist at all,
    # silently breaking cleanup (wrapped in try/except) exactly like the FLR-wizard-reopen bug.
    DataProtectionPage(page).open()
    flb_job_cleanup(JOB_NAME)
