"""NJM-67694 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow on Windows Server 2019.
Original verdict (raw-RPC execution): PASS.

Verify FLB end-to-end workflow (create -> run -> FLR recover -> compare) on a Windows Server
2019 source (win-fs3-src / PM-9 / Win_Server2019_15.3). Scope note: this machine's primary role
in the framework is the NFS/CIFS share host + FLR export target — reused here as an FLB source
in its secondary role; the share-host role is unaffected.
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

pytestmark = [pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-67694")]

MACHINE = "Win_Server2019_15.3"


@allure.title("NJM-67694 — End-to-end workflow on Windows Server 2019")
def test_windows_server_2019_e2e(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67694")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"])
    found = set(extract_item_names(rows))
    assert found == MIXED_TYPES_FILES, f"expected the standard MixedTypes fileset, got {found}"

    verify_checksum(
        page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"], "sample.docx",
        "manifest-win2019-mixed.sha256",
    )
