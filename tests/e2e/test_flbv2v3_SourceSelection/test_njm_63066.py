r"""NJM-63066 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): Cancel discards in-dialog selection
changes in the 'Select Items' dialog (does not commit them to the Source step's footer count).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-63066"),
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


@allure.title("NJM-63066 — Cancel discards in-dialog selection changes")
def test_cancel_discards_changes(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.click_force(SI.checkbox("ft_access"))
    flb.wait(500)
    assert "1" in flb.picker_selected_count(), "selection should register inside the dialog"

    page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
    flb.wait(800)

    # Reopen the picker fresh — the earlier selection should NOT have been committed.
    flb.open_item_picker()
    flb.wait(1000)
    count_after_reopen = flb.picker_selected_count()
    assert count_after_reopen.strip().endswith(": 0"), (
        f"Cancel should discard the in-dialog selection, but reopening shows: {count_after_reopen!r}"
    )
    page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
    flb.click_cancel()
