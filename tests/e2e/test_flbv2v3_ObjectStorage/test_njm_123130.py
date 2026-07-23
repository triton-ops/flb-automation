r"""NJM-123130 — [FLB v1] Verify Backup to Immutable Synology C2 Object Storage (Windows & Linux
Sources).

Previously BLOCKED (no Synology C2 repository configured on nbr-84). CONFIRMED live 2026-07-22: a
Synology C2 repository now exists on nbr-84 (found via the Destination combo's live option list
while investigating an unrelated suite C failure). RE-CONFIRMED live 2026-07-23: only ONE Synology
C2 repository exists — display name `SynologyC2` (no underscore; no separate `..._Immutable`-named
repository was found searching the wizard's Destination combo for "Synology"). The original
finding recorded this as two repos, `Synology_C2`/`Synology_C2_Immutable`; corrected here. Same
pattern as test_njm_123133.py (Local-Immutable) — immutability is applied via the job-level
'Immutable for N days' retention option on this SAME repository, not a separate repo name. Build a
job against it with that option set, run it, confirm the recovery point is genuinely marked
immutable, and verify the recovered content matches the source.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.repository_management_page import RepositoryManagementPage

from ._helpers import build_flb_job, run_and_wait_flb_job, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-123130")]

REPOSITORY = "SynologyC2"


@allure.title("NJM-123130 — backup to immutable Synology C2 repository, 1-day immutability")
def test_backup_to_synology_c2_immutable(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-123130_synology-immutable")

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
