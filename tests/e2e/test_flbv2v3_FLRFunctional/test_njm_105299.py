"""NJM-105299 — [FLB v1] FLR - Recovery from HPE StoreOnce Repository.

Previously BLOCKED (no HPE StoreOnce repository fixture existed on nbr-84). CONFIRMED live
2026-07-21: `HPE_Repo` now exists on nbr-84 (Settings > Repositories: "HPE_Repo — No backups,
694.5 GB free" at the time of this check). Builds an FLB job targeting it, runs it, then recovers
via FLR to the win-fs3 CIFS share — same build->run->FLR-to-share pattern as the OS-support
matrix in this suite (test_njm_83226_83255_os_support_flr_matrix.py).

SCOPE NOTE (same convention as the rest of this suite): pytest asserts job status + the wizard's
recovery-started confirmation; destination-content verification is done via WinRM against
win-fs3, comparing the landed zip's files against manifest-win11-mixed.sha256 (Window11's
MixedTypes fileset, already used/verified elsewhere in this project).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-105299")]

MACHINE = "Window11"
REPOSITORY = "HPE_Repo"


@allure.title("NJM-105299 — FLR recovery from a backup on the HPE StoreOnce repository")
def test_flr_from_storeonce_repository(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-105299")

    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"],
                  repository=REPOSITORY)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job to {REPOSITORY} did not succeed: {status}"

    started = recover_to_share(page, job_name, ["C:", "TestData_ForFLB"], ["MixedTypes"], "cifs")
    assert started, "the FLR wizard did not confirm the recovery started"
