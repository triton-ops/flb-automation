r"""NJM-123120 — [FLB v1] FLB - Functional - Verify Backup to Immutable Azure Blob Repository.

Build a job against an immutable repository with an 'Immutable for N days' retention set, run it,
confirm the recovery point is genuinely marked immutable, and verify the recovered content matches
the source. See test_njm_123133.py's module docstring for the shared immutability-mechanics
writeup (orphaned-backup-on-job-delete behavior, etc.) — not repeated here.

⚠ COST NOTE: this row uploads real data to a real external cloud account and leaves it there,
undeletable, for the immutability window — run deliberately, not by default.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.repository_management_page import RepositoryManagementPage

from ._helpers import build_flb_job, run_and_wait_flb_job, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-123120")]

REPOSITORY = "Azure_Immutable"


@allure.title("NJM-123120 — backup to immutable Azure Blob repository, 1-day immutability")
def test_backup_to_azure_immutable(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-123120_azure-immutable")

    build_flb_job(
        page, job_name, "Window11", ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"],
        repository=REPOSITORY, immutable_days=1,
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=600_000)
    assert status == "Successful", f"job did not succeed on {REPOSITORY}: {status}"

    rp = RepositoryManagementPage(page)
    rp.open()
    rp.open_repository(REPOSITORY)
    rp.open_backup("Window11")
    marker = rp.immutability_marker_text()
    assert marker, f"expected an 'Immutable until' marker on the recovery point for {REPOSITORY}, found none"

    DataProtectionPage(page).open()
    verify_checksum(
        page,
        job_name,
        ["C:", "TestData_ForFLB", "MixedTypes"],
        "sample.pdf",
        "manifest-win11-mixed.sha256",
    )
