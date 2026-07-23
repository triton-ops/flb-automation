r"""NJM-185037 — [FLB v1] FLB Job Wizard - Source Step (UI): 'Select all' respects the 200-item cap
in the 'Select Items' dialog.

CALIBRATED live 2026-07-18 (see check_select_items_dialog.py): 'Select all' in a 200+-item folder
(Subfolder_200Folders, 207 real items on disk) selects exactly 200 and stops.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-185037"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@allure.title("NJM-185037 — Select-all respects the 200 cap")
def test_select_all_stops_at_200_cap(logged_in_page):
    page = logged_in_page
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.picker_drill("Subfolder_200Folders")
    flb.wait(1000)

    flb.picker_select_all()
    count = flb.picker_selected_count()
    assert count.strip().endswith("200"), f"Select-all should cap at 200 (Select-all respects the 200 cap): {count!r}"

    flb.click_cancel()
    flb.click_cancel()
