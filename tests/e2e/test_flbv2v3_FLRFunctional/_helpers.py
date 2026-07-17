"""Shared build/run/verify helpers for the FLBv2v3_FLRFunctional suite (NJM-182725).

Covers the "FLR from FLB - Functional" + "FLB v1 OS Support" TCs whose real destination is a
CIFS/NFS share or a browser download — the FLR wizard steps this suite drives that neither
FLBv2v3_IncludeExclude nor FLBv2v3_Inventory needed (those only ever browsed a recovery point,
never executed a real recovery to an external target).

win-fs3 (10.10.15.3) is the documented FLR CIFS/NFS export target (test-data/environment.md).
FLR_CIFS_Export is a dedicated SMB share created on it for this suite (C:\\FLR_CIFS_Export,
FullAccess granted to Administrator only). Its NFS counterpart reuses NFS_REPO's existing
export (10.10.15.3:/NFS_Share_Win) — no NFS-specific auth is needed by the wizard.

CIFS credentials come from .env via load_app_config().share("winfs3") (WINFS3_USER/WINFS3_PASS)
and are only ever handed to Playwright's own .fill() — the same channel already used for the
NBR login all session. Destination-content verification (checksum/ACL/permission checks on the
share) is NOT done here — pytest can't call the remoting (WinRM/SSH) tools this project uses for
that; it's a separate, agent-driven step reported alongside each test's result, not a pytest
assertion. Each test's docstring says so explicitly.
"""
from __future__ import annotations

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.base.config import load_app_config
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.locators import WizardLocators
from tests.e2e._lib._shared_helpers import (
    attach_test_data,
    extract_item_names,
    flr_browse,
    run_and_wait_flb_job,
    verify_checksum,
)

__all__ = [
    "MIXED_TYPES_FILES",
    "WINFS3_SHARE_CIFS",
    "WINFS3_SHARE_NFS",
    "build_flb_job",
    "edit_flb_job_and_rerun",
    "extract_item_names",
    "flr_browse",
    "recover_to_share",
    "run_and_wait_flb_job",
    "verify_checksum",
]

WINFS3_SHARE_CIFS = r"\\10.10.15.3\FLR_CIFS_Export"
WINFS3_SHARE_NFS = "10.10.15.3:/NFS_Share_Win"

MIXED_TYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


def build_flb_job(
    page,
    job_name: str,
    machine: str,
    drill_path: list[str],
    checks: list[str],
    *,
    is_linux: bool = False,
    repository: str = "Onboard repository",
    run_on_demand: bool = True,
) -> FlbWizardPage:
    """Build (but do not run) an FLB job via the wizard through Finish.

    `run_on_demand=True` (default, unchanged behavior for every other caller of this helper)
    checks 'Do not schedule, run on demand' on the Schedule step. CALIBRATED LIVE 2026-07-16
    for NJM-70312: an on-demand job's Schedule step has NO retention field exposed at all (it
    only appears for a real recurring schedule) — the appliance was observed to eventually prune
    an on-demand job down to just its LATEST recovery point (the pruning is asynchronous, not
    immediate, which is why a quick manual spot-check can miss it). Pass `run_on_demand=False`
    when a test needs MULTIPLE recovery points of the same job to coexist and be independently
    inspectable (e.g. an RP-picker test) — this leaves the wizard's default real schedule
    (Weekly) + its default 'Keep backups for 10 days' retention in place, which reliably keeps
    every recovery point created within that window; the job is still run purely on-demand via
    the Jobs sidebar's own Run button (run_and_wait_flb_job()/edit_flb_job_and_rerun()), the
    schedule itself is never allowed to actually fire during a test."""
    attach_test_data(
        job_name=job_name, machine=machine, drill_path=drill_path, checks=checks,
        is_linux=is_linux, repository=repository, run_on_demand=run_on_demand,
    )
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
    flb.click_next()  # Exclusion
    flb.click_next()  # Destination
    flb.select_repository(repository)
    flb.click_next()  # Schedule
    if run_on_demand:
        flb.set_run_on_demand()
    flb.click_next()  # Options
    flb.set_job_name(job_name)
    flb.finish()
    page.wait_for_timeout(2000)
    return flb


def edit_flb_job_and_rerun(
    page,
    job_name: str,
    drill_path: list[str],
    uncheck_names: list[str],
    check_names: list[str],
    backup_type: str = "Incremental",
    timeout_ms: int = 300_000,
) -> str:
    """Reopen `job_name` via DataProtectionPage.edit_job(), swap its Source-step item selection
    at `drill_path` (uncheck `uncheck_names`, check `check_names` — each name TOGGLES its
    current tick, same as FlbWizardPage.select_items()), Save & Run (forcing `backup_type` on
    the resulting 'Run this job?' dialog), then poll the job to a terminal status. Returns the
    terminal status string (same contract as run_and_wait_flb_job()).

    CALIBRATED live 2026-07-16 for NJM-70312: this is how this suite gets a SECOND, genuinely
    different recovery point for the SAME job WITHOUT any host-side content seeding (no
    SSH/WinRM access to the source host is available/in-scope here) — changing what the job
    backs up (not what exists on the source) is enough to produce a real, independently
    verifiable content difference between two recovery points of one job.

    ⚠ `backup_type='Incremental'` (NOT 'Full') is required — CALIBRATED LIVE (two separate
    passes): forcing 'Full' on this second run was first tried (and looked fine in a quick
    manual spot-check, AUTO_FLB_NJM-70312_calib, cleaned up after), but a full pytest run later
    showed only ONE recovery point left by the time the FLR wizard opened a few minutes later —
    a second FULL backup appears to start a brand-new chain that supersedes/prunes the prior
    savepoint asynchronously (not immediately, which is why the quick manual check missed it),
    rather than 30-day-old-age-based retention (the 'Keep recovery points for' value on the Run
    dialog, left at its 30-day default both times, rules that out). 'Incremental' builds on the
    EXISTING chain instead and reliably leaves both recovery points in place."""
    dp = DataProtectionPage(page)
    dp.edit_job(job_name)
    flb = FlbWizardPage(page)
    flb.goto_step(WizardLocators.STEP_SOURCE)
    flb.open_item_picker()
    flb.select_items(drill_path, uncheck_names + check_names)
    flb.picker_apply()
    flb.save_and_run()
    if backup_type:
        flb.set_run_dialog_backup_type(backup_type)
    flb.confirm_run()
    page.wait_for_timeout(2000)
    return dp.wait_for_job_status(job_name, timeout_ms=timeout_ms, poll_ms=10_000)


def recover_to_share(
    page,
    job_name: str,
    path_segments: list[str],
    filenames: list[str] | None,
    share_type: str,
    nth: int = 0,
    rp_index: int | None = None,
) -> bool:
    """Open FLR for `job_name`, drill to `path_segments`, select `filenames` (or the whole
    root if None), and execute a real 'Recover to custom location (CIFS/NFS)' recovery to the
    win-fs3 export target. Returns whether the wizard confirmed the recovery started — callers
    should assert on this. Does not verify destination content — see module docstring.

    `rp_index` (None = the wizard's default, i.e. the latest recovery point — unchanged behavior
    for every pre-existing caller): explicitly select recovery point `rp_index` on the Backup
    step first (0 = latest, 1 = next-older — display order is newest-first, see
    list_recovery_points()). Selecting a specific RP only makes sense with >=2 points, so this
    also waits for at least max(2, rp_index+1) points via wait_for_recovery_point_count() —
    which doubles as the Full+Incremental-pair precondition check for NJM-70372/70373 (the
    picker can lag a fresh run's Successful status by minutes; that helper's close-reopen
    polling is the calibrated fix, see its docstring)."""
    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name, nth=nth)
    page.wait_for_timeout(2000)
    if rp_index is not None:
        flr.wait_for_recovery_point_count(job_name, min_count=max(2, rp_index + 1))
        flr.select_recovery_point(rp_index)
    flr.click_next()
    page.wait_for_timeout(2000)
    flr.wait_files_ready(timeout=180_000)
    if path_segments:
        flr.drill_to(path_segments)
    if filenames:
        for filename in filenames:
            flr.select_file_in_current_folder(filename)
    else:
        flr.select_root()
    flr.click_next()  # Files -> Options
    flr.choose_recovery_type("custom")
    if share_type.lower() == "cifs":
        creds = load_app_config().share("winfs3")
        connected = flr.fill_custom_location("cifs", WINFS3_SHARE_CIFS, creds.user, creds.password)
    else:
        connected = flr.fill_custom_location("nfs", WINFS3_SHARE_NFS)
    assert connected, "Test Connection did not succeed — Recover button never became enabled"
    return flr.execute_custom_location_recovery()
