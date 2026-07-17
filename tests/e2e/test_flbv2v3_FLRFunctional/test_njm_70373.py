"""NJM-70373 — [FLB v1] FLR from FLB - Functional - Verify Recovery from an Incremental Recovery
Point. Original status: never executed under the old RPC workflow (no cases/*.md runbook exists).

Per the TC's own Xray steps: confirm one FLB job has BOTH a Full and an Incremental recovery
point; open Recover > Individual files and select the INCREMENTAL recovery point; select items
(including the incremental changes); recover to a CIFS share; verify the destination reflects
the state at the Incremental RP.

FIXTURE: identical Full+Incremental chain machinery to NJM-70372 (see that file's docstring and
edit_flb_job_and_rerun()'s calibration) — run 1 = Full RP with Folder_test2 content, run 2 =
Incremental RP with Folder_test3 content. The "incremental changes" (TC step 3) ARE the
selection swap: Folder_test3 exists only in the incremental point's state, so this test's
destination zip must contain Folder_test3/* paths and no Folder_test2 — the exact inverse of
NJM-70372's, from the same chain shape.

rp_index=0 selects the latest point explicitly (display order is newest-first — the incremental)
and, through recover_to_share()'s min_count=2 wait, asserts the Full+Incremental pair actually
exists in the picker first — TC step 1's precondition, checked in-browser, not assumed.

SCOPE NOTE (same convention as the rest of this suite): pytest asserts the wizard flow and both
runs' Successful status; destination-content verification (TC step 5) is done by the agent
driving WinRM against win-fs3 (expected: exactly the 21 Folder_test3 manifest entries).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, edit_flb_job_and_rerun, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70373")]

MACHINE = "Window11"
DRILL_PATH = ["Local Disk (C:)", "TestData_ForFLB"]


@allure.title("NJM-70373 — Recovery from the INCREMENTAL recovery point of a Full+Incremental chain")
def test_recover_from_incremental_recovery_point(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70373")

    # run 1 -> Full RP (Folder_test2); run_on_demand=False keeps both points (see NJM-70372).
    build_flb_job(page, job_name, MACHINE, DRILL_PATH, ["Folder_test2"], run_on_demand=False)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"run 1 (Full RP) did not succeed: {status}"

    # run 2 -> Incremental RP (Folder_test3).
    status = edit_flb_job_and_rerun(
        page, job_name,
        drill_path=DRILL_PATH,
        uncheck_names=["Folder_test2"],
        check_names=["Folder_test3"],
    )
    assert status == "Successful", f"run 2 (Incremental RP) did not succeed: {status}"

    # TC steps 2-4: select the INCREMENTAL (latest, index 0) recovery point explicitly and
    # recover its content (Folder_test3 — the incremental change itself) to CIFS.
    started = recover_to_share(
        page, job_name, ["C:", "TestData_ForFLB"], ["Folder_test3"], "cifs", rp_index=0
    )
    assert started, "the FLR wizard did not confirm the recovery started"
