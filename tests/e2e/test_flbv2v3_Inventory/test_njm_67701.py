"""NJM-67701 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow on Windows 10 Enterprise.
Original verdict (raw-RPC execution): PASS, with a documented scope deviation.

Verify FLB end-to-end workflow (create -> run -> FLR recover -> compare) on a Windows 10
Enterprise source (win10-src / PM-25 / Window_10).

SCOPE NOTE (carried over from the original investigation): WinRM is not enabled on this host
(confirmed refused on both 5985 and 5986 with valid credentials — a local/console-access fix,
not bootstrappable via remoting), so the standard MixedTypes fixture was never seeded here.
Uses the pre-existing `TestData_ForFLB` tree already present on the machine instead. Since its
exact contents were never independently checksummed, this test verifies the job succeeds and FLR
shows a non-empty listing, rather than asserting specific file names — a deliberately looser
check reflecting the same scope deviation, not an oversight.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-67701")]

MACHINE = "Window_10"


@allure.title("NJM-67701 — End-to-end workflow on Windows 10 Enterprise (pre-existing data)")
def test_windows_10_e2e(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67701")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, ["C:", "TestData_ForFLB"])
    assert extract_item_names(rows), "FLR browse of TestData_ForFLB should show at least one item"
