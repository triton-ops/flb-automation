"""Shared build/run/verify helpers for the FLBv2v3_IncludeExclude suite (NJM-182720).

Every data-driven TC in this suite follows the same shape: build an FLB job (optionally with
Inclusion/Exclusion patterns) over a subfolder of the seeded C:\\TestData_ForFLB\\IncludeExclude\\
(Windows, PM-3 `Window11`) or /TestData_ForFLB/IncludeExclude/ (Linux, PM-2 `Linux_16.84`)
fixture (see test-data/test-data.md), run it, verify via FLR browse, then clean up (the
flb_job_cleanup fixture in tests/e2e/conftest.py handles teardown).
"""
from __future__ import annotations

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage

WINDOWS_MACHINE = "Window11"
LINUX_MACHINE = "Linux_16.84"

# Wizard Select-Items dialog drill path to reach IncludeExclude's subfolders — folder DISPLAY
# names as shown in that dialog (e.g. "Local Disk (C:)", not "C:").
IE_WIZARD_DRILL = ["Local Disk (C:)", "TestData_ForFLB", "IncludeExclude"]
# FLR Files-step left-tree path to the same location — tree NODE names (e.g. "C:", not
# "Local Disk (C:)"). See FileLevelRecoveryLocators.left_tree_row's docstring.
IE_FLR_PREFIX = ["C:", "TestData_ForFLB", "IncludeExclude"]

# Same fixture tree on the Linux source (linux-src / PM-2 / Linux_16.84): /TestData_ForFLB is a
# root-level item in the wizard's Select Items dialog (no "Local Disk" drive-letter wrapper).
IE_LINUX_WIZARD_DRILL = ["TestData_ForFLB", "IncludeExclude"]
# CALIBRATED live 2026-07-16: the FLR Files-step left tree does NOT mirror the wizard drill path —
# its single top-level node under the machine/recovery-point row is "root" (confirmed via
# screenshot of the AUTO_FLB_NJM-185020 job's FLR wizard), with TestData_ForFLB nested one level
# beneath that. Omitting "root" caused every Linux FLR browse in this suite to time out looking
# for a "TestData_ForFLB" tree row that was never a direct child.
IE_LINUX_FLR_PREFIX = ["root", "TestData_ForFLB", "IncludeExclude"]


def build_flb_job(
    page,
    job_name: str,
    drill_path: list[str],
    checks: list[str],
    *,
    machine: str = WINDOWS_MACHINE,
    is_linux: bool = False,
    inclusion: list[str] | None = None,
    exclusion: list[str] | None = None,
) -> FlbWizardPage:
    """Build (but do not run) an FLB job via the wizard through Finish."""
    dp = DataProtectionPage(page)
    dp.open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    if is_linux:
        flb.expand_linux()
    else:
        flb.expand_windows()
    flb.select_machine(machine)
    flb.open_item_picker()
    flb.select_items(drill_path, checks)
    flb.picker_apply()
    flb.click_next()  # Inclusion
    if inclusion:
        flb.enable_inclusion(inclusion)
    flb.click_next()  # Exclusion
    if exclusion:
        flb.enable_exclusion(exclusion)
    flb.click_next()  # Destination
    flb.select_repository("Onboard repository")
    flb.click_next()  # Schedule
    flb.set_run_on_demand()
    flb.click_next()  # Options
    flb.set_job_name(job_name)
    flb.finish()
    page.wait_for_timeout(2000)
    return flb


def run_and_wait_flb_job(page, job_name: str, timeout_ms: int = 300_000) -> str:
    """Run `job_name` and poll its dashboard status to a terminal state. Returns the final
    status string (e.g. 'Successful', 'Failed', 'Stopped')."""
    dp = DataProtectionPage(page)
    dp.open()
    page.wait_for_timeout(1500)
    dp.run_job(job_name)
    return dp.wait_for_job_status(job_name, timeout_ms=timeout_ms, poll_ms=10_000)


def flr_browse(page, job_name: str, path_segments: list[str]) -> list[dict]:
    """Open File Level Recovery for `job_name`, drill through `path_segments`, read the
    right-hand listing, then cancel the wizard. Browse-only — never selects a recovery type
    or executes a recovery. Returns the recovered items as [{'name', 'modified', 'size'}, ...]."""
    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name)
    page.wait_for_timeout(2000)
    flr.click_next()
    page.wait_for_timeout(2000)
    flr.wait_files_ready(timeout=180_000)
    recovered_items = flr.list_folder_contents(path_segments)
    flr.click_cancel()
    page.wait_for_timeout(1000)
    return recovered_items


def extract_item_names(recovered_items: list[dict]) -> list[str]:
    return [item["name"] for item in recovered_items]


def open_to_inclusion(page) -> FlbWizardPage:
    """Wizard-only helper (no job saved) for the pure UI-validation TCs — opens the FLB wizard,
    selects TestData_ForFLB as source, and advances to Step 2 - Inclusion."""
    DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(WINDOWS_MACHINE)
    flb.open_item_picker()
    flb.select_items(["Local Disk (C:)"], ["TestData_ForFLB"])
    flb.picker_apply()
    flb.click_next()  # -> Inclusion
    return flb


def has_visible_invalid_feedback(page) -> bool:
    """True if ANY visible red/invalid-state indicator exists: an 'Invalid parameters' message,
    or an ExtJS x-form-invalid class on the textarea. Per the NAS Backup Confluence spec
    (https://confluence.nakivo.com/display/tst/NAS+Backup, which File Level Backup's own spec
    explicitly reuses for Inclusion/Exclusion), an invalid entry SHOULD highlight the whole
    textarea red and show a message like "Invalid parameters: *.docx, My file.xlsx" — CALIBRATED
    live 2026-07-15: this build shows neither, only a behavioral Next-block."""
    if page.get_by_text("Invalid parameters", exact=False).locator("visible=true").count() > 0:
        return True
    invalid_textarea = page.locator(
        "//textarea[contains(@class,'x-form-invalid')]"
    ).locator("visible=true")
    return invalid_textarea.count() > 0
