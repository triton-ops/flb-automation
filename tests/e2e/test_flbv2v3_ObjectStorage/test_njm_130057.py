r"""NJM-130057 — [FLB v1] FLB - Functional - Verify Job Execution with Repository Encryption
Enabled/Disabled.

Asserts BOTH an unencrypted and an encrypted run of the same source/destination succeed and both
recover correctly. See test_njm_123509.py's module docstring for the encryption-password
calibration note (identical mechanics, not repeated here).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, run_and_wait_flb_job, verify_checksum

pytestmark = [
    pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-130057"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"
MANIFEST = "manifest-win11-mixed.sha256"


@allure.title("NJM-130057 — backup with Backup Encryption disabled, Onboard repository")
def test_backup_with_encryption_disabled(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-130057_unencrypted")

    build_flb_job(
        page, job_name, MACHINE, ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"],
        encryption=False,
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"unencrypted job did not succeed: {status}"

    verify_checksum(page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"], "sample.pdf", MANIFEST)


@allure.title("NJM-130057 — backup with Backup Encryption enabled, Onboard repository")
def test_backup_with_encryption_enabled(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-130057_encrypted")

    build_flb_job(
        page, job_name, MACHINE, ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"],
        encryption=True,
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"encrypted job did not succeed: {status}"

    verify_checksum(page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"], "sample.pdf", MANIFEST)
