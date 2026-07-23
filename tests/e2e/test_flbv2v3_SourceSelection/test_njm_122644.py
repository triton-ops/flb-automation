r"""NJM-122644 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): the 'Select Items' dialog stays
responsive and renders correctly with a large item count.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122644"),
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


@allure.title("NJM-122644 — dialog stays responsive and renders correctly with a large item count")
def test_large_item_count_ui_responsiveness(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.picker_drill("Subfolder_200Folders")
    flb.wait(1000)
    # "Renders correctly and stays responsive" — assert the dialog is still open and interactive
    # (title readable, Apply/Cancel still respond) rather than hung/frozen after a large render.
    assert flb.picker_dialog_open(), "dialog should remain open after loading a large listing"
    assert flb.picker_title().strip().lower() == "select items", "title should still read correctly"
    assert flb.picker_apply_enabled(), "Apply should remain interactive after a large render"
    flb.click_cancel()
    flb.click_cancel()
