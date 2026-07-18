r"""NJM-62788 / 63061 / 122655 / 122654 / 122642 — [FLB v1/v2] FLB Job Wizard - Source Step (UI):
dialog open behavior, volume-view default, title, and general layout/elements of the 'Select
Items' dialog.

Pure UI-state checks — no job is built (matches check_select_items_dialog.py's own convention:
open the wizard, open the picker, assert, cancel out). CALIBRATED live 2026-07-18 against nbr-84 /
Window11 (see browser/checks/check_select_items_dialog.py, the same live pass this suite's POM
additions came from — SelectItemsLocators / FlbWizardPage.picker_*). All 5 rows share one body:
open the picker on a machine and assert the same set of structural facts (dialog opens, default
listing is a volume, correct title, and its core elements — search/breadcrumb/list-header/footer/
Apply-Cancel — are all present). 122654 and 122642 are duplicate "general layout" TCs (FLB v2 vs
v1 revisions of the same coverage) so they parametrize alongside the other three rather than
duplicating the body.
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


DIALOG_TCS = [
    pytest.param("NJM-62788", marks=pytest.mark.jira("NJM-62788"), id="NJM-62788-opens-on-selection"),
    pytest.param("NJM-63061", marks=pytest.mark.jira("NJM-63061"), id="NJM-63061-defaults-volume-view"),
    pytest.param("NJM-122655", marks=pytest.mark.jira("NJM-122655"), id="NJM-122655-title"),
    pytest.param("NJM-122654", marks=pytest.mark.jira("NJM-122654"), id="NJM-122654-general-layout"),
    pytest.param("NJM-122642", marks=pytest.mark.jira("NJM-122642"), id="NJM-122642-dialog-layout"),
]


@pytest.mark.parametrize("jira_id", DIALOG_TCS)
def test_dialog_opens_with_correct_layout(logged_in_page, jira_id):
    allure.dynamic.title(f"{jira_id} — 'Select Items' dialog opens with title, volume default, core elements")
    page = logged_in_page
    flb = _open_picker(page)

    assert flb.picker_dialog_open(), "dialog did not open on machine selection"
    assert flb.picker_title().strip().lower() == "select items", f"unexpected title: {flb.picker_title()!r}"

    names = flb.picker_row_names()
    assert "Local Disk (C:)" in names, f"dialog did not default to volume view: {names}"
    assert not flb.picker_up_one_level_present(), "an Up-One-Level row should not appear at volume root"

    # Core elements: search box, breadcrumb bar (root icon), list header (via row names being
    # readable at all), footer selection count, and Apply/Cancel controls.
    assert page.locator(SI.SEARCH_INPUT).locator("visible=true").count() > 0, "search input missing"
    assert page.locator(SI.BREADCRUMB_ROOT).locator("visible=true").count() > 0, "breadcrumb root icon missing"
    assert "selected for" in flb.picker_selected_count().lower(), "footer selection count missing"
    assert page.locator(SI.CANCEL).locator("visible=true").count() > 0, "Cancel button missing"
    assert page.locator(SI.APPLY).locator("visible=true").count() > 0, "Apply button missing"

    page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
    flb.click_cancel()
