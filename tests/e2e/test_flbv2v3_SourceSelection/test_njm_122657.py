r"""NJM-122657 — [FLB v2] FLB Job Wizard - Source Step (UI) - Verify Breadcrumb Truncation in
'Select Items' Dialog.

DOCUMENTED GAP, not faked — CALIBRATED live 2026-07-18 (see check_select_items_dialog.py's
BREADCRUMB_BAR calibration and its own docstring): 3 levels deep (C: / TestData_ForFLB /
Subfolder_200Folders), every segment rendered in full — no ellipsis/overflow truncation was
observed. Reproducing genuine truncation would need a MUCH deeper path than any fixture in this
suite currently has (this suite's own MaxPathTest_ForFLB gets a single FILE path to 259 chars via
5 nested 44-char folders — but the breadcrumb only needs to render FOLDER NAME segments, and 5
segments of 44 chars each did not overflow the 640px-wide dialog in practice during calibration).
Skipped rather than asserting a fabricated pass; unskip if a future build's dialog width changes
or a deeper fixture is seeded specifically for this case.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122657"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@pytest.mark.skip(
    reason="BLOCKED: breadcrumb truncation not reproducible with any fixture in this suite — "
    "calibrated live 2026-07-18 through 5 nested 44-char folder segments (MaxPathTest_ForFLB) with "
    "no overflow observed. Written and executable; unskip if a deeper fixture is seeded."
)
@allure.title("NJM-122657 — breadcrumb truncates on a very deep path")
def test_breadcrumb_truncation(logged_in_page):
    page = logged_in_page
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("MaxPathTest_ForFLB")
    for _ in range(5):
        names = [n for n in flb.picker_row_names() if n != "[..]"]
        if not names:
            break
        flb.picker_drill(names[0])
        flb.wait(500)
    crumb = flb.picker_breadcrumb_text()
    assert "…" in crumb or "..." in crumb, f"expected a truncation ellipsis in a deep breadcrumb: {crumb!r}"
    flb.click_cancel()
    flb.click_cancel()
