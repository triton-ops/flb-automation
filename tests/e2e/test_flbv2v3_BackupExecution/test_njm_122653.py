r"""NJM-122653 — [FLB v1] FLB Job Wizard - Validation - Ensure 'Next' Button is Enabled After Item
Selection.

Standalone script (not folded into suite A's overlapping dialog-UI coverage, per explicit
instruction — each suite's TCs are executed separately, so suite D keeps its own copy here rather
than pointing at test_flbv2v3_SourceSelection).

Verifies the Select Items dialog's own footer count text ('Selected for Physical Machine: 0' ->
'...: N' — CALIBRATED live 2026-07-20, correcting an earlier wrong assumption that it read 'No
item(s) selected') around the tick+Apply step, then that clicking 'Next' genuinely advances the
wizard past Inclusion/Exclusion to the Destination step (asserted via DestinationLocators.COMBO's
'Select a target destination' text, which only renders on that step) — the zero-to-nonzero count
transition is what this TC is actually about, not just that some Next button exists somewhere.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import DestinationLocators

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution]

MACHINE = "Window11"


@allure.title("NJM-122653 — 'Next' enables only after at least one item is selected, and advances the wizard")
@pytest.mark.jira("NJM-122653")
def test_next_button_enabled_after_item_selection(logged_in_page):
    page = logged_in_page
    dp = DataProtectionPage(page)
    dp.open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()

    before = flb.picker_selected_count()
    assert before.strip().endswith(": 0"), f"expected a zero selected-item count before any tick, got {before!r}"

    flb.picker_drill("Local Disk (C:)")
    flb.picker_drill("TestData_ForFLB")
    flb.picker_check("MixedTypes")
    after = flb.picker_selected_count()
    assert not after.strip().endswith(": 0"), f"expected a nonzero selected-item count after ticking, got {after!r}"

    flb.picker_apply()
    flb.click_next()  # Inclusion
    flb.click_next()  # Exclusion
    flb.click_next()  # Destination

    destination_visible = page.locator(DestinationLocators.COMBO).locator("visible=true").count() > 0
    assert destination_visible, "expected the wizard to advance to the Destination step after Next"
