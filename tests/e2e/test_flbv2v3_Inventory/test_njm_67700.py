"""NJM-67700 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow on Windows 11.
Original verdict (raw-RPC execution): PASS.

Verify FLB end-to-end workflow (create -> run -> FLR recover -> compare) on a Windows 11 source
(windows-src / PM-3 / Window11).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import (
    MIXED_TYPES_FILES,
    build_flb_job,
    flr_browse,
    extract_item_names,
    run_and_wait_flb_job,
    verify_checksum,
)

pytestmark = [pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-67700")]

MACHINE = "Window11"


@allure.title("NJM-67700 — End-to-end workflow on Windows 11")
def test_windows_11_e2e(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67700")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"])
    found = set(extract_item_names(rows))
    assert found == MIXED_TYPES_FILES, f"expected the standard MixedTypes fileset, got {found}"

    verify_checksum(
        page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"], "sample.docx",
        "manifest-win11-mixed.sha256",
    )
