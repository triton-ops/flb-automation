"""NJM-185012 — [FLB v3] FLB Job Wizard - Step 3 Exclusion - Exclude by extension wildcard
'*.csv' (FLB-12). Original verdict (raw-RPC execution): PASS.

Verify an exclusion rule *.csv excludes all .csv files, keeping non-.csv files.
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

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185012")]


@allure.title("NJM-185012 — Exclude by extension wildcard '*.csv'")
def test_exclude_by_extension_wildcard(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-185012")
    build_flb_job(page, job_name, IE_WIZARD_DRILL, ["CsvTest"], exclusion=["*.csv"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["CsvTest"])
    found = set(extract_item_names(rows))
    assert found == {"a.docx", "b.pdf"}, f"only non-.csv files should remain, got {found}"
