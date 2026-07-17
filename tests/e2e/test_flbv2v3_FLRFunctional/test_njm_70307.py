"""NJM-70307 — [FLB v1] FLR from FLB - Functional - Verify End-to-End Recovery via FLR Wizard.
Original status: never executed under the old RPC workflow (no cases/*.md runbook exists).

Per the TC's own Xray steps: confirm a valid FLB recovery point, open Recover > Individual
files, select at least one file and one folder on the Files step, choose 'Recover to File
Share (CIFS)' on the Options step, finish and run — the recovery should complete successfully.

SCOPE NOTE: this suite drives the wizard through a REAL execution (not just a browse), so the
pytest assertion is limited to what the browser can observe — the wizard's own "The File Level
recovery has started" confirmation and the FLB job's Successful status. Destination-content
verification (recovered files/folders present on the CIFS share with matching content, per the
TC's own step 5) is done separately by the agent driving WinRM against win-fs3 — pytest itself
cannot call the remoting tools this project uses for that (see _helpers.py's module docstring).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70307")]

MACHINE = "Window11"


@allure.title("NJM-70307 — End-to-end recovery via FLR wizard (CIFS)")
def test_flr_wizard_end_to_end(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70307")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    started = recover_to_share(page, job_name, ["C:", "TestData_ForFLB"], None, "cifs")
    assert started, "the FLR wizard did not confirm the recovery started"
