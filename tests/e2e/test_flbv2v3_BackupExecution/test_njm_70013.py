r"""NJM-70013 — [FLB v1/v2] FLB - Functional - Verify User Story: Backup Folders (US1).

Selects the MixedTypes folder specifically (not the machine root/other volumes) — proves
folder-level scoping, not whole-machine backup.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-70013")]

MACHINE = "Window11"
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-70013 — backup a specific folder, not the whole machine (US1)")
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
