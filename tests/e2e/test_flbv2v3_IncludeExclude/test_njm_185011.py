"""NJM-185011 — [FLB v3] FLB Job Wizard - Step 2 Inclusion - Include files by name wildcard
'*Report*' (FLB-11). Original verdict (raw-RPC execution): PASS.

Verify an inclusion rule using *Report* (wildcard both sides) backs up only names containing
"Report", regardless of position — unlike the prefix-only report* rule in NJM-182425, both
Q1Report.docx and Report_final.pdf match.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import IE_FLR_PREFIX, IE_WIZARD_DRILL, build_flb_job, flr_browse, extract_item_names, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185011")]


@allure.title("NJM-185011 — Include files by name wildcard '*Report*' (both sides)")
def test_include_by_wildcard_both_sides(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-185011")
    build_flb_job(page, job_name, IE_WIZARD_DRILL, ["ByName"], inclusion=["*Report*"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["ByName"])
    found = set(extract_item_names(rows))
    assert found == {"Q1Report.docx", "Report_final.pdf"}, (
        f"both Report-containing names should be present regardless of position, got {found}"
    )
