r"""NJM-62728 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): folders, files, and the volume
itself are all selectable item types in the 'Select Items' dialog.

CALIBRATED live 2026-07-18 (see check_select_items_dialog.py).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-62728"),
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


@allure.title("NJM-62728 — folders, files, and the volume itself are all selectable item types")
def test_selection_of_various_item_types(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)

    # 1) A whole volume is selectable directly at the root listing.
    flb.click_force(SI.checkbox("Local Disk (C:)"))
    flb.wait(500)
    assert "1" in flb.picker_selected_count(), "selecting the volume itself should count as 1 selection"
    flb.click_force(SI.checkbox("Local Disk (C:)"))  # deselect before drilling in
    flb.wait(500)

    flb.picker_drill("Local Disk (C:)")
    flb.wait(800)

    # 2) A folder (TestData_ForFLB) is selectable.
    flb.click_force(SI.checkbox("TestData_ForFLB"))
    flb.wait(500)
    assert "1" in flb.picker_selected_count(), "selecting one folder should count as 1"
    flb.click_force(SI.checkbox("TestData_ForFLB"))  # deselect
    flb.wait(500)

    # 3) A FILE (not a folder) is selectable — SpecialFiles_ForFLB\Makefile (extensionless probe
    # file, this suite's own fixture, guaranteed to be a real file rather than a folder).
    flb.picker_drill("SpecialFiles_ForFLB")
    flb.wait(800)
    flb.click_force(SI.checkbox("Makefile"))
    flb.wait(500)
    assert "1" in flb.picker_selected_count(), "selecting one file should count as 1"

    page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
    flb.click_cancel()
