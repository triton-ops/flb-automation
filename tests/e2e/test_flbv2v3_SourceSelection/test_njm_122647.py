r"""NJM-122647 — [FLB v2] FLB Job Wizard - Source Step (UI): the 'Selected Items' Show/Hide
expansion panel in the 'Select Items' dialog expands a Name/Path list of the current selection.

RE-CALIBRATED live 2026-07-18: the dialog DOES have a working Show/Hide toggle that expands a real
ExtJS grid (Name/Path columns, one row per selection) — this corrects an earlier same-day
miscalibration that checked the wrong CSS class (borrowed from the FLR wizard) and wrongly
concluded no such panel existed. See SelectItemsLocators.SELECTED_ITEMS_TOGGLE/GRID's docstring.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122647"),
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


@allure.title("NJM-122647 — Selected Items Show/Hide expands a Name/Path list of the current selection")
def test_selected_items_view_and_expansion(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.wait(800)

    names = [n for n in flb.picker_row_names() if n != "[..]"][:2]
    for n in names:
        flb.click_force(SI.checkbox(n))
    flb.wait(500)

    assert not flb.picker_selected_items_panel_expanded(), "panel should start collapsed"
    flb.picker_toggle_selected_items()
    assert flb.picker_selected_items_panel_expanded(), "Show should expand the panel"

    rows = flb.picker_selected_items_rows()
    listed_names = {r["name"] for r in rows}
    assert set(names) <= listed_names, f"expected {names} in the expanded panel, got {rows}"

    flb.picker_toggle_selected_items()
    assert not flb.picker_selected_items_panel_expanded(), "Hide should collapse the panel again"

    flb.click_cancel()
    flb.click_cancel()
