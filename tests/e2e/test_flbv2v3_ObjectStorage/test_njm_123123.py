r"""NJM-123123 — [FLB v1] FLB - Functional - Verify Backup to the Backblaze B2 Repository (Windows
& Linux Sources).

Back up the seeded MixedTypes fixture, run a full then an incremental backup, recover a file via
FLR Download and verify its checksum against the source manifest — one function per source OS.
See test_njm_67687.py's module docstring for the shared scope note and incremental methodology
(identical reasoning, not repeated here).

FIXTURE NOTE: there is no separate non-immutable Backblaze repo on nbr-84 — this reuses
`BlackBlaze_Immutable` WITHOUT enabling any immutability/retention option on the job, the same
documented substitution convention environment.md already uses for Cloudian standing in for the
removed Ceph_S3.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, run_full_then_incremental, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-123123")]

REPOSITORY = "BlackBlaze_Immutable"


@allure.title("NJM-123123 — backup to Backblaze B2 repository (Windows), full + incremental + checksum verify")
def test_backup_to_backblaze_windows(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-123123_backblaze-win")

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


@allure.title("NJM-123123 — backup to Backblaze B2 repository (Linux), full + incremental + checksum verify")
def test_backup_to_backblaze_linux(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-123123_backblaze-linux")

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
