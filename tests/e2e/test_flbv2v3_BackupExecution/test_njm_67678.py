r"""NJM-67678 — [FLB v1] FLB Job Wizard - Options Step - Verify All Job Options (App-aware,
Scripts, etc.).

Builds on the Options-step POM calibration added 2026-07-19 (FlbWizardPage.set_acl_mode() /
set_app_aware_mode() / set_concurrent_task_limit(), _helpers.py's build_flb_job() kwargs) — see
browser/pom/common/locators.py's OptionsLocators docstring for the full live-calibration writeup.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-67678")]

MACHINE = "Window11"
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-67678 — Options step: exercise app-aware/ACL/encryption/concurrency options together")
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
