r"""NJM-62728 / 122643 / 63184 / 122656 / 63185 — [FLB v1/v2] FLB Job Wizard - Source Step (UI):
folder/file navigation, Up One Level, and breadcrumb accuracy in the 'Select Items' dialog.

CALIBRATED live 2026-07-18 (see check_select_items_dialog.py). Each test drills from the volume
root into TestData_ForFLB and asserts the resulting navigation state — breadcrumb text, Up-One-
Level presence, and (for NJM-62728) that folders, files, and the volume itself are all tickable
item types via the same select_items() call the rest of this suite already relies on.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection,
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


@allure.title("NJM-122643 / NJM-63184 — folder navigation drills in, Up One Level navigates back out")
@pytest.mark.jira("NJM-122643")
@pytest.mark.jira("NJM-63184")
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


@allure.title("NJM-122656 / NJM-63185 — breadcrumb reflects the current path accurately")
@pytest.mark.jira("NJM-122656")
@pytest.mark.jira("NJM-63185")
def test_breadcrumb_path_accuracy(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)

    flb.picker_drill("Local Disk (C:)")
    flb.wait(800)
    crumb_c = flb.picker_breadcrumb_text()
    assert "C:" in crumb_c, f"breadcrumb should show C: after drilling into the volume: {crumb_c!r}"

    flb.picker_drill("TestData_ForFLB")
    flb.wait(800)
    crumb_deeper = flb.picker_breadcrumb_text()
    assert "TestData_ForFLB" in crumb_deeper, f"breadcrumb should include the deeper segment: {crumb_deeper!r}"
    assert "C:" in crumb_deeper, f"breadcrumb should retain the earlier segment too: {crumb_deeper!r}"

    # Clicking the earlier 'C:' segment should navigate back up to it directly (not just Up One Level).
    flb.picker_breadcrumb_click("C:")
    names_after_crumb_click = flb.picker_row_names()
    assert "TestData_ForFLB" in names_after_crumb_click, (
        f"clicking the C: breadcrumb segment should return to C:'s own listing: {names_after_crumb_click}"
    )

    page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
    flb.click_cancel()


@allure.title("NJM-62728 — folders, files, and the volume itself are all selectable item types")
@pytest.mark.jira("NJM-62728")
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
