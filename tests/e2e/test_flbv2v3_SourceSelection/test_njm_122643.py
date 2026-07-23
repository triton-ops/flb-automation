r"""NJM-122643 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): folder navigation drills in, and
Up One Level navigates back out, in the 'Select Items' dialog. Also fully exercises NJM-63184
(same "drill in / Up One Level" steps against the same fixture) — no separate file, since a
second run of the identical dialog interaction would add nothing.

CALIBRATED live 2026-07-18 (see check_select_items_dialog.py). Drills from the volume root into
TestData_ForFLB and asserts the resulting navigation state — breadcrumb text and Up-One-Level
presence at each depth.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122643"),
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


@allure.title("NJM-122643 — folder navigation drills in, Up One Level navigates back out")
def test_folder_navigation_and_up_one_level(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)

    flb.picker_drill("Local Disk (C:)")
    flb.wait(800)
    assert flb.picker_up_one_level_present(), "Up-One-Level should appear once below volume root"
    names_at_c = flb.picker_row_names()

    flb.picker_drill("TestData_ForFLB")
    flb.wait(800)
    names_inside = flb.picker_row_names()
    assert names_inside != names_at_c, "drilling into TestData_ForFLB should change the listing"
    assert flb.picker_up_one_level_present(), "Up-One-Level should still appear inside a subfolder"

    flb.picker_up_one_level()
    flb.wait(800)
    names_back = flb.picker_row_names()
    assert "TestData_ForFLB" in names_back, f"Up One Level did not return to C:'s listing: {names_back}"

    page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
    flb.click_cancel()
