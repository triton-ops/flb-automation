"""NJM-182425 — [FLB v3] FLB Job Wizard - Step 2 Inclusion - Include files by file name (FLB-11).
Original verdict (raw-RPC execution): PASS.

Verify that a File-name inclusion rule (report*) backs up only files whose name matches, skipping
the rest. report* is a case-insensitive PREFIX match — Report_final.pdf matches (starts with
"Report"), Q1Report.docx does not (contains but doesn't start with it).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import IE_FLR_PREFIX, IE_WIZARD_DRILL, build_flb_job, flr_browse, extract_item_names, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-182425")]


@allure.title("NJM-182425 — Include files by file name (report*, case-insensitive prefix)")
def test_include_by_filename_prefix(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-182425")
    build_flb_job(page, job_name, IE_WIZARD_DRILL, ["ByName"], inclusion=["report*"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["ByName"])
    found = extract_item_names(rows)
    assert found == ["Report_final.pdf"], f"only the prefix-matching file should be present, got {found}"
