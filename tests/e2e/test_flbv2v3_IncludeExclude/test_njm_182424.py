"""NJM-182424 — [FLB v3] FLB Job Wizard - Step 2 Inclusion - Include files by extension (FLB-11).
Original verdict (raw-RPC execution): PASS.

Verify that adding an Extension inclusion rule (*.docx) on Step 2 - Inclusion backs up only files
matching that extension, skipping everything else.

CALIBRATED live 2026-07-16: browsing INTO a folder matched by an active Inclusion filter (a
distinct "gear" icon renders on it in the left tree) needs FileLevelRecoveryPage's right-panel
navigation fix — see _drill_left_tree()'s docstring in
browser/pom/backup_types/file_level_recovery_page.py. An earlier pass here mistakenly concluded
this was the same product defect as NJM-182426's nested-folder FLR-browse limitation; it was
actually a POM navigation/timing bug (reading the listing during an async load, and selecting
via the wrong element) — fixed in the POM, not worked around here.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import IE_FLR_PREFIX, IE_WIZARD_DRILL, build_flb_job, flr_browse, extract_item_names, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-182424")]


@allure.title("NJM-182424 — Include files by extension (*.docx)")
def test_include_by_extension(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-182424")
    build_flb_job(page, job_name, IE_WIZARD_DRILL, ["MixedTypes"], inclusion=["*.docx"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["MixedTypes"])
    found = extract_item_names(rows)
    assert found == ["sample.docx"], (
        f"FLR browse into MixedTypes should show only sample.docx (non-.docx files excluded by "
        f"the inclusion filter), got {found}"
    )
