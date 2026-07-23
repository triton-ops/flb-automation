r"""NJM-185039 — [FLB v1] FLB Job Wizard - Source Step (UI): a system folder's checkbox is disabled
with the 'System folder' tooltip in the 'Select Items' dialog.

CALIBRATED live 2026-07-18: a genuine system folder (e.g. 'Windows' under C:) is independently
disabled with the tooltip 'System folder is not supported.' regardless of the 200-item cap.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-185039"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@allure.title("NJM-185039 — a system folder's checkbox is disabled with the 'System folder' tooltip")
def test_system_folder_disabled_tooltip(logged_in_page):
    page = logged_in_page
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)
    flb.picker_drill("Local Disk (C:)")
    flb.wait(800)

    assert flb.picker_row_disabled("Windows"), "the 'Windows' system folder should be disabled"
    assert flb.picker_row_tooltip("Windows") == SI.SYSTEM_FOLDER_TOOLTIP, (
        f"expected the system-folder tooltip, got: {flb.picker_row_tooltip('Windows')!r}"
    )

    flb.click_cancel()
    flb.click_cancel()
