"""NJM-182427 — [FLB v3] FLB Job Wizard - Step 3 Exclusion - Exclude all .pdf files [UC3]
(FLB-12). Original verdict (raw-RPC execution): PASS.

Verify that an Extension exclusion rule (*.pdf) excludes all .pdf files while backing up
everything else.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import IE_FLR_PREFIX, IE_WIZARD_DRILL, build_flb_job, flr_browse, extract_item_names, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-182427")]


@allure.title("NJM-182427 — Exclude all .pdf files [UC3]")
def test_exclude_all_pdf(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-182427")
    build_flb_job(page, job_name, IE_WIZARD_DRILL, ["MixedTypes"], exclusion=["*.pdf"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["MixedTypes"])
    found = extract_item_names(rows)
    assert "sample.docx" in found and "sample.jpg" in found, f"non-.pdf files should remain, got {found}"
    assert "sample.pdf" not in found, f".pdf files should be excluded, got {found}"
