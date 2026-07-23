r"""NJM-122642 — [FLB v1] FLB Job Wizard - Source Step (UI): 'Select Items' dialog layout.

Pure UI-state check — no job is built. See test_njm_62788.py's module docstring for the shared
calibration note (identical body across this suite's 5 dialog-open/layout TCs; this TC and
NJM-122654 are duplicate "general layout" TCs — FLB v1 vs v2 revisions of the same coverage).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122642"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@allure.title("NJM-122642 — 'Select Items' dialog opens with title, volume default, core elements")
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
