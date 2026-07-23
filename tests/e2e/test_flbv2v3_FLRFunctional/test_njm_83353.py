"""NJM-83353 — [FLB v1] FLR from FLB - Functional - Verify Recovery from a Local Repository.

Per the TC's own Xray steps: confirm an FLB job targeting a Local repository has a valid recovery
point; open Recover > Individual files; on the Files step select items to recover; on the Options
step choose Recover to CIFS Share (or NFS Share), finish and run; on the destination share, verify
recovered files match the source content.

Uses the Onboard repository (test-data/environment.md: id 2, type LOCAL, state OK) — the only
Local-type repository on nbr-84 available for this suite's Window11 source, and this suite's own
default `build_flb_job()` repository (made explicit here rather than left implicit, since this TC
is specifically about the Local-repository case).

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

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-83353")]

MACHINE = "Window11"
REPOSITORY = "Onboard repository"


@allure.title("NJM-83353 — recovery from a Local (Onboard) repository, recover to CIFS Share")
def test_recover_from_local_repository(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-83353")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"], repository=REPOSITORY)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed on {REPOSITORY}: {status}"

    started = recover_to_share(
        page, job_name, ["C:", "TestData_ForFLB"], ["atest1.txt", "Folder_test2"], "cifs"
    )
    assert started, "the FLR wizard did not confirm the recovery started"
