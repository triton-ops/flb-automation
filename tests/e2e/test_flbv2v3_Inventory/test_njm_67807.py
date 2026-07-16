"""NJM-67807 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow on Ubuntu 24.04 LTS.
Original verdict (raw-RPC execution): PASS (rebuilt via the UI wizard — see NJM-67702's note).

Verify FLB end-to-end workflow (create -> run -> FLR recover -> compare) on an Ubuntu 24.04 LTS
source (linux-src / PM-2 / Linux_16.84, Ubuntu Server 24.04.3 LTS — the Server variant satisfies
this TC as-is since it doesn't require a Desktop qualifier, unlike NJM-67816/67817).

NOTE: this test shares a source machine (Linux_16.84/PM-2) with NJM-68933 in this same suite —
see _helpers.py's module docstring on why these must not run concurrently with each other.
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

pytestmark = [pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-67807")]

MACHINE = "Linux_16.84"


@allure.title("NJM-67807 — End-to-end workflow on Ubuntu 24.04 LTS (Server)")
def test_ubuntu_24_04_server_e2e(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67807")
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
        "manifest-linux-mixed.sha256",
    )
