r"""NJM-182441 — [FLB v2] FLB Job Wizard - Source Step (UI): "Selected Items Expanded + Search
Results Over 200 Items" — the Selected Items panel stays expandable while viewing a >200-item
listing in the 'Select Items' dialog.

Since search doesn't filter this listing at all (see test_njm_63205.py and siblings), the exact
"search-produced >200 results" precondition can't be produced. The closest faithful, non-
fabricated reproduction is: expand the panel while VIEWING a >200-item listing reached by plain
navigation (not search) — both underlying states are independently real, so this is written as a
real test with the search-vs-navigation deviation stated honestly, not skipped.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-182441"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


def _open_picker(page) -> FlbWizardPage:
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)
    return flb


@allure.title("NJM-182441 — Selected Items panel stays expandable while viewing a >200-item listing")
def test_selected_items_expanded_with_over_200_listing(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.picker_drill("Subfolder_200Folders")
    flb.wait(1000)
    assert flb.picker_over_200_message_shown(), "precondition: this listing should show the >200 banner"

    names = [n for n in flb.picker_row_names() if n != "[..]"][:2]
    for n in names:
        flb.click_force(SI.checkbox(n))
    flb.wait(500)

    flb.picker_toggle_selected_items()
    assert flb.picker_selected_items_panel_expanded(), "panel should still expand correctly on a >200 listing"
    rows = flb.picker_selected_items_rows()
    listed_names = {r["name"] for r in rows}
    assert set(names) <= listed_names, f"expected {names} in the expanded panel, got {rows}"

    flb.click_cancel()
    flb.click_cancel()
