"""NJM-67809 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow on SLES 15 SP6.
Original verdict (raw-RPC execution): PASS (rebuilt via the UI wizard — see NJM-67702's note).

Verify FLB end-to-end workflow (create -> run -> FLR recover -> compare) on a SLES 15 SP6 source
(sles15-src / PM-20 / SLE_SUSE_15.205).
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

pytestmark = [pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-67809")]

MACHINE = "SLE_SUSE_15.205"


@allure.title("NJM-67809 — End-to-end workflow on SLES 15 SP6")
def test_sles_15_sp6_e2e(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67809")
    build_flb_job(page, job_name, MACHINE, ["TestData_ForFLB"], ["MixedTypes"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    # CALIBRATED live 2026-07-16: a Linux source's FLR left tree top-level node is "root", not
    # the wizard drill path's TestData_ForFLB — see NJM-67702's note.
    rows = flr_browse(page, job_name, ["root", "TestData_ForFLB", "MixedTypes"])
    found = set(extract_item_names(rows))
    assert found == MIXED_TYPES_FILES, f"expected the standard MixedTypes fileset, got {found}"

    verify_checksum(
        page, job_name, ["root", "TestData_ForFLB", "MixedTypes"], "sample.docx",
        "manifest-sles15-mixed.sha256",
    )
