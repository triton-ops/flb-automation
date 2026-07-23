r"""NJM-185038 — [FLB v1] FLB Job Wizard - Source Step (UI): a sibling row is disabled with the
'Maximum selected items' tooltip once the 200-item cap is reached, in the 'Select Items' dialog.

CALIBRATED live 2026-07-18: once 200 items are selected in a folder, every other still-empty
selectable row in the PARENT folder shows a disabled checkbox with the tooltip 'Maximum selected
items were reached.'
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-185038"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@allure.title("NJM-185038 — a sibling row is disabled with the 'Maximum selected items' tooltip once capped")
def test_max_selected_items_tooltip(logged_in_page):
    page = logged_in_page
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.picker_drill("Subfolder_200Folders")
    flb.wait(1000)
    flb.picker_select_all()
    flb.picker_up_one_level()
    flb.wait(800)

    names = [n for n in flb.picker_row_names() if n not in ("[..]", "Subfolder_200Folders")]
    capped = next((n for n in names if flb.picker_row_tooltip(n) == SI.MAX_SELECTED_TOOLTIP), None)
    assert capped is not None, f"expected at least one sibling row disabled at the 200 cap, checked: {names[:10]}"
    assert flb.picker_row_disabled(capped), f"the tooltip-bearing row {capped!r} should also be disabled"

    flb.click_cancel()
    flb.click_cancel()
