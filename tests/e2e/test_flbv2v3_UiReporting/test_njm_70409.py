r"""NJM-70409 — [FLB v1] FLB - Reliability (ICT) - Verify Job Fails When Root Backup Folder is
Missing (ict45).

TWO-PHASE COMBINATION TEST (same rationale as every other suite's — a live WinRM rename between
two pytest invocations can only be driven by the session's own agent, not pytest code):
  1. `pytest test_njm_70409.py::test_baseline_backup` — builds+runs a job whose ENTIRE source
     selection is the root-level folder `C:\RootMissingTest_ForFLB` itself. No cleanup call —
     job survives into phase 2.
  2. Agent renames `RootMissingTest_ForFLB` away via WinRM so the job's configured root no
     longer exists at its path.
  3. `pytest test_njm_70409.py::test_rerun_fails_and_retains_reference` — reruns the SAME job
     (must now FAIL — contrast with NJM-70410, where a MISSING SUB-item is skipped and the job
     still succeeds; a missing ROOT fails the whole job), asserts the Issues-panel alarm names
     the missing folder, then opens the job editor and confirms (a) the Source step's Selected
     Items dialog still lists the missing folder as selected (not silently dropped), and (b) the
     SAME dialog's browsable folder listing does NOT show it (excluded from the live inventory).

⚠ If phase 2 (the rename) is never applied, phase 3 will just pass as a normal successful rerun
and silently fail to exercise ict45 at all.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import WizardLocators

from ._helpers import build_flb_job, read_job_alarm_text, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-70409")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-70409_root-missing-ict45"


@allure.title("NJM-70409 phase 1/2 — baseline backup with RootMissingTest_ForFLB as the job's root")
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, ["Local Disk (C:)"], ["RootMissingTest_ForFLB"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"


@allure.title("NJM-70409 phase 2/2 — rerun after root folder removal fails (ict45); editor retains reference")
@pytest.mark.flaky(reruns=0)
def test_rerun_fails_and_retains_reference(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=180_000)
    assert status == "Failed", (
        f"expected the rerun to FAIL (its root folder was renamed away), got: {status}"
    )

    alarm_text = read_job_alarm_text(page, JOB_NAME)
    assert "RootMissingTest_ForFLB" in alarm_text, (
        f"expected the Issues panel to name the missing RootMissingTest_ForFLB folder, "
        f"got panel text: {alarm_text!r}"
    )

    # Open the job editor and inspect the Source step's Select Items dialog.
    DataProtectionPage(page).edit_job(JOB_NAME)
    page.wait_for_timeout(1500)
    page.locator(WizardLocators.STEP_SOURCE).locator("visible=true").first.click()
    page.wait_for_timeout(1500)

    flb = FlbWizardPage(page)
    flb.open_item_picker()
    page.wait_for_timeout(1000)
    if not flb.picker_selected_items_panel_expanded():
        flb.picker_toggle_selected_items()

    selected_rows = flb.picker_selected_items_rows()
    selected_names = [row.get("name", "") for row in selected_rows]
    assert any("RootMissingTest_ForFLB" in name for name in selected_names), (
        f"expected the missing folder to still be listed as SELECTED (not auto-removed), "
        f"got selected rows: {selected_rows!r}"
    )

    browsable_names = flb.picker_row_names()
    assert not any("RootMissingTest_ForFLB" in name for name in browsable_names), (
        f"expected the missing folder to be EXCLUDED from the browsable Select Items listing, "
        f"got: {browsable_names!r}"
    )

    flb.picker_apply()  # no ticks changed — closes the dialog without altering the job
    flb.click_cancel()  # exit the editor without saving
    page.wait_for_timeout(1000)

    flb_job_cleanup(JOB_NAME)
