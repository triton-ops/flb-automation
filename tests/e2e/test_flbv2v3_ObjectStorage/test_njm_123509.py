r"""NJM-123509 — [FLB v1] FLB - Functional - Verify Backup with Repository Encryption Enabled.

Exercises the Options-step 'Backup encryption' combo (FlbWizardPage.set_encryption()) plus the
password dialog it reveals (FlbWizardPage.set_encryption_password() — CALIBRATED live 2026-07-22,
resolving the NJM-123510 gap: enabling encryption alone left the job unsubmittable with no
visible error). Uses the Onboard repository (fast, no cloud dependency) since encryption is a
job-level option, not a repository-specific one.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, run_and_wait_flb_job, verify_checksum

pytestmark = [
    pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-123509"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"
MANIFEST = "manifest-win11-mixed.sha256"


@allure.title("NJM-123509 — backup with Backup Encryption enabled, Onboard repository")
def test_backup_with_encryption_enabled(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-123509_encrypted")

    build_flb_job(
        page, job_name, MACHINE, ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"],
        encryption=True,
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"encrypted job did not succeed: {status}"

    verify_checksum(page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"], "sample.pdf", MANIFEST)
