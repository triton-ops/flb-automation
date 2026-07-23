r"""NJM-122656 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): the breadcrumb reflects the current
path accurately in the 'Select Items' dialog. Also fully exercises NJM-63185 (same breadcrumb-
accuracy steps against the same fixture) — no separate file, since a second run of the identical
dialog interaction would add nothing.

CALIBRATED live 2026-07-18 (see check_select_items_dialog.py).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122656"),
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


@allure.title("NJM-122656 — breadcrumb reflects the current path accurately")
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
