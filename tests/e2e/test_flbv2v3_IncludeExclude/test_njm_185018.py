"""NJM-185018 — [FLB v3] FLB Job Wizard - Step 2/3 - Unicode characters supported (FLB-11/FLB-12).
Original verdict (raw-RPC execution): PASS.

Verify Unicode characters (accented Latin + CJK) are accepted in an Exclusion rule and filter as
intended when the job runs. Original RPC-driven investigation found that FLR browse INTO the
nested folder 文件夹 returns empty (the same nested-folder FLR-browse limitation documented for
NJM-182426, this time under an Exclusion-only filter) — verified via byte-count there instead.
This UI-driven port attempts the FLR browse honestly rather than assuming that limitation
carries over unchanged from the RPC-built path.
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

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185018")]


@allure.title("NJM-185018 — Unicode characters supported in Exclusion")
def test_unicode_exclusion(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-185018")
    build_flb_job(page, job_name, IE_WIZARD_DRILL, ["Unicode"], exclusion=["日本語ファイル.txt"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["Unicode"])
    found = extract_item_names(rows)
    assert "café_résumé.txt" in found, f"café_résumé.txt should be present, got {found}"
    assert "文件夹" in found, f"文件夹 folder should be present, got {found}"
    assert "日本語ファイル.txt" not in found, f"日本語ファイル.txt should be excluded, got {found}"
