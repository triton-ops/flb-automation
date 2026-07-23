r"""NJM-185036 — [FLB v1] FLB - Functional - 'Limit a concurrent task to N folders' field governs
folder parallelism.

⚠ SCOPE REDUCTION (see OptionsLocators' docstring in locators.py for the full live-calibration
writeup): NBR's UI has no visible per-folder timing/concurrency indicator, so "observe folder
processing" (the TC's own step 3) isn't something a UI-driven test can directly witness. This
test instead verifies the field accepts both a low (1) and high (8) value and that the job
completes successfully with all content backed up either way — proving the setting doesn't break
anything, not the actual concurrency behavior. Uses TestData_ForFLB itself (18 top-level
subfolders — Folder_test1/2/3, FolderEmpty_test4/5, 9× ft_*, Subfolder_200Folders,
Wilcard_Recheck — close to but not literally the TC's own '20+' example) rather than MixedTypes,
since the whole point is a source with many subfolders.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-185036")]

MACHINE = "Window11"
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-185036 — 'Limit a concurrent task to N folders' accepts low and high values")
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
