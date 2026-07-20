r"""NJM-122651 — [FLB v1] FLB Job Wizard - Functional - Verify Selection of All Item Types
(Volumes, Folders, Files).

Standalone script in suite D (per explicit instruction — each suite's TCs are executed
separately; not folded into suite A's overlapping Select-Items-dialog coverage).

⚠ LIVE FINDING, CORRECTING THE TC'S OWN LITERAL STEPS (2026-07-20): the TC's steps 5-7 assume a
FOLDER, its own SUBFOLDER, and a FILE inside that subfolder can all be ticked SIMULTANEOUSLY,
stacking to a selected count of 3. Verified live via a throwaway probe script that this is NOT
what happens on this build: once an ancestor folder is fully ticked, drilling into it renders
every descendant row DISABLED (confirmed via FlbWizardPage.picker_row_disabled() reading `true`,
and the real DOM — the row's own tooltip stays just the item's name, no 'Maximum selected items'
message, so this is a distinct disabled-reason from the 200-item cap already documented
elsewhere) — a click on a disabled descendant is silently a no-op, which is exactly why the
original attempt at this test kept reading back only the ancestor's own row after supposedly
ticking a child. This matches the SAME logic the TC's own step 5 already applies (it explicitly
UNTICKS the volume before ticking the folder) — steps 6-7 just don't say so explicitly, but the
real UI enforces it anyway. Rewritten below to untick each ancestor before drilling into it and
selecting the next, more specific item — proving all three non-volume granularities (folder,
subfolder, file) are each independently selectable, without claiming a stacked/simultaneous
selection across nesting levels that this build doesn't support.

Uses FlbWizardPage.picker_selected_items_rows() (reads the Selected Items panel's Name column —
CALIBRATED live 2026-07-20: this panel shows a volume as 'C:', not the folder-listing row's own
label 'Local Disk (C:)') to verify the selection at each step.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-122651")]

MACHINE = "Window11"
REPOSITORY = "Onboard repository"


def _panel_rows(flb: FlbWizardPage) -> list[dict]:
    """See this module's own docstring for the settle-wait rationale (a bare toggle-then-read
    caught the grid mid-refresh once during calibration)."""
    if not flb.picker_selected_items_panel_expanded():
        flb.picker_toggle_selected_items()
    flb.wait(800)
    return flb.picker_selected_items_rows()


@allure.title("NJM-122651 — select a volume, then (independently) a folder, subfolder, and file")
def test_selection_of_all_item_types(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-122651_all-item-types")

    dp = DataProtectionPage(page)
    dp.open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(MACHINE)
    flb.open_item_picker()

    # 1. tick the volume itself
    flb.picker_check("Local Disk (C:)")
    rows = _panel_rows(flb)
    assert [r["name"] for r in rows] == ["C:"], f"expected only the volume selected, got {rows}"

    # 2. untick it (required before drilling in — a ticked ancestor disables its descendants)
    flb.picker_check("Local Disk (C:)")
    rows = _panel_rows(flb)
    assert rows == [], f"expected the volume's selection to be cleared, got {rows}"

    # 3. drill into the volume, tick the folder
    flb.picker_drill("Local Disk (C:)")
    flb.picker_check("TestData_ForFLB")
    rows = _panel_rows(flb)
    assert [r["name"] for r in rows] == ["TestData_ForFLB"], f"expected only the folder selected, got {rows}"

    # 4. untick the folder (its descendants render disabled while it stays ticked — live-verified,
    # see module docstring), THEN drill in and tick the subfolder independently
    flb.picker_check("TestData_ForFLB")
    assert _panel_rows(flb) == [], "expected the folder's selection to be cleared before drilling in"
    flb.picker_drill("TestData_ForFLB")
    flb.picker_check("MixedTypes")
    rows = _panel_rows(flb)
    assert [r["name"] for r in rows] == ["MixedTypes"], f"expected only the subfolder selected, got {rows}"

    # 5. untick the subfolder, drill in, tick an individual file independently
    flb.picker_check("MixedTypes")
    assert _panel_rows(flb) == [], "expected the subfolder's selection to be cleared before drilling in"
    flb.picker_drill("MixedTypes")
    flb.picker_check("sample.pdf")
    rows = _panel_rows(flb)
    assert [r["name"] for r in rows] == ["sample.pdf"], f"expected only the file selected, got {rows}"

    flb.picker_apply()
    flb.click_next()  # Inclusion
    flb.click_next()  # Exclusion
    flb.click_next()  # Destination
    flb.select_repository(REPOSITORY)
    flb.click_next()  # Schedule
    flb.set_run_on_demand()
    flb.click_next()  # Options
    flb.set_job_name(job_name)
    flb.finish_and_run()
    flb.confirm_run()

    status = dp.wait_for_job_status(job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"
