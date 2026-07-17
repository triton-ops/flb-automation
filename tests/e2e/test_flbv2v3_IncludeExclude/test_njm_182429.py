"""NJM-182429 — [FLB v3] FLB Job Wizard - Step 3 Exclusion - Exclude files by path (FLB-12).
Original verdict (raw-RPC execution): PASS.

Verify that a Path exclusion rule scoped to one subfolder skips everything under that path while
backing up the rest of the parent folder. Uses the bare folder name `temp` (no path prefix, no
wildcard) — per the original investigation, a full absolute-path pattern risks issues (see
NJM-182426), and the bare name proved sufficient: Exclusion by bare folder name removes the
excluded subfolder ENTIRELY from the FLR tree (unlike Inclusion, which only matches the top-level
name but leaves it empty of nested content — the NJM-182426 FLR-browse defect), so this TC's
verification never needs to browse into a nested folder.
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

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-182429")]


@allure.title("NJM-182429 — Exclude files by path (bare folder name)")
def test_exclude_by_path(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-182429")
    build_flb_job(page, job_name, IE_WIZARD_DRILL, ["WithTemp"], exclusion=["temp"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["WithTemp"])
    found = extract_item_names(rows)
    assert found == ["keep.txt"], (
        f"only keep.txt should remain; the excluded 'temp' subfolder should be absent entirely, got {found}"
    )
