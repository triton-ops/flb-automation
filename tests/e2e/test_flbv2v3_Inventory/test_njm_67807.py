"""NJM-67807 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow on Ubuntu 24.04 LTS
(Server).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import (
    MIXED_TYPES_FILES,
    build_flb_job,
    extract_item_names,
    flr_browse,
    run_and_wait_flb_job,
    verify_checksum,
)

# xdist_group: shares a source (Linux_16.84/PM-2) with NJM-68933 in this suite — see
# test_njm_68933.py's own marker and docs/xdist-parallelization.md.
pytestmark = [
    pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-67807"),
    pytest.mark.xdist_group(name="Linux_16.84"),
]

MACHINE = "Linux_16.84"
MANIFEST = "manifest-linux-mixed.sha256"


@allure.title("NJM-67807 — End-to-end workflow on Ubuntu 24.04 LTS (Server)")
def test_linux_os_support_e2e(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67807")
    build_flb_job(page, job_name, MACHINE, ["TestData_ForFLB"], ["MixedTypes"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, ["root", "TestData_ForFLB", "MixedTypes"])
    found = set(extract_item_names(rows))
    assert found == MIXED_TYPES_FILES, f"expected the standard MixedTypes fileset, got {found}"

    verify_checksum(page, job_name, ["root", "TestData_ForFLB", "MixedTypes"], "sample.docx", MANIFEST)
