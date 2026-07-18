r"""NJM-70019 / 70018 / 70016 / 70013 — [FLB v1/v2] FLB - Functional - Verify Use Case: Create and
Run a Basic File/Folder Backup Job (UC1 & UC2); Verify Full Workflow (Create, Run, Recover, Delete
Job); Verify User Story: Backup Specific Individual Files (US4); Verify User Story: Backup Folders
(US1).

All four share the same MixedTypes fixture (test-data/test-data.md — 7 deterministic files:
sample.pdf/xml/json/docx/sys/jpg/mp4) on Window11 (C:\TestData_ForFLB\MixedTypes), differing only
in item-selection SCOPE, which is exactly what each TC is actually testing:
  - NJM-70019 (UC1&2): select the whole MixedTypes FOLDER — basic file/folder backup.
  - NJM-70016 (US4): select two INDIVIDUAL FILES inside MixedTypes (not the folder) — the
    recovery point must contain only those two, not the other five.
  - NJM-70013 (US1): select the MixedTypes folder specifically (not the machine root/other
    volumes) — proves folder-level scoping, not whole-machine backup.
  - NJM-70018 (Full workflow): builds+runs+recovers (browse-only, no original-location overwrite
    needed since the TC only asks to confirm recovered content matches source) then explicitly
    deletes the job and asserts it's gone from the Jobs sidebar — flb_job_cleanup's teardown
    would otherwise do this same delete silently at test end, but this TC's own steps call for
    verifying the deletion as part of the test itself, so it's done inline here instead.

NJM-70015 (US3 — recover accidentally-deleted files to their ORIGINAL location) is NOT covered
here: recovering to the original location is an execute-not-just-browse action gated by this
project's safety rules (see CLAUDE.md and suite F's NJM-182724, which owns this exact scenario)
— must ask the user before ever executing an original-location recovery. Deferred to suite F
rather than duplicated with a scope-reduced substitute here.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.job_management_page import JobManagementPage
from browser.pom.common.locators import DataProtectionLocators

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution]

MACHINE = "Window11"
# Wizard item-picker drill path (build_flb_job) vs FLR Files-step tree drill path (flr_browse) use
# DIFFERENT root-node naming for the same C: drive ('Local Disk (C:)' vs plain 'C:') — the same
# conflation bug already found+fixed once in test_repo_backup_matrix.py (see
# tests/e2e/test_flbv2v3_ObjectStorage's own flr_parent column) and re-found live here via a real
# test failure (flr_browse timed out drilling 'Local Disk (C:)' in the FLR tree, which doesn't use
# that label) before this fix — two separate FLR-facing constants, never share one.
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
DRILL_TO_MIXEDTYPES = ["Local Disk (C:)", "TestData_ForFLB", "MixedTypes"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-70019 — basic file/folder backup job (UC1 & UC2)")
@pytest.mark.jira("NJM-70019")
def test_basic_file_folder_backup(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70019_basic")

    build_flb_job(page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"expected all 7 MixedTypes files, got {names}"


@allure.title("NJM-70016 — backup specific individual files, not whole folders (US4)")
@pytest.mark.jira("NJM-70016")
def test_backup_individual_files_only(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70016_indiv-files")
    selected = ["sample.pdf", "sample.xml"]

    build_flb_job(page, job_name, MACHINE, DRILL_TO_MIXEDTYPES, selected)
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == set(selected), (
        f"expected ONLY the individually-selected files {selected}, got {names} "
        f"(unselected siblings {ALL_MIXEDTYPES_FILES - set(selected)} must be excluded)"
    )


@allure.title("NJM-70013 — backup a specific folder, not the whole machine (US1)")
@pytest.mark.jira("NJM-70013")
def test_backup_folder_scope_not_whole_machine(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70013_folder-scope")

    build_flb_job(page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, (
        f"expected exactly the MixedTypes folder's own 7 files (folder-level scope), got {names}"
    )


@allure.title("NJM-70018 — full workflow: create, run, recover, delete job")
@pytest.mark.jira("NJM-70018")
def test_full_workflow_create_run_recover_delete(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70018_full-workflow")

    build_flb_job(page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"recovered content mismatch: {names}"

    JobManagementPage(page).delete_job(job_name)
    page.wait_for_timeout(1000)
    remaining = page.locator(DataProtectionLocators.sidebar_job_row(job_name)).count()
    assert remaining == 0, f"job {job_name!r} should be removed from the Jobs sidebar after delete"
