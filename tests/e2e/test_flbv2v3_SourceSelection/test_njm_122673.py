r"""NJM-122673 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): a folder with more than 200 items
shows the first-200-results banner in the 'Select Items' dialog.

CALIBRATED live 2026-07-18: Subfolder_200Folders (under TestData_ForFLB on Window11) has 207 real
items on disk (confirmed via WinRM `Get-ChildItem | Measure-Object`) — a deterministic fixture,
unlike TestData_ForFLB's own top-level count which fluctuates as other suites create/clean up
AUTO_FLB_* fixtures concurrently. Opening it shows exactly the capped first-200 listing plus the
banner 'Showing the first 200 results. Try using Search to narrow your results.' — this is the
EXACT text from this TC's own Xray spec, confirmed real (not a documented gap) after correcting an
earlier same-day miscalibration that checked the wrong ambient folder.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122673"),
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


@allure.title("NJM-122673 — folder with more than 200 items shows the first-200-results banner")
def test_item_display_more_than_200(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.picker_drill("Subfolder_200Folders")
    flb.wait(1000)
    names = [n for n in flb.picker_row_names() if n != "[..]"]
    assert len(names) == 200, f"listing should cap display at 200 rows, got {len(names)}"
    assert flb.picker_over_200_message_shown(), "expected the 'first 200 results' banner"
    flb.click_cancel()
    flb.click_cancel()
