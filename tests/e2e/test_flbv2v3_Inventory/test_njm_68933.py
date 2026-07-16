"""NJM-68933 — [FLB v1] FLB - Functional (Linux) - Verify Backup of EXT4 File System.
Original verdict (raw-RPC execution): PASS (built via the UI wizard — see NJM-67702's note; also
already covered by browser/checks/build_flb_jobs_linux_batch.py's build-only batch script).

Verify FLB backup of an ext4 root filesystem (linux-src / PM-2 / Linux_16.84) — backs up the
whole TestData_ForFLB tree (not just the MixedTypes subfolder used by the OS-support TCs), since
this TC's focus is filesystem-type coverage rather than a specific fileset's content. No
per-file content assertion — the job succeeding plus a non-empty FLR listing is the pass
condition, matching the TC's own filesystem-coverage (not content-matching) objective.

NOTE: this test shares a source machine (Linux_16.84/PM-2) with NJM-67807 in this same suite —
see _helpers.py's module docstring on why these must not run concurrently with each other.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, flr_browse, extract_item_names, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-68933")]

MACHINE = "Linux_16.84"


@allure.title("NJM-68933 — Backup of EXT4 file system")
def test_ext4_backup(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68933")
    build_flb_job(page, job_name, MACHINE, [], ["TestData_ForFLB"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    # CALIBRATED live 2026-07-16: a Linux source's FLR left tree top-level node is "root", not
    # the wizard drill path's TestData_ForFLB — see NJM-67702's note.
    rows = flr_browse(page, job_name, ["root", "TestData_ForFLB"])
    assert extract_item_names(rows), "FLR browse of the ext4 TestData_ForFLB tree should show at least one item"
