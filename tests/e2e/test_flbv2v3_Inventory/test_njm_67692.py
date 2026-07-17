"""NJM-67692 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow on Windows Server 2025.
Original verdict (raw-RPC execution): PASS.

Verify FLB end-to-end workflow (create -> run -> FLR recover -> compare) on a Windows Server
2025 source (win2025-src / PM-19 / Win_Server2025_15.245).

CALIBRATING live 2026-07-16: first live exercise of real content-integrity verification (vs.
filename-only FLR-browse elsewhere in this suite) — downloads sample.docx via the FLR wizard's
Download recovery type and compares its SHA-256 against test-data/manifests/manifest-win2025-
mixed.sha256, the manifest test-data/test-data.md documents as "the verification oracle for FLR".
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

pytestmark = [pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-67692")]

MACHINE = "Win_Server2025_15.245"


@allure.title("NJM-67692 — End-to-end workflow on Windows Server 2025")
def test_windows_server_2025_e2e(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67692")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"])
    found = set(extract_item_names(rows))
    assert found == MIXED_TYPES_FILES, f"expected the standard MixedTypes fileset, got {found}"

    verify_checksum(
        page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"], "sample.docx",
        "manifest-win2025-mixed.sha256",
    )
