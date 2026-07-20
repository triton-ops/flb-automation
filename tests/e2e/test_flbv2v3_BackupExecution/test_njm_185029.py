r"""NJM-185029 — [FLB v3] FLB - Functional - Incremental backup with and without changed source
data (incl. 0-delta recovery point).

Per the TC's own Xray steps (re-checked live against Jira 2026-07-20 to fix a real sequencing
mismatch an earlier version of this file had):
  1. Create an FLB job over a folder of known content, run the INITIAL FULL backup. Expected:
     initial full recovery point created; contents match source.
  2. Add + modify source files, run an INCREMENTAL backup. Expected: incremental completes; the
     new recovery point captures the current source state (this suite's own scope note: "captures
     only the new/changed data" in the TC's own wording is about incremental STORAGE efficiency,
     not what FLR-browse exposes — FLR always shows the full consistent state of a recovery point,
     never a delta view — so this is verified as "recovered data matches CURRENT source", per the
     TC's own literal expected-result text for this step).
  3. WITHOUT further source changes, run ANOTHER incremental (0-delta). Expected: completes
     successfully with no/near-zero new data; job does not fail.
  4. Recover from the LATEST recovery point (the 0-delta one from step 3). Expected: the full
     current file set (baseline + changes) is recovered correctly — i.e. the 0-delta run didn't
     corrupt or drop anything. Verified two ways: a filename-set check (structural), AND a real
     SHA-256 checksum comparison of both changed files (modify_me.txt, added_after_baseline.txt)
     against test-data/manifests/manifest-changetest-forflb.sha256 — computed from the actual
     bytes on win11 via Get-FileHash right after the step-2 WinRM change (ground truth, not
     guessed from the string passed to Set-Content, to avoid any encoding/newline mismatch).

TWO-PHASE COMBINATION TEST (per explicit instruction): pytest code cannot drive live WinRM
mid-test — only the agent driving the session can — so genuinely changing source content between
runs happens BETWEEN two separate pytest invocations of this file's two test functions, not
within one self-contained `pytest` run. Procedure:

  1. `pytest test_njm_185029.py::test_baseline` — builds the job against the dedicated
     `ChangeTest_ForFLB/incremental_with_changes` fixture (seeded 2026-07-20: keep.txt/
     modify_me.txt/delete_me.txt, isolated from every shared fixture so these mutations never
     collide with other suites/tests) and runs the initial full backup (TC step 1). Deliberately
     does NOT register `flb_job_cleanup` — the job must survive into phase 2.
  2. The agent runs a WinRM step to add a new file (`added_after_baseline.txt`) and modify
     `modify_me.txt`'s content under the SAME fixture folder.
  3. `pytest test_njm_185029.py::test_incremental_then_zero_delta` — runs the incremental that
     captures the real change (TC step 2), verifies it, THEN immediately runs a second, genuinely
     UNMODIFIED incremental (TC step 3, the 0-delta case — no agent action needed between these
     two since nothing should change), and verifies the latest recovery point still reflects the
     full current state (TC step 4). Registers `flb_job_cleanup` here, so the job is cleaned up
     only once every phase has completed.

⚠ If phase 2 is never run (e.g. this file is abandoned mid-procedure), the job LEAKS — no
automatic teardown runs after phase 1 alone. Run `browser/checks/cleanup_auto_flb_jobs.py`
(dry-run) to check before moving on if both phases weren't completed in the same session.

⚠ REAL BUG FOUND+FIXED LIVE 2026-07-20 (canonical writeup — every phase-2 test in this suite's
combination-test family carries the same fix): phase 2 must NOT participate in this project's
global pytest-rerunfailures setting (--reruns=1, pyproject.toml). flb_job_cleanup(JOB_NAME) only
REGISTERS the name — the actual jm.delete_job() call happens at fixture TEARDOWN, which fires
after ANY attempt ends, pass or fail (by the fixture's own design, so failed tests don't leak
jobs). If attempt #1 hits a transient failure (e.g. a locator timeout from appliance load right
after a fresh browser/login), its teardown still deletes the job — then pytest's automatic rerun
(attempt #2) runs against a job that's now genuinely gone, failing again with what LOOKS like the
identical error. This is exactly what happened during live debugging: a controlled, minimal-gap
repro confirmed the job existed immediately before AND immediately after the WinRM step, but was
gone immediately after a `1 failed, 1 rerun` phase-2 attempt — proving the disappearance was
caused by attempt #1's own teardown, not appliance housekeeping, not the full_backup_mode/'Job
runs #' setting (an isolated probe job using that exact setting survived 20+ minutes fine), and
not elapsed time. @pytest.mark.flaky(reruns=0) on every phase-2 test overrides the global setting
— a rerun can never legitimately help once the first attempt's own cleanup has already destroyed
the shared state it depends on.

⚠ SECOND REAL FINDING, live 2026-07-20: a run that just reached 'Successful' can still show only
its PREVIOUS recovery point in the FLR picker for 90+ seconds afterward — a documented
appliance-side indexing lag (see FileLevelRecoveryPage.wait_for_recovery_point_count()'s own
docstring, originally found for NJM-70312). Without waiting for the new point to actually appear,
flr_browse() silently browses the STALE recovery point instead of the new one, making a genuine
content change look like it was never captured. Both content checks below wait for the expected
recovery-point count first.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-185029")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-185029_incremental"
DRILL_TO_PARENT = ["Local Disk (C:)", "TestData_ForFLB", "ChangeTest_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "TestData_ForFLB", "ChangeTest_ForFLB", "incremental_with_changes"]
BASELINE_FILES = {"keep.txt", "modify_me.txt", "delete_me.txt"}
AFTER_CHANGE_FILES = BASELINE_FILES | {"added_after_baseline.txt"}


@allure.title("NJM-185029 phase 1/2 — initial full backup (TC step 1)")
def test_baseline(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["incremental_with_changes"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"initial full backup did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == BASELINE_FILES, f"expected the 3 seeded baseline files, got {names}"


@allure.title("NJM-185029 phase 2/2 — incremental with real changes (step 2), then a 0-delta incremental (step 3/4)")
@pytest.mark.flaky(reruns=0)
def test_incremental_then_zero_delta(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    # CHANGED 2026-07-20 (user-directed): flb_job_cleanup(JOB_NAME) now registers at the END,
    # only once every phase/assertion below has actually passed — see test_njm_128609.py's
    # comment for the reasoning (a mid-test failure must never risk deleting the job via its own
    # teardown before it can be inspected/retried).

    # TC step 2: incremental capturing the real WinRM-driven change.
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"post-change incremental run did not succeed: {status}"

    FileLevelRecoveryPage(page).wait_for_recovery_point_count(JOB_NAME, min_count=2)
    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == AFTER_CHANGE_FILES, (
        f"expected the new file added_after_baseline.txt to appear after a real source change, got {names}"
    )

    # TC step 3: a further incremental with NO source changes (0-delta) — must still succeed.
    zero_delta_status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert zero_delta_status == "Successful", f"0-delta incremental did not succeed: {zero_delta_status}"

    # TC step 4: recover from the LATEST recovery point (the 0-delta one) — full current state.
    FileLevelRecoveryPage(page).wait_for_recovery_point_count(JOB_NAME, min_count=3)
    zero_delta_names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert zero_delta_names == AFTER_CHANGE_FILES, (
        f"expected the 0-delta run's recovery point to still reflect the full current state, got {zero_delta_names}"
    )

    # Real content-integrity check (not just filenames): both the file modified in step 2 and the
    # file added in step 2 must byte-match their real source content, via the actual FLR
    # Download-and-hash mechanism this project uses everywhere else for FLR verification.
    verify_checksum(
        page, JOB_NAME, FLR_DRILL_TO_FOLDER, "modify_me.txt", "manifest-changetest-forflb.sha256",
    )
    verify_checksum(
        page, JOB_NAME, FLR_DRILL_TO_FOLDER, "added_after_baseline.txt", "manifest-changetest-forflb.sha256",
    )

    flb_job_cleanup(JOB_NAME)
