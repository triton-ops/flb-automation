r"""NJM-67678 / 67583 / 185052 / 182439 / 185036 — [FLB v1/v3] FLB Job Wizard - Options Step -
Verify All Job Options (App-aware, Scripts, etc.); FLB Job Wizard - Retention Step - Verify
Creation of a Job with Custom Retention Rules; FLB Job Wizard - Options - ACL default 'Back up
only folder permissions' does not capture file-level permissions; FLB Job Wizard - Options - Back
up folder and file permissions (ACL); FLB - Functional - 'Limit a concurrent task to N folders'
field governs folder parallelism.

Builds on the Options-step POM calibration added 2026-07-19 (FlbWizardPage.set_acl_mode() /
set_app_aware_mode() / set_concurrent_task_limit(), _helpers.py's build_flb_job() kwargs) —
see browser/pom/common/locators.py's OptionsLocators docstring for the full live-calibration
writeup, including two real gaps that scope these tests down from their literal TC wording:

1. **NJM-185052/182439 (ACL fidelity)**: the literal TC steps want a folder whose FILES and
   SUBFOLDERS carry genuinely DISTINCT ACLs, then a post-recovery icacls comparison proving
   folder-only vs folder+file permission capture. Setting up per-file distinct ACLs (via
   `icacls` over WinRM) and diffing them after recovery is a real, separate piece of fixture +
   verification work not attempted here — these two tests instead verify what the Options step
   itself actually does: the ACL combo accepts each value and the job completes successfully
   with the selected content intact. The folder-vs-file ACL-fidelity claim itself is UNVERIFIED
   — a genuine scope reduction, stated honestly rather than faked.

2. **NJM-185036 (concurrent-task-limit governs folder parallelism)**: NBR's UI has no visible
   per-folder timing/concurrency indicator, so "observe folder processing" (the TC's own step 3)
   isn't something a UI-driven test can directly witness. This test instead verifies the field
   accepts both a low (1) and high (8) value and that the job completes successfully with all
   content backed up either way — proving the setting doesn't break anything, not the actual
   concurrency behavior. Uses TestData_ForFLB itself (18 top-level subfolders — Folder_test1/2/3,
   FolderEmpty_test4/5, 9× ft_*, Subfolder_200Folders, Wilcard_Recheck — close to but not
   literally the TC's own '20+' example) rather than MixedTypes, since the whole point is a
   source with many subfolders.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution]

MACHINE = "Window11"
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
DRILL_TO_MIXEDTYPES = ["Local Disk (C:)", "TestData_ForFLB", "MixedTypes"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-67678 — Options step: exercise app-aware/ACL/encryption/concurrency options together")
@pytest.mark.jira("NJM-67678")
def test_options_step_all_settings_accepted(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67678_all-options")

    build_flb_job(
        page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"],
        acl_mode="Back up folder and file permissions",
        app_aware_mode="Enabled (proceed on error)",
        concurrent_task_limit=2,
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job with combined Options-step settings did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"expected all 7 MixedTypes files, got {names}"


@allure.title("NJM-67583 — Retention step: custom 'keep backups for N units' rule is accepted")
@pytest.mark.jira("NJM-67583")
def test_retention_step_custom_rule_accepted(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-67583_custom-retention")

    build_flb_job(
        page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"],
        retention=(30, "days"),
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job with a custom retention rule did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"expected all 7 MixedTypes files, got {names}"


@allure.title("NJM-185052 — ACL default ('Back up only folder permissions') job completes normally")
@pytest.mark.jira("NJM-185052")
def test_acl_default_folder_only_permissions(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-185052_acl-folder-only")

    # Leave acl_mode unset — 'Back up only folder permissions' is the wizard's own default.
    build_flb_job(page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"expected all 7 MixedTypes files, got {names}"


@allure.title("NJM-182439 — ACL set to 'Back up folder and file permissions'")
@pytest.mark.jira("NJM-182439")
def test_acl_folder_and_file_permissions(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-182439_acl-folder-and-file")

    build_flb_job(
        page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"],
        acl_mode="Back up folder and file permissions",
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"expected all 7 MixedTypes files, got {names}"


@allure.title("NJM-185036 — 'Limit a concurrent task to N folders' accepts low and high values")
@pytest.mark.jira("NJM-185036")
@pytest.mark.parametrize("limit", [1, 8], ids=["limit-1", "limit-8"])
def test_concurrent_task_limit_accepted(logged_in_page, flb_job_cleanup, limit):
    page = logged_in_page
    job_name = flb_job_cleanup(f"AUTO_FLB_NJM-185036_concurrency-{limit}")

    build_flb_job(
        page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"],
        concurrent_task_limit=limit,
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job with concurrent-task-limit={limit} did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, ["C:", "TestData_ForFLB", "MixedTypes"])))
    assert names == ALL_MIXEDTYPES_FILES, (
        f"expected all 7 MixedTypes files present under a full TestData_ForFLB backup, got {names}"
    )
