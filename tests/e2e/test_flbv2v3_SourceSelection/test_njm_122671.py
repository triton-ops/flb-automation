r"""NJM-122671 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): the Cancel button in the 'Select
Items' dialog is present and closes the dialog.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122671"),
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


@allure.title("NJM-122671 — Cancel button is present and closes the dialog")
def test_cancel_button(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    assert page.locator(SI.CANCEL).locator("visible=true").count() > 0, "Cancel button should be present"
    page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
    flb.wait(500)
    assert not flb.picker_dialog_open(), "dialog should close after Cancel"
    flb.click_cancel()
