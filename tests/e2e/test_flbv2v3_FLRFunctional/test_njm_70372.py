"""NJM-70372 — [FLB v1] FLR from FLB - Functional - Verify Recovery from a Full Recovery Point.
Original status: never executed under the old RPC workflow (no cases/*.md runbook exists).

Per the TC's own Xray steps: confirm one FLB job has BOTH a Full and an Incremental recovery
point; open Recover > Individual files and select the FULL recovery point; select items; recover
to a CIFS share; verify the destination matches the Full RP's content.

FIXTURE (same machinery NJM-70312 calibrated): run 1 of a fresh job is by definition the FULL
recovery point (selection: Folder_test2); run 2 via edit_flb_job_and_rerun() swaps the selection
to Folder_test3 and forces backup_type='Incremental' (REQUIRED — a second Full supersedes the
prior chain and asynchronously prunes the first point; see edit_flb_job_and_rerun()'s
calibration docstring). Result: RP index 1 (older) = Full with Folder_test2 content, RP index 0
(latest) = Incremental with Folder_test3 content — genuinely different content per RP, so the
destination unambiguously proves WHICH point was recovered: this test's zip must contain
Folder_test2/* paths and no Folder_test3.

recover_to_share(rp_index=1) also waits for BOTH recovery points to be visible in the picker
first (wait_for_recovery_point_count min_count=2) — that is TC step 1's Full+Incremental-pair
precondition, asserted in-browser, not assumed.

SCOPE NOTE (same convention as the rest of this suite): pytest asserts the wizard flow and both
runs' Successful status; destination-content verification (TC step 5) is done by the agent
driving WinRM against win-fs3 (expected: exactly the 21 Folder_test2 manifest entries).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, edit_flb_job_and_rerun, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70372")]

MACHINE = "Window11"
DRILL_PATH = ["Local Disk (C:)", "TestData_ForFLB"]


@allure.title("NJM-70372 — Recovery from the FULL recovery point of a Full+Incremental chain")
def test_recover_from_full_recovery_point(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70372")

    # run 1 -> Full RP (Folder_test2). run_on_demand=False keeps a real schedule + its default
    # retention so both recovery points persist (see build_flb_job()'s docstring).
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

    # TC steps 2-4: select the FULL (older, index 1) recovery point and recover it to CIFS.
    started = recover_to_share(
        page, job_name, ["C:", "TestData_ForFLB"], ["Folder_test2"], "cifs", rp_index=1
    )
    assert started, "the FLR wizard did not confirm the recovery started"
