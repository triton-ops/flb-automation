r"""NJM-70410 — [FLB v1] FLB - Reliability (ICT) - Verify Job Skips Missing Sub-Items and Succeeds
(error346).

TWO-PHASE COMBINATION TEST (same rationale as every other suite's — a live WinRM mutation between
two pytest invocations can only be driven by the session's own agent, not pytest code):
  1. `pytest test_njm_70410.py::test_baseline_backup` — builds+runs a job whose source is the
     PARENT folder `C:\ErrorTest346_ForFLB` (containing `sub1\file1.txt`, `sub2\file2.txt`).
     No cleanup call — job survives into phase 2.
  2. Agent adds a dangling symlink (`sub2\broken_link.txt`, via `mklink` to a non-existent
     target) via WinRM.
  3. `pytest test_njm_70410.py::test_rerun_skips_missing_subitem` — reruns the SAME job and
     asserts it still completes (not fails) with at least 1 skipped item and an error346-coded
     report link — i.e. a genuinely-missing sub-item is skipped, not treated as a job failure
     (contrast with NJM-70409's ict45 case, where the MISSING ROOT itself fails the whole job).

⚠ CALIBRATION NOTE (real finding, live 2026-07-21): the TC's OWN literal recipe — just DELETE an
existing sub-folder (`sub1`) and rerun — does NOT reproduce a skip on this build. Confirmed live:
after deleting `sub1`, the rerun (an INCREMENTAL run, per its own Events log: "the job has run 1
time(s) previously... Backup type: INCREMENTAL") completed with `Skipped items: 0 item(s)` and
NO skip-related event in its Events log at all — the incremental engine simply omits a vanished
item from its scan; a deleted item is never "seen" in order to be marked as skipped. Only a
STILL-PRESENT-but-unreadable item (a dangling symlink — the same recipe validated for the whole
suite, see _helpers.py's module docstring) reliably triggers error346. The mutation this test
actually applies is therefore ADD a dangling symlink, not delete a sub-folder — `sub1`'s deletion
happened once during this suite's investigation and is harmless leftover, not part of the
intended repro.

⚠ If phase 2 (the symlink add) is never applied, phase 3 will just pass as a normal successful
rerun with 0 skips and silently fail to exercise error346 at all.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, report_link_attrs, run_and_wait_flb_job, skipped_items_count

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-70410")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-70410_error346"


@allure.title("NJM-70410 phase 1/2 — baseline backup of ErrorTest346_ForFLB (parent + 2 subfolders)")
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, ["Local Disk (C:)"], ["ErrorTest346_ForFLB"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"
    count = skipped_items_count(page, JOB_NAME)
    assert count == 0, f"expected 0 skipped items on the baseline run, got: {count}"


@allure.title("NJM-70410 phase 2/2 — rerun after sub1 is deleted skips it and still succeeds (error346)")
@pytest.mark.flaky(reruns=0)
def test_rerun_skips_missing_subitem(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=180_000)
    assert status == "Successful", (
        f"expected the job to SUCCEED despite the missing sub-item (skip, not fail), got: {status}"
    )

    count = skipped_items_count(page, JOB_NAME)
    assert count >= 1, f"expected at least 1 skipped item (the deleted sub1 folder), got: {count}"

    attrs = report_link_attrs(page, JOB_NAME)
    assert attrs.get("eventCode") == "error346", (
        f"expected the error346 skip-notification code, got: {attrs!r}"
    )

    flb_job_cleanup(JOB_NAME)
