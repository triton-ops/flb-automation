"""NJM-67817 — [FLB v1] FLB - Functional (Linux) - Verify Backup from Ubuntu 24.04 LTS Desktop,
mixed file types. Original verdict (raw-RPC execution): PASS (built via the UI wizard — see
NJM-67702's note; also already covered by browser/checks/build_flb_jobs_linux_batch.py's
build-only batch script).

Verify FLB backup from an Ubuntu 24.04 LTS Desktop source (ubuntu24-desktop-src / PM-15 /
Ubuntu2404Desktop_16.119), mixed file types.
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

pytestmark = [pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-67817")]

MACHINE = "Ubuntu2404Desktop_16.119"


@allure.title("NJM-67817 — Backup from Ubuntu 24.04 LTS Desktop, mixed file types")
def test_ubuntu_24_04_desktop_mixed_types(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67817")
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
        "manifest-ubuntu24-mixed.sha256",
    )
