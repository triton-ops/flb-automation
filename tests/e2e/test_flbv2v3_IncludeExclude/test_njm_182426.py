"""NJM-182426 — [FLB v3] FLB Job Wizard - Step 2 Inclusion - Include files by path (FLB-11).
Original verdict (raw-RPC execution): FAIL — the original investigation attributed this to FLR's
directory listing returning empty for nested-subfolder content whenever the job's Inclusion
filter is active (confirmed across 5 raw-RPC-built job variants — see
cases/FLBv2v3_IncludeExclude/NJM-182426.md).

CALIBRATED live 2026-07-16: this UI-driven re-run PASSES. The real root cause of the empty
listing turned out to be a POM bug in FileLevelRecoveryPage — RIGHT_PANEL_ROW only matched
folder rows (class `flrGridContainer`), silently missing every file row, plus a premature read
during an async load. Both are fixed in browser/pom/backup_types/file_level_recovery_page.py
(see test_njm_182424.py, where this was first isolated and fixed). Include-by-path itself works
correctly; the original FAIL verdict was a verification-tooling defect, not a product defect.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import IE_FLR_PREFIX, IE_WIZARD_DRILL, build_flb_job, flr_browse, extract_item_names, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-182426")]


@allure.title("NJM-182426 — Include files by path")
def test_include_by_path(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-182426")
    build_flb_job(page, job_name, IE_WIZARD_DRILL, ["PathTest"], inclusion=["A\\*"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    top = flr_browse(page, job_name, IE_FLR_PREFIX + ["PathTest"])
    top_names = extract_item_names(top)
    assert top_names == ["A"], f"only subfolder A should appear at the PathTest root, got {top_names}"

    inside_a = flr_browse(page, job_name, IE_FLR_PREFIX + ["PathTest", "A"])
    assert extract_item_names(inside_a) == ["file_a.txt"], (
        f"FLR browse into subfolder A should show file_a.txt — got {extract_item_names(inside_a)}. If this "
        f"comes back empty, that reproduces the known FLR-browse-under-active-Inclusion-filter "
        f"defect documented in cases/FLBv2v3_IncludeExclude/NJM-182426.md, not a test bug."
    )
