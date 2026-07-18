r"""NJM-63200 / 62783 — [FLB v2] FLB Job Wizard - Source Step (UI): the 'Select Items' dialog
retains an existing job's selections when editing, and edits (deselect + select new) are saved
correctly.

Unlike the rest of this file's siblings, these two build a real job (safety-fenced AUTO_FLB_*,
cleaned up by flb_job_cleanup) since "editing" requires an existing job to edit — the dialog-only
assertions still don't execute a backup run (Finish, not Finish & Run; no run_and_wait_flb_job()
call). CALIBRATED pattern reused from the FLRFunctional suite's edit_flb_job_and_rerun(): reopen
via DataProtectionPage.edit_job() then FlbWizardPage.goto_step(WizardLocators.STEP_SOURCE) — EDIT
mode does not always land on Source (see edit_job()'s own docstring).

VERIFIED LIVE 2026-07-18: an initial version called expand_windows()/select_machine() again after
goto_step(STEP_SOURCE), which timed out — in EDIT mode the machine is ALREADY selected from the
original build, so re-clicking its LEFT-tree checkbox is wrong; open_item_picker() itself already
reopens the dialog for an already-selected machine via the right-hand panel's pencil/edit icon
(reveal_and_click(SELECTED_HEADER, EDIT_ICON) — see its own docstring), which is the correct,
existing mechanism for both create and edit mode alike.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import SelectItemsLocators as SI
from browser.pom.common.locators import WizardLocators

from ._helpers import build_flb_job

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection,
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@allure.title("NJM-63200 — reopening the dialog on an existing job retains its prior selections")
@pytest.mark.jira("NJM-63200")
def test_retains_selections_when_editing(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-63200")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["SpecialFiles_ForFLB"])

    dp = DataProtectionPage(page)
    dp.edit_job(job_name)
    flb = FlbWizardPage(page)
    flb.goto_step(WizardLocators.STEP_SOURCE)
    flb.open_item_picker()
    flb.wait(1500)

    assert flb.picker_row_disabled("SpecialFiles_ForFLB") is False, "should be a normal, re-openable row"
    # The previously-checked folder should already be ticked when reopening the picker for editing.
    flb.picker_toggle_selected_items()
    rows = flb.picker_selected_items_rows()
    names = {r["name"] for r in rows}
    assert "SpecialFiles_ForFLB" in names, f"expected the prior selection retained on edit, got: {rows}"

    page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
    flb.click_cancel()


@allure.title("NJM-62783 — editing selections via the dialog (deselect + select new) saves correctly")
@pytest.mark.jira("NJM-62783")
def test_editing_selections_via_dialog(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-62783")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["SpecialFiles_ForFLB"])

    dp = DataProtectionPage(page)
    dp.edit_job(job_name)
    flb = FlbWizardPage(page)
    flb.goto_step(WizardLocators.STEP_SOURCE)
    flb.open_item_picker()
    flb.wait(1500)

    # Reopening starts back at the volume-view root (confirmed live 2026-07-18 — the panel of
    # already-SELECTED items is retained, per NJM-63200, but the current BROWSE position is not),
    # so drill back into C: before the target checkboxes are visible in the listing.
    flb.picker_drill("Local Disk (C:)")
    flb.wait(800)

    # Deselect the original folder, select a different one, then Apply.
    flb.click_force(SI.checkbox("SpecialFiles_ForFLB"))
    flb.click_force(SI.checkbox("MaxNameTest_ForFLB"))
    flb.wait(500)
    flb.picker_apply()

    # Reopen to confirm the change was actually saved into the job's Source selection.
    flb.open_item_picker()
    flb.wait(1000)
    flb.picker_toggle_selected_items()
    rows = flb.picker_selected_items_rows()
    names = {r["name"] for r in rows}
    assert "MaxNameTest_ForFLB" in names, f"expected the new selection saved, got: {rows}"
    assert "SpecialFiles_ForFLB" not in names, f"expected the old selection removed, got: {rows}"

    page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
    flb.click_cancel()
