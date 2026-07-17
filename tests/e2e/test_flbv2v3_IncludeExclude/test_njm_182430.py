"""NJM-182430 — [FLB v3] FLB Job Wizard - Inclusion + Exclusion - Combined rules precedence.
Original verdict (raw-RPC execution): PASS.

Verify that when Inclusion (*.docx) and Exclusion (a specific .docx file) are both set,
exclusion takes precedence within the included set. Confirmed against the NAS Backup Confluence
spec's own "Workflow for Inclusion and Exclusion" section: "Exclusion shall have the right to
overrule Inclusion."
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

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-182430")]


@allure.title("NJM-182430 — Combined Inclusion + Exclusion rules precedence")
def test_combined_precedence(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-182430")
    build_flb_job(
        page, job_name, IE_WIZARD_DRILL, ["CombinedPrecedence"],
        inclusion=["*.docx"], exclusion=["draft.docx"],
    )
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["CombinedPrecedence"])
    found = set(extract_item_names(rows))
    assert found == {"report1.docx", "report2.docx"}, (
        f"all .docx present except draft.docx (exclusion overrules inclusion), got {found}"
    )
