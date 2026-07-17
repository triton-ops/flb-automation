"""NJM-185020 — [FLB v3] FLB Job Wizard - Inclusion + Exclusion - Overrule Example A (include
*.txt, exclude Text.txt) (FLB-11/FLB-12). Original verdict (raw-RPC execution): PASS (verified
via byte-count — FLR browse hit the known RPC-built-Linux FLR-browse defect).

Verify: Include *.txt + Exclude Text.txt -> all .txt backed up EXCEPT Text.txt/text.txt
(case-insensitive matching, per the NAS Backup Confluence spec's own "Example A"), keep.doc not
included at all (never matched by the inclusion). Deliberately uses Linux (ext4, case-sensitive
filesystem) rather than Windows — NTFS is case-insensitive at the filesystem level, so Text.txt
and text.txt cannot coexist as two distinct files on Windows; Linux lets both genuinely exist, so
this actually exercises whether NBR's rule-matching is case-insensitive, not masked by filesystem
case-folding.

The original RPC-built job hit a known FLR-browse defect for Linux jobs. This UI-built job
attempts the FLR browse honestly rather than assuming that limitation carries over unchanged.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import (
    IE_LINUX_FLR_PREFIX,
    IE_LINUX_WIZARD_DRILL,
    LINUX_MACHINE,
    build_flb_job,
    extract_item_names,
    flr_browse,
    run_and_wait_flb_job,
)

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185020")]


@allure.title("NJM-185020 — Overrule Example A (Linux): include *.txt, exclude Text.txt")
def test_overrule_example_a_linux(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-185020")
    build_flb_job(
        page, job_name, IE_LINUX_WIZARD_DRILL, ["TxtOverruleA"],
        machine=LINUX_MACHINE, is_linux=True,
        inclusion=["*.txt"], exclusion=["Text.txt"],
    )
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_LINUX_FLR_PREFIX + ["TxtOverruleA"])
    found = extract_item_names(rows)
    assert found == ["other.txt"], (
        f"only other.txt should remain — both Text.txt/text.txt case-insensitively excluded, "
        f"keep.doc never matched *.txt, got {found}"
    )
