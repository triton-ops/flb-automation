r"""NJM-123129 — [FLB v1] Verify Backup to Synology C2 Object Storage (Windows & Linux Sources).

Previously BLOCKED (no Synology C2 repository configured on nbr-84). CONFIRMED live 2026-07-22:
a Synology C2 repository now exists on nbr-84 (found via the Destination combo's live option
list while investigating an unrelated suite C failure). RE-CONFIRMED live 2026-07-23: the
repository's real display name is `SynologyC2` (no underscore) — the original finding recorded it
as `Synology_C2`, which does not match anything in the wizard's Destination combo (search for
"Synology_C2" returns nothing; search for "Synology" returns exactly one match, `SynologyC2`).
Fixed here. Same pattern as test_njm_67687.py — back up the seeded MixedTypes fixture, run a full
then an incremental backup, recover a file via FLR Download and verify its checksum against the
source manifest — one function per source OS.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, run_full_then_incremental, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-123129")]

REPOSITORY = "SynologyC2"


@allure.title("NJM-123129 — backup to Synology C2 (Windows), full + incremental + checksum verify")
def test_backup_to_synology_c2_windows(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-123129_synology-win")

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


@allure.title("NJM-123129 — backup to Synology C2 (Linux), full + incremental + checksum verify")
def test_backup_to_synology_c2_linux(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-123129_synology-linux")

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
