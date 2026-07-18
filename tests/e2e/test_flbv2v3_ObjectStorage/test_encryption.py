r"""NJM-123509 / 130057 — [FLB v1] FLB - Functional - Verify Backup with Repository Encryption
Enabled / Verify Job Execution with Repository Encryption Enabled/Disabled.

Both TCs exercise the SAME already-calibrated Options-step 'Backup encryption' combo
(FlbWizardPage.set_encryption(), CALIBRATED live 2026-07-08 — Disabled/Enabled, no new POM work
needed). NJM-123509 asserts a single encrypted run recovers correctly; NJM-130057 asserts BOTH an
unencrypted and an encrypted run of the same source/destination succeed and both recover
correctly — written as one parametrized matrix since the body is identical either way.

Uses the Onboard repository (fast, no cloud dependency) since encryption is a job-level option,
not a repository-specific one — this is the fastest fixture that isolates the behavior under test.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, run_and_wait_flb_job, verify_checksum

pytestmark = [
    pytest.mark.flb, pytest.mark.objectstorage,
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"
MANIFEST = "manifest-win11-mixed.sha256"

ENCRYPTION_TCS = [
    pytest.param("NJM-123509", True, marks=pytest.mark.jira("NJM-123509"), id="NJM-123509-encrypted"),
    pytest.param("NJM-130057", False, marks=pytest.mark.jira("NJM-130057"), id="NJM-130057-unencrypted"),
    pytest.param("NJM-130057", True, marks=pytest.mark.jira("NJM-130057"), id="NJM-130057-encrypted"),
]


@pytest.mark.parametrize("jira_id,encryption", ENCRYPTION_TCS)
def test_backup_with_repository_encryption(logged_in_page, flb_job_cleanup, jira_id, encryption):
    label = "encrypted" if encryption else "unencrypted"
    allure.dynamic.title(f"{jira_id} — backup with Backup Encryption {label}, Onboard repository")
    page = logged_in_page
    job_name = flb_job_cleanup(f"AUTO_FLB_{jira_id}_{label}")

    build_flb_job(
        page, job_name, MACHINE, ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"],
        encryption=encryption,
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed ({label}): {status}"

    verify_checksum(page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"], "sample.pdf", MANIFEST)
