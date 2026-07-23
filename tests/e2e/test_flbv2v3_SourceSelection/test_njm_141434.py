r"""NJM-141434 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): search bar / search controls in the
'Select Items' dialog.

CALIBRATED live 2026-07-18 (see check_select_items_dialog.py's SEARCH_INPUT/SEARCH_CLEAR
calibration and picker_search()'s docstring): the search INPUT and its clear/X control both work
correctly (typing reveals the clear control; clearing empties the box and hides it again) — but
typing into the box does NOT filter the folderInfoItem listing at all in this build (see
test_njm_63205.py and its 3 sibling skip-stubs for that documented gap). This TC covers only the
controls themselves, which work exactly as specified.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-141434"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@allure.title("NJM-141434 — search box accepts input and the clear control appears/clears reliably")
def test_search_input_and_clear_controls(logged_in_page):
    page = logged_in_page
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)

    assert not flb.picker_search_clear_visible(), "clear control should be hidden with an empty search box"
    flb.picker_search("TestData")
    assert flb.picker_search_clear_visible(), "clear control should appear once text is entered"
    flb.picker_clear_search()
    assert not flb.picker_search_clear_visible(), "clear control should hide again once the box is emptied"

    flb.click_cancel()
    flb.click_cancel()
