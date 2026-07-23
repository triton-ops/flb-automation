"""NJM-83358 — [FLB v1] FLR from FLB - Functional - Verify Recovery from a Backblaze B2
Repository.

Per the TC's own Xray steps: confirm an FLB job targeting a Backblaze B2 repository has a valid
recovery point; open Recover > Individual files; on the Files step select items to recover; on
the Options step choose Recover to CIFS Share, finish and run; on the destination share, verify
recovered files match the source content.

Uses BlackBlaze_Immutable (test-data/environment.md: id 13, type BACKBLAZE, state OK) — no plain
non-immutable Backblaze repo exists on nbr-84 (confirmed live 2026-07-23 via the wizard's own
Destination-step repo search: only 'BlackBlaze_Immutable' matches), reused without the
immutability option for this non-immutable TC, same substitution convention documented in
test_flbv2v3_ObjectStorage/_helpers.py's module docstring.

⚠ COST NOTE: this row uploads real data to a real external Backblaze B2 account. Run
deliberately, not by default in a routine batch pass.

SCOPE NOTE (same convention as the rest of this suite): pytest asserts only on what the browser can
observe — the wizard's own recovery-started confirmation and the FLB job's Successful status.
Destination-content verification (TC step 5) is done separately by the agent driving WinRM against
win-fs3 and reported alongside this test's result — pytest itself cannot call the remoting tools
this project uses for that.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-83358")]

MACHINE = "Window11"
REPOSITORY = "BlackBlaze_Immutable"


@allure.title("NJM-83358 — recovery from a Backblaze B2 repository, recover to CIFS Share")
def test_recover_from_backblaze_b2_repository(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-83358")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"], repository=REPOSITORY)
    status = run_and_wait_flb_job(page, job_name, timeout_ms=600_000)
    assert status == "Successful", f"job did not succeed on {REPOSITORY}: {status}"

    started = recover_to_share(
        page, job_name, ["C:", "TestData_ForFLB"], ["atest1.txt", "Folder_test2"], "cifs"
    )
    assert started, "the FLR wizard did not confirm the recovery started"
