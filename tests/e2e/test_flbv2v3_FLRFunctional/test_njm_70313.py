"""NJM-70313 — [FLB v1] FLR from FLB - Files Step - Verify File/Folder Browser and Selection for
Recovery. Original status: never executed under the old RPC workflow (no cases/*.md runbook
exists).

Per the TC's own Xray steps: confirm a valid FLB recovery point exists and the source machine is
in Inventory (OK); on the Files step, browse the file tree and confirm it shows the backed-up
directory structure; select a mix of individual files and folders via checkboxes and confirm they
are added to the recovery list with correct names (and sizes, for files); deselect one item and
confirm it's removed from the recovery list without affecting the other selected item.

CALIBRATED LIVE 2026-07-16 (AUTO_FLB_DEBUG_70313, built + fully cleaned up during calibration —
the job built by THIS test is the real AUTO_FLB_NJM-70313): the Files step shows a
'Selected for recovery: N' summary above the tree, with 'Show'/'Hide' and 'Clear Selection' text
links. Clicking 'Show' expands a panel listing each selected item's Name/Path/Modified/Size —
this IS the TC's "recovery list". Files show their size immediately (e.g. '0.0 KB'); folders were
observed to NOT render a size in this panel (likely computed lazily/async) — see
FileLevelRecoveryPage.selected_items_panel_text()'s docstring. This test therefore asserts on
selected-count and item names (both files and folders) but does not assert on a folder's size.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage

from ._helpers import build_flb_job, extract_item_names, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70313")]

MACHINE = "Window11"
DRILL_PATH = ["C:", "TestData_ForFLB"]


@allure.title("NJM-70313 — Files step: browse tree, select/deselect mixed file+folder for recovery")
def test_files_step_browse_and_select(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70313")

    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name)
    page.wait_for_timeout(2000)
    flr.click_next()
    page.wait_for_timeout(2000)
    flr.wait_files_ready(timeout=180_000)

    # --- TC step 2: the Files-step tree shows the backed-up directory structure ---
    root_contents = flr.list_folder_contents(DRILL_PATH)
    root_names = set(extract_item_names(root_contents))
    assert {"atest1.txt", "Folder_test2"} <= root_names, (
        f"expected backed-up items not shown in the Files tree at {DRILL_PATH}: {root_names}"
    )

    # --- TC step 3: select a mix of one file and one folder; both are added to the recovery
    # list with correct names ---
    assert flr.selected_items_count() == 0, "expected 0 items selected before any selection"
    flr.select_file_in_current_folder("atest1.txt")
    flr.select_file_in_current_folder("Folder_test2")
    assert flr.selected_items_count() == 2, "expected 2 items selected after ticking a file + a folder"
    panel_text = flr.selected_items_panel_text()
    assert "atest1.txt" in panel_text, f"selected file 'atest1.txt' missing from recovery list: {panel_text!r}"
    assert "Folder_test2" in panel_text, f"selected folder 'Folder_test2' missing from recovery list: {panel_text!r}"
    assert "0.0 KB" in panel_text or "KB" in panel_text, (
        f"expected a file size to be shown in the recovery list: {panel_text!r}"
    )

    # --- TC step 4: deselect one item; it's removed from the recovery list, the other is
    # unaffected ---
    flr.select_file_in_current_folder("atest1.txt")  # toggles OFF (already ticked)
    assert flr.selected_items_count() == 1, "expected 1 item selected after deselecting atest1.txt"
    panel_text_after = flr.selected_items_panel_text()
    assert "atest1.txt" not in panel_text_after, (
        f"deselected file 'atest1.txt' still shown in the recovery list: {panel_text_after!r}"
    )
    assert "Folder_test2" in panel_text_after, (
        f"unaffected folder 'Folder_test2' unexpectedly removed from the recovery list: {panel_text_after!r}"
    )

    flr.click_cancel()
