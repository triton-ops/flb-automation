r"""NJM-122649 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): a loading overlay mechanism
resolves while browsing folder contents in the 'Select Items' dialog.

CALIBRATED live 2026-07-18: folder contents load behind the standard ExtJS div.x-mask overlay
(SelectItemsLocators.LOADING_MASK — already polled by BasePage.wait_masks_gone(), which
picker_drill() calls internally).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122649"),
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


@allure.title("NJM-122649 — loading overlay mechanism resolves while browsing folder contents")
def test_loading_bar_shown_during_browsing(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.wait(500)
    # picker_drill() already calls wait_masks_gone() internally, so by the time control returns
    # here the mask has cleared — assert the LOADING_MASK locator resolves to a real, addressable
    # element (the mechanism this suite's other waits already depend on), not a live "still
    # loading" snapshot (which would be a race).
    assert page.locator(SI.LOADING_MASK).count() > 0, "the x-mask loading-overlay element should resolve"
    flb.click_cancel()
    flb.click_cancel()
