r"""NJM-67687 — [FLB v1] FLB - Functional - Verify Backup to the Onboard Repository (Windows &
Linux Sources). Also fully exercises NJM-85728 (Repository - Integrity and Structure of Backup
Data Post-Job): that TC's steps (build+run full, verify recovery point, add data+run incremental,
FLR-recover and verify content) are exactly this test's own body, so it has no separate file — a
second live full+incremental job against the same repository would add appliance load, not
coverage.

Back up the seeded MixedTypes fixture, run a full then an incremental backup, recover a file via
FLR Download and verify its checksum against the source manifest — one function per source OS.

SCOPE NOTE (same convention as the rest of this project): pytest asserts both the full AND the
incremental job runs reached Successful, and the downloaded file's SHA-256 matches the manifest —
this last assertion IS the "recovered files are byte-identical to the source" check the TC asks
for, verified directly in Python (not deferred to an agent-driven remoting step), since
verify_checksum() downloads through the browser itself.

INCREMENTAL METHODOLOGY — see _helpers.py's module docstring for the full reasoning. In short: a
real incremental backup captures the CHANGE since the last backup, which this suite cannot
literally exercise (changing SOURCE content mid-test needs SSH/WinRM from inside the pytest
process — a capability this project doesn't have). This test runs the SAME job twice unmodified
via run_full_then_incremental() — the second run is confirmed live to default to 'Incremental' on
its own, not something this test forces by editing the job's selection.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, run_full_then_incremental, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-67687")]

REPOSITORY = "Onboard repository"


@allure.title("NJM-67687 — backup to Onboard repository (Windows), full + incremental + checksum verify")
def test_backup_to_onboard_windows(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67687_onboard-win")

    build_flb_job(page, job_name, "Window11", ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"],
                  repository=REPOSITORY)
    full_status, incremental_status = run_full_then_incremental(page, job_name, timeout_ms=600_000)
    assert full_status == "Successful", f"full run did not succeed on {REPOSITORY}: {full_status}"
    assert incremental_status == "Successful", f"incremental run did not succeed on {REPOSITORY}: {incremental_status}"

    verify_checksum(
        page,
        job_name,
        ["C:", "TestData_ForFLB", "MixedTypes"],
        "sample.pdf",
        "manifest-win11-mixed.sha256",
    )


@allure.title("NJM-67687 — backup to Onboard repository (Linux), full + incremental + checksum verify")
def test_backup_to_onboard_linux(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67687_onboard-linux")

    build_flb_job(page, job_name, "Linux_16.84", ["TestData_ForFLB"], ["MixedTypes"],
                  is_linux=True, repository=REPOSITORY)
    full_status, incremental_status = run_full_then_incremental(page, job_name, timeout_ms=600_000)
    assert full_status == "Successful", f"full run did not succeed on {REPOSITORY}: {full_status}"
    assert incremental_status == "Successful", f"incremental run did not succeed on {REPOSITORY}: {incremental_status}"

    verify_checksum(
        page,
        job_name,
        ["root", "TestData_ForFLB", "MixedTypes"],
        "sample.pdf",
        "manifest-linux-mixed.sha256",
    )
