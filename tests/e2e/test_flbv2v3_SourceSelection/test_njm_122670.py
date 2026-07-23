r"""NJM-122670 — [FLB v1/v2] FLB Job Wizard - Source Step (UI): the Apply button in the 'Select
Items' dialog is present and interactive.

CALIBRATED live 2026-07-18: Apply carries no 'x-btn-disabled' class even with nothing selected in
this build (the 'select at least one item' gate is enforced by the Source step itself when
advancing past it — see NJM-62756 — not by disabling the dialog's own Apply).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-122670"),
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


@allure.title("NJM-122670 — Apply button is present and interactive")
def test_apply_button(logged_in_page):
    page = logged_in_page
    flb = _open_picker(page)
    assert page.locator(SI.APPLY).locator("visible=true").count() > 0, "Apply button should be present"
    assert flb.picker_apply_enabled(), "Apply should be enabled/interactive"
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.click_force(SI.checkbox("ft_access"))
    flb.wait(500)
    flb.picker_apply()
    # Applying should close the dialog and reflect the pick on the Source step.
    assert not flb.picker_dialog_open(), "dialog should close after Apply"
    flb.click_cancel()
