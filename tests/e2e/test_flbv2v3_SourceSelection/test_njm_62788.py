r"""NJM-62788 — [FLB v1] FLB Job Wizard - Source Step (UI): 'Select Items' dialog opens on machine
selection.

Pure UI-state check — no job is built (matches check_select_items_dialog.py's own convention:
open the wizard, open the picker, assert, cancel out). CALIBRATED live 2026-07-18 against nbr-84 /
Window11 (see browser/checks/check_select_items_dialog.py, the same live pass this suite's POM
additions came from — SelectItemsLocators / FlbWizardPage.picker_*).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-62788"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@allure.title("NJM-62788 — 'Select Items' dialog opens with title, volume default, core elements")
def test_dialog_opens_with_correct_layout(logged_in_page):
    page = logged_in_page
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)

    assert flb.picker_dialog_open(), "dialog did not open on machine selection"
    assert flb.picker_title().strip().lower() == "select items", f"unexpected title: {flb.picker_title()!r}"

    names = flb.picker_row_names()
    assert "Local Disk (C:)" in names, f"dialog did not default to volume view: {names}"
    assert not flb.picker_up_one_level_present(), "an Up-One-Level row should not appear at volume root"

    assert page.locator(SI.SEARCH_INPUT).locator("visible=true").count() > 0, "search input missing"
    assert page.locator(SI.BREADCRUMB_ROOT).locator("visible=true").count() > 0, "breadcrumb root icon missing"
    assert "selected for" in flb.picker_selected_count().lower(), "footer selection count missing"
    assert page.locator(SI.CANCEL).locator("visible=true").count() > 0, "Cancel button missing"
    assert page.locator(SI.APPLY).locator("visible=true").count() > 0, "Apply button missing"

    page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
    flb.click_cancel()
