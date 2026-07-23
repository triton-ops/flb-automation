r"""NJM-67571 — [FLB v1] FLB Job Wizard - Destination Step - Verify Azure Blob Repository is a
Supported Target.

Lightweight wizard-navigation check, NOT a full backup run: reach the Destination step, select
the repository, and confirm it's selectable without error. No job is ever Finished (Cancel out
after confirming selection succeeded) — this only proves the repository TYPE is offered/selectable
as a destination; the "does a real backup to it actually succeed" question is covered separately
by test_njm_123119.py.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-67571"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"
REPOSITORY = "Azure_Repo"


@allure.title("NJM-67571 — Azure_Repo is a selectable Destination-step target")
def test_azure_is_supported_target(logged_in_page):
    page = logged_in_page
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()
    flb.wait(1500)
    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("SpecialFiles_ForFLB")
    flb.click_force(SI.checkbox("Makefile"))
    flb.wait(500)
    flb.picker_apply()
    flb.click_next()  # Inclusion
    flb.click_next()  # Exclusion
    flb.click_next()  # -> Destination

    flb.select_repository(REPOSITORY)
    flb.click_cancel()
