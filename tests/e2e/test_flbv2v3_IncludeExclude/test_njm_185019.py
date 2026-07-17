"""NJM-185019 — [FLB v3] FLB Job Wizard - Step 3 Exclusion - Foreign-language folder names
(Arabic, Chinese, Korean, Russian) (FLB-12). Original verdict (raw-RPC execution): PASS.

Verify Exclusion rules using foreign-language folder names/paths are accepted, displayed
correctly, and the named folders are excluded from the backup — bare folder name exclusion
behaves the same as the plain-ASCII case (NJM-182429): the excluded folder disappears from the
tree entirely rather than just emptying.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import (
    IE_FLR_PREFIX,
    IE_WIZARD_DRILL,
    build_flb_job,
    extract_item_names,
    flr_browse,
    run_and_wait_flb_job,
)

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185019")]

_FOREIGN_FOLDERS = ["مجلد_عربي", "中文文件夹", "한국어_폴더", "Русская_папка"]


@allure.title("NJM-185019 — Exclude foreign-language folder names (Arabic, Chinese, Korean, Russian)")
def test_exclude_foreign_folder_names(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-185019")
    build_flb_job(page, job_name, IE_WIZARD_DRILL, ["ForeignFolders"], exclusion=_FOREIGN_FOLDERS)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["ForeignFolders"])
    found = extract_item_names(rows)
    assert found == ["keep.txt"], (
        f"only keep.txt should remain; all 4 foreign-language folders should be absent entirely, got {found}"
    )
