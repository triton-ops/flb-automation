r"""NJM-122672 / 122673 / 122644 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): item display with
fewer/more than 200 items, and general UI behavior with large item counts, in the 'Select Items'
dialog.

CALIBRATED live 2026-07-18: Subfolder_200Folders (under TestData_ForFLB on Window11) has 207 real
items on disk (confirmed via WinRM `Get-ChildItem | Measure-Object`) — a deterministic fixture,
unlike TestData_ForFLB's own top-level count which fluctuates as other suites create/clean up
AUTO_FLB_* fixtures concurrently. Opening it shows exactly the capped first-200 listing plus the
banner 'Showing the first 200 results. Try using Search to narrow your results.' — this is the
EXACT text from NJM-122673/122645's own Xray spec, confirmed real (not a documented gap) after
correcting an earlier same-day miscalibration that checked the wrong ambient folder.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

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


@allure.title("NJM-122672 — folder with fewer than 200 items lists them all, no banner")
@pytest.mark.jira("NJM-122672")
def test_item_display_fewer_than_200(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("SpecialFiles_ForFLB")  # this suite's own fixture: 13 items, well under 200
    flb.wait(800)
    names = [n for n in flb.picker_row_names() if n != "[..]"]
    assert 0 < len(names) < 200, f"expected a small item count, got {len(names)}: {names}"
    assert not flb.picker_over_200_message_shown(), "the >200 banner should NOT show for a small folder"
    flb.click_cancel()
    flb.click_cancel()


@allure.title("NJM-122673 — folder with more than 200 items shows the first-200-results banner")
@pytest.mark.jira("NJM-122673")
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


@allure.title("NJM-122644 — dialog stays responsive and renders correctly with a large item count")
@pytest.mark.jira("NJM-122644")
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
