r"""NJM-70016 — [FLB v1/v2] FLB - Functional - Verify User Story: Backup Specific Individual Files
(US4).

Selects two INDIVIDUAL FILES inside MixedTypes (not the whole folder) — the recovery point must
contain only those two, not the other five.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-70016")]

MACHINE = "Window11"
DRILL_TO_MIXEDTYPES = ["Local Disk (C:)", "TestData_ForFLB", "MixedTypes"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-70016 — backup specific individual files, not whole folders (US4)")
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
