"""NJM-182428 — [FLB v3] FLB Job Wizard - Step 3 Exclusion - Exclude files by file name
(FLB-12). Original verdict (raw-RPC execution): PASS.

Verify that a File-name exclusion rule (*tmp*) excludes matching files, keeping the rest.
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

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-182428")]


@allure.title("NJM-182428 — Exclude files by file name (*tmp*)")
def test_exclude_by_filename(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-182428")
    build_flb_job(page, job_name, IE_WIZARD_DRILL, ["NameExclude"], exclusion=["*tmp*"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["NameExclude"])
    found = extract_item_names(rows)
    assert found == ["notes.txt"], f"only the non-matching file should remain, got {found}"
