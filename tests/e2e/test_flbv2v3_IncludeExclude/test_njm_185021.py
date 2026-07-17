"""NJM-185021 — [FLB v3] FLB Job Wizard - Inclusion + Exclusion - Overrule Example B (include
keep.txt, exclude *.txt) (FLB-11/FLB-12). Original verdict (raw-RPC execution): PASS.

Verify: Include keep.txt (specific) + Exclude *.txt (wildcard) -> NO .txt files are backed up at
all, including keep.txt (the broader exclusion overrules the specific inclusion). Matches the
NAS Backup Confluence spec's own "Example B (Opposite to Example A)": "The product shall exclude
all files that have .txt extension, even the files whose names are 'Text.txt'/'text.txt'." The
job is expected to succeed with an empty recovery point rather than fail.
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

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185021")]


@allure.title("NJM-185021 — Overrule Example B: include keep.txt, exclude *.txt")
def test_overrule_example_b(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-185021")
    build_flb_job(
        page, job_name, IE_WIZARD_DRILL, ["TxtOverruleB"],
        inclusion=["keep.txt"], exclusion=["*.txt"],
    )
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job should succeed even with an empty item set, got {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["TxtOverruleB"])
    assert extract_item_names(rows) == [], (
        f"no .txt files (including the explicitly-included keep.txt) should be present, got {extract_item_names(rows)}"
    )
