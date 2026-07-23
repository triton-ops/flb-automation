r"""NJM-123133 — [FLB v1] FLB - Functional - Verify Backup to Immutable Local Linux Repository. Also
representatively satisfies NJM-70517 ("Linux-based or NAS repository with immutability") — same
immutable-repository mechanics against the Local-Immutable repository (this appliance's own "Local
Linux" framing); no separate file, since a second live job would add cost, not coverage.

Build a job against an immutable repository with an 'Immutable for N days' retention set, run it,
confirm the recovery point is genuinely marked immutable, and verify the recovered content matches
the source.

CONFIRMED LIVE 2026-07-18 (browser/checks/check_immutability_calibration.py — first-ever proof on
this appliance that NBR can create a genuinely immutable savepoint, updating test-data/
environment.md's long-standing "never proven" caveat): the recovery point's own detail page
(Settings -> Repositories -> <repo> -> <machine>) shows 'Immutable until'/'Protected until'
columns with real computed timestamps. Deleting the JOB is NOT blocked (disappears from the Jobs
sidebar normally via flb_job_cleanup) — but the underlying BACKUP does NOT delete with it; it
survives as an orphaned entry until the immutable window elapses. Uses the shortest practical
period (1 day) to minimize how long that orphaned data lingers — expected/by-design, not a leak
to chase. This row is free (local disk) and intended to be run routinely.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.repository_management_page import RepositoryManagementPage

from ._helpers import build_flb_job, run_and_wait_flb_job, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-123133")]

REPOSITORY = "Local-Immutable"


@allure.title("NJM-123133 — backup to immutable Local-Immutable repository, 1-day immutability")
def test_backup_to_local_immutable(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-123133_local-immutable")

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

    # recover_file_level() (inside verify_checksum) expects the Data Protection dashboard's own
    # Jobs sidebar to already be on-screen — navigate back explicitly (found live 2026-07-19: a
    # real authoring bug where skipping this made the job-row locator wait out its full timeout).
    DataProtectionPage(page).open()
    verify_checksum(
        page,
        job_name,
        ["C:", "TestData_ForFLB", "MixedTypes"],
        "sample.pdf",
        "manifest-win11-mixed.sha256",
    )
