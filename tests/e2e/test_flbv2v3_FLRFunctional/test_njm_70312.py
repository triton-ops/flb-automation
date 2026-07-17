"""NJM-70312 — [FLB v1] FLR from FLB - Backup Step - Verify Selection of Backup and Recovery
Point. Original status: never executed under the old RPC workflow (no cases/*.md runbook
exists).

Per the TC's own Xray steps: confirm a valid FLB recovery point exists and the source machine is
in Inventory (OK); from the backup/repository, choose Recover > Individual files; on the Backup
step, select a backup job and choose a SPECIFIC recovery point (both independently selectable);
switch to an OLDER recovery point and confirm the Files-step tree updates to reflect it.

FIXTURE NOTE: getting two genuinely different recovery points for the SAME job, without any
host-side content seeding (SSH/WinRM access to the source host is out of scope for this suite/
session), is done by running the job TWICE with a DIFFERENT item selection each time —
edit_flb_job_and_rerun() in _helpers.py reopens the wizard's Source step between runs and swaps
Folder_test2 -> Folder_test3, two pre-existing, byte-identical sibling folders under
C:\\TestData_ForFLB on windows-src (see test-data/test-data.md §1). This produces two REAL,
independently-verifiable recovery points for one job.

CALIBRATED LIVE 2026-07-16 (AUTO_FLB_NJM-70312_calib, built + fully cleaned up during
calibration — the job built by THIS test is the real AUTO_FLB_NJM-70312): the Backup step's
right-hand recovery-point picker (Table view, one radio per row) is a genuinely separate widget
from the left-hand job/machine tree (View: Jobs & Groups) — confirming both are independently
selectable (TC step 2). Selecting a non-default (older) recovery point and advancing to Files
correctly updates the tree/header to that recovery point's content on the first switch away from
the wizard's default (latest) selection within a fresh recover_file_level() session — see
file_level_recovery_page.py's select_recovery_point() docstring for a caveat about repeated
switches within one session (not exercised by this test, which opens a fresh session per
recovery point instead).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage

from ._helpers import build_flb_job, edit_flb_job_and_rerun, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70312")]

MACHINE = "Window11"
DRILL_PATH = ["Local Disk (C:)", "TestData_ForFLB"]


@allure.title("NJM-70312 — Backup step: independent job/recovery-point selection; RP switch updates Files tree")
def test_backup_step_recovery_point_selection(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70312")

    # --- Build RP1 (older): job selects only Folder_test2 ---
    # run_on_demand=False: keeps a real (never-triggered) schedule + its default 10-day
    # retention so BOTH recovery points created below actually persist — see
    # build_flb_job()'s docstring for why a genuinely on-demand job doesn't work for this TC.
    build_flb_job(page, job_name, MACHINE, DRILL_PATH, ["Folder_test2"], run_on_demand=False)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"RP1 (Folder_test2) job run did not succeed: {status}"

    # --- Build RP2 (latest): edit the SAME job to select Folder_test3 instead, run again ---
    status = edit_flb_job_and_rerun(
        page, job_name,
        drill_path=DRILL_PATH,
        uncheck_names=["Folder_test2"],
        check_names=["Folder_test3"],
    )
    assert status == "Successful", f"RP2 (Folder_test3) job run did not succeed: {status}"

    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name)

    # --- TC step 2: both the backup job AND a specific recovery point are independently
    # selectable on the Backup step ---
    assert flr.backup_step_machine_selected(MACHINE), (
        f"{MACHINE!r} is not shown as selected on the Backup step's job/machine tree"
    )
    # the picker can lag a run's own 'Successful' status by several minutes before showing its
    # recovery point (only clears on a fresh wizard open, not a same-session re-click) — see
    # wait_for_recovery_point_count()'s docstring
    recovery_points = flr.wait_for_recovery_point_count(job_name, min_count=2)
    assert len(recovery_points) >= 2, f"expected >=2 recovery points, found {len(recovery_points)}: {recovery_points}"
    # DOM/display order is newest-first (see list_recovery_points() docstring): index 0 is RP2
    # (latest, Folder_test3), index 1 is RP1 (older, Folder_test2).
    assert recovery_points[0]["selected"], f"the latest recovery point is not selected by default: {recovery_points}"
    assert not recovery_points[1]["selected"], f"the older recovery point is unexpectedly selected: {recovery_points}"

    # independently select the OLDER recovery point (index 1)
    flr.select_recovery_point(1)
    recovery_points_after = flr.list_recovery_points()
    assert recovery_points_after[1]["selected"], (
        f"the older recovery point did not become selected after select_recovery_point(1): {recovery_points_after}"
    )
    assert not recovery_points_after[0]["selected"], (
        f"the latest recovery point is still selected after switching to the older one: {recovery_points_after}"
    )
    # the machine/job selection on the LEFT tree is unaffected by the RP switch (independence,
    # the other half of TC step 2's claim)
    assert flr.backup_step_machine_selected(MACHINE), (
        f"{MACHINE!r} lost its selection on the job/machine tree after switching recovery points"
    )

    # --- TC step 3: switching to the older recovery point updates the Files-step tree ---
    flr.click_next()
    flr.wait_files_ready()
    older_label = flr.current_recovery_point_label(MACHINE)
    older_contents = flr.list_folder_contents(["C:", "TestData_ForFLB"])
    older_names = {item["name"] for item in older_contents}
    assert older_names == {"Folder_test2"}, (
        f"Files tree for the OLDER recovery point ({older_label!r}) does not show Folder_test2 only: {older_names}"
    )
    flr.click_cancel()

    # --- real content-diff assertion: a FRESH session (default = latest recovery point, RP2)
    # shows the genuinely different content (Folder_test3), never touching the RP picker ---
    flr2 = FileLevelRecoveryPage(page)
    flr2.recover_file_level(job_name)
    flr2.click_next()
    flr2.wait_files_ready()
    latest_label = flr2.current_recovery_point_label(MACHINE)
    latest_contents = flr2.list_folder_contents(["C:", "TestData_ForFLB"])
    latest_names = {item["name"] for item in latest_contents}
    assert latest_names == {"Folder_test3"}, (
        f"Files tree for the LATEST recovery point ({latest_label!r}) does not show Folder_test3 only: {latest_names}"
    )
    flr2.click_cancel()

    assert older_names != latest_names, (
        f"Files tree content did not differ between the two recovery points: "
        f"older={older_names!r} ({older_label!r}), latest={latest_names!r} ({latest_label!r})"
    )
