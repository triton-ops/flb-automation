r"""NJM-123121 — [FLB v1] FLB - Functional - Verify Backup to the Wasabi Repository (Windows &
Linux Sources).

Back up the seeded MixedTypes fixture, run a full then an incremental backup, recover a file via
FLR Download and verify its checksum against the source manifest — one function per source OS.
See test_njm_67687.py's module docstring for the shared scope note and incremental methodology
(identical reasoning, not repeated here).

⚠ KNOWN CURRENT ISSUE (found live 2026-07-22): the non-immutable `Wasabi_Repo` repository no
longer exists on nbr-84 — only `Wasabi-immutable` remains now (confirmed via the Destination
combo's live option list). Both functions below will fail at `build_flb_job()`'s repository
selection step until this is resolved (either point them at a real non-immutable Wasabi repo once
one exists again, or this TC needs to be re-scoped/blocked) — awaiting a decision, not yet fixed.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, run_full_then_incremental, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-123121")]

REPOSITORY = "Wasabi_Repo"


@allure.title("NJM-123121 — backup to Wasabi repository (Windows), full + incremental + checksum verify")
def test_backup_to_wasabi_windows(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-123121_wasabi-win")

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


@allure.title("NJM-123121 — backup to Wasabi repository (Linux), full + incremental + checksum verify")
def test_backup_to_wasabi_linux(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-123121_wasabi-linux")

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
