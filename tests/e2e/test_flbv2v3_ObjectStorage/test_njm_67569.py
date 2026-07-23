r"""NJM-67569 — [FLB v1] FLB Job Wizard - Destination Step - Verify Wasabi Repository is a
Supported Target.

Lightweight wizard-navigation check, NOT a full backup run: reach the Destination step, select
the repository, and confirm it's selectable without error. No job is ever Finished (Cancel out
after confirming selection succeeded) — this only proves the repository TYPE is offered/selectable
as a destination; the "does a real backup to it actually succeed" question is covered separately
by test_njm_123121.py.

⚠ KNOWN CURRENT ISSUE (found live 2026-07-22): the non-immutable `Wasabi_Repo` repository no
longer exists on nbr-84 — only `Wasabi-immutable` remains now (confirmed via the Destination
combo's live option list). This test will fail at `select_repository()` until this is resolved —
awaiting a decision, not yet fixed.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI

pytestmark = [
    pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-67569"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"
REPOSITORY = "Wasabi_Repo"


@allure.title("NJM-67569 — Wasabi_Repo is a selectable Destination-step target")
def test_wasabi_is_supported_target(logged_in_page):
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

    # select_repository() already asserts nothing itself — if the repo weren't selectable this
    # would raise a Playwright timeout, which is the real failure signal for this TC.
    flb.select_repository(REPOSITORY)
    flb.click_cancel()
