r"""NJM-62756 — [FLB v1] FLB Job Wizard - Validation - Allow Proceeding When at Least One Item is
Selected.

Per the TC's Xray steps: select the physical machine, select exactly one item in the 'Select
Items' dialog, Apply, then click Next — the wizard should advance without a validation error.
(The TC's own text says "advances to Step 2 - Destination", reflecting the OLD 2-step Source/
Destination wizard layout that WizardLocators' own docstring notes is gone — the current NBR
11.2.1 wizard has SIX steps, so "advances past Source with no validation error" is the TC's real,
still-valid intent; three click_next() calls are needed to actually reach Destination, matching
build_flb_job()'s own established Source->Inclusion->Exclusion->Destination pattern.)

VERIFIED LIVE 2026-07-18: an initial version of this test called click_next() only once and then
called select_repository() directly, which failed — the wizard had only advanced to step 2
(Inclusion), not step 4 (Destination), confirming the wizard is 6 steps deep. Fixed to click
through Inclusion and Exclusion (matching this suite's build_flb_job()) before asserting the
Destination step's repo combo is reachable.

Pure wizard-navigation check; no job is built (Cancel out after confirming the step advanced).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI
from browser.pom.common.locators import WizardLocators

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-62756"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@allure.title("NJM-62756 — selecting at least one item allows the wizard to advance past Source")
def test_proceed_allowed_with_one_item_selected(logged_in_page):
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

    flb.click_next()  # Source -> Inclusion
    assert page.locator(WizardLocators.SELECT_AT_LEAST_ONE).locator("visible=true").count() == 0, (
        "no 'select at least one item' validation error should block advancing past Source"
    )
    flb.click_next()  # Inclusion -> Exclusion
    flb.click_next()  # Exclusion -> Destination
    # Prove the Destination step was actually reached by successfully interacting with its own
    # repo combo (no dedicated 'Destination step active' locator is calibrated).
    flb.select_repository("Onboard repository")
    flb.click_cancel()
