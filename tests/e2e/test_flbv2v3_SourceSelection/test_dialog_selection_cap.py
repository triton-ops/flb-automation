r"""NJM-122648 / 185037 / 185038 / 185039 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): the
200-item selection cap, its 'Select all' behavior, its tooltip, and the system-folder-disabled
tooltip in the 'Select Items' dialog.

CALIBRATED live 2026-07-18 (see check_select_items_dialog.py): 'Select all' in a 200+-item folder
(Subfolder_200Folders, 207 real items on disk) selects exactly 200 and stops; every other,
still-empty selectable row in the PARENT folder then shows a disabled checkbox with the tooltip
'Maximum selected items were reached.'; a genuine system folder (e.g. 'Windows' under C:) is
independently disabled with the tooltip 'System folder is not supported.' regardless of the
200-item cap.
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


CAP_BEHAVIOR_TCS = [
    pytest.param("NJM-122648", "UI behavior at the 200 max", marks=pytest.mark.jira("NJM-122648"),
                 id="NJM-122648-max-selection-limit"),
    pytest.param("NJM-185037", "Select-all respects the 200 cap", marks=pytest.mark.jira("NJM-185037"),
                 id="NJM-185037-select-all-cap"),
]


@pytest.mark.parametrize("jira_id,label", CAP_BEHAVIOR_TCS)
def test_select_all_stops_at_200_cap(logged_in_page, jira_id, label):
    allure.dynamic.title(f"{jira_id} — {label}")
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.picker_drill("Subfolder_200Folders")
    flb.wait(1000)

    flb.picker_select_all()
    count = flb.picker_selected_count()
    assert count.strip().endswith("200"), f"Select-all should cap at 200 ({label}): {count!r}"

    flb.click_cancel()
    flb.click_cancel()


@allure.title("NJM-185038 — a sibling row is disabled with the 'Maximum selected items' tooltip once capped")
@pytest.mark.jira("NJM-185038")
def test_max_selected_items_tooltip(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.picker_drill("Subfolder_200Folders")
    flb.wait(1000)
    flb.picker_select_all()
    flb.picker_up_one_level()
    flb.wait(800)

    names = [n for n in flb.picker_row_names() if n not in ("[..]", "Subfolder_200Folders")]
    capped = next((n for n in names if flb.picker_row_tooltip(n) == SI.MAX_SELECTED_TOOLTIP), None)
    assert capped is not None, f"expected at least one sibling row disabled at the 200 cap, checked: {names[:10]}"
    assert flb.picker_row_disabled(capped), f"the tooltip-bearing row {capped!r} should also be disabled"

    flb.click_cancel()
    flb.click_cancel()


@allure.title("NJM-185039 — a system folder's checkbox is disabled with the 'System folder' tooltip")
@pytest.mark.jira("NJM-185039")
def test_system_folder_disabled_tooltip(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.wait(800)

    assert flb.picker_row_disabled("Windows"), "the 'Windows' system folder should be disabled"
    assert flb.picker_row_tooltip("Windows") == SI.SYSTEM_FOLDER_TOOLTIP, (
        f"expected the system-folder tooltip, got: {flb.picker_row_tooltip('Windows')!r}"
    )

    flb.click_cancel()
    flb.click_cancel()
