r"""NJM-70018 — [FLB v1/v2] FLB - Functional - Verify Full Workflow (Create, Run, Recover, Delete
Job).

Builds+runs+recovers (browse-only, no original-location overwrite needed since the TC only asks to
confirm recovered content matches source) then explicitly deletes the job and asserts it's gone
from the Jobs sidebar — flb_job_cleanup's teardown would otherwise do this same delete silently at
test end, but this TC's own steps call for verifying the deletion as part of the test itself, so
it's done inline here instead.

NJM-70015 (US3 — recover accidentally-deleted files to their ORIGINAL location) is NOT covered
here: recovering to the original location is an execute-not-just-browse action gated by this
project's safety rules (see CLAUDE.md and suite F's NJM-182724, which owns this exact scenario) —
must ask the user before ever executing an original-location recovery. Deferred to suite F rather
than duplicated with a scope-reduced substitute here.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.job_management_page import JobManagementPage
from browser.pom.common.locators import DataProtectionLocators

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-70018")]

MACHINE = "Window11"
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-70018 — full workflow: create, run, recover, delete job")
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
