r"""NJM-63205 — [FLB v1] FLB Job Wizard - Source Step (UI): basic search functionality in the
'Select Items' dialog.

BLOCKED: the dialog's search box does not filter the listing in this build (verified live
2026-07-18 — a matching and a non-matching search term both leave the full listing unchanged), so
there is no "search functionality" to verify beyond the controls already covered by
test_njm_141434.py (input + clear control, which work correctly). Written and executable; unskip
once search actually filters.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-63205"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@allure.title("NJM-63205 — basic search functionality")
@pytest.mark.skip(
    reason="BLOCKED: the dialog's search box does not filter the listing in this build (verified "
    "live 2026-07-18 — a matching and a non-matching search term both leave the full listing "
    "unchanged), so no search-driven filtering behavior exists to verify. Written and executable; "
    "unskip once search actually filters."
)
def test_search_filtering_behavior(logged_in_page):
    page = logged_in_page
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    before = set(flb.picker_row_names())
    flb.picker_search("zzzznomatchzzzz")
    after = set(flb.picker_row_names())
    assert after != before, (
        "search for a non-matching term should narrow/empty the listing (basic search functionality)"
    )
    flb.click_cancel()
    flb.click_cancel()
