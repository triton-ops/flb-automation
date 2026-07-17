"""NJM-185022 — [FLB v3] FLB Job Wizard - Inclusion + Exclusion - Overrule Example C (same
parameter in both -> excluded) (FLB-11/FLB-12). Original verdict (raw-RPC execution): PASS.

Verify: the same parameter set in BOTH Inclusion and Exclusion (data.bin) -> the item is
excluded (exclusion wins on a direct conflict). Matches the NAS Backup Confluence spec's own
"Example C": "Step 2 - Inclusion and Step 3 - Exclusion have the parameter 'Report.docx'. The
product shall exclude the files whose names are 'Report.docx' instead of including them." The
job is expected to succeed with an empty recovery point (data.bin was the only inclusion match,
and it's also excluded) rather than fail.
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

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185022")]


@allure.title("NJM-185022 — Overrule Example C: same parameter (data.bin) in both -> excluded")
def test_overrule_example_c(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-185022")
    build_flb_job(
        page, job_name, IE_WIZARD_DRILL, ["BinOverrule"],
        inclusion=["data.bin"], exclusion=["data.bin"],
    )
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job should succeed even with an empty item set, got {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["BinOverrule"])
    assert extract_item_names(rows) == [], (
        "data.bin should be excluded on direct conflict, leaving an empty recovery point, "
        f"got {extract_item_names(rows)}"
    )
