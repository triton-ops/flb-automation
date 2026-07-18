"""Shared build/run/verify helpers for the FLBv2v3_SourceSelection suite (NJM-182719, execution A).

This suite splits into two halves:

  * 34 "Select Items" dialog / Source-step UI-state TCs — these drive the FLB wizard's Source step
    picker (title, breadcrumbs, search, Up-One-Level, Selected-Items panel, the 200-item cap and
    its tooltip, Volume-view default, Apply/Cancel, etc.) via the calibrated POM on FlbWizardPage.
    They assert on UI state only; they never run a job.

  * 14 "FLB - Functional" backup/recovery TCs — back up a folder holding a special file type
    (unicode names, dotfiles, extensionless files, .iso/.exe, archives, hidden files, .lnk
    shortcuts, max filename/path length, symlinks/hard links, permissions), then either recover to
    an external share and byte-verify the content, or (for the "expected to skip" TCs — system
    files, EFS-encrypted files) browse the recovery point and assert the skipped items are ABSENT.

The functional half reuses the exact build → run → recover-to-share apparatus the FLRFunctional
suite (NJM-182725) already calibrated live, against the same win-fs3 (10.10.15.3) CIFS/NFS export
target. build_flb_job() and recover_to_share() are cloned here (not imported from the sibling
suite) deliberately: per tests/e2e/_lib/_shared_helpers.py's own module docstring, build_flb_job()
is intentionally NOT shared — its signature/behavior diverges per suite and the FLB wizard UI can
still drift, so each suite keeps its own copy and only the genuinely-identical generic plumbing
(run_and_wait_flb_job / flr_browse / extract_item_names / verify_checksum / attach_test_data)
lives in _lib. Destination-content verification (checksum on the share) is NOT a pytest assertion
— it's the agent-driven remoting step reported alongside each test, same convention as
FLRFunctional; each functional test's docstring says so explicitly.
"""
from __future__ import annotations

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.base.config import load_app_config
from browser.pom.common.data_protection_page import DataProtectionPage
from tests.e2e._lib._shared_helpers import (
    attach_test_data,
    extract_item_names,
    flr_browse,
    run_and_wait_flb_job,
    verify_checksum,
)

__all__ = [
    "WINFS3_SHARE_CIFS",
    "WINFS3_SHARE_NFS",
    "attach_test_data",
    "build_flb_job",
    "extract_item_names",
    "flr_browse",
    "recover_to_share",
    "run_and_wait_flb_job",
    "verify_checksum",
]

# Same documented FLR export target as the FLRFunctional suite (test-data/environment.md).
WINFS3_SHARE_CIFS = r"\\10.10.15.3\FLR_CIFS_Export"
WINFS3_SHARE_NFS = "10.10.15.3:/NFS_Share_Win"


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
    """Build (but do not run) an FLB job via the wizard through Finish. Same contract as the
    FLRFunctional suite's build_flb_job() — see that copy's docstring for the run_on_demand
    calibration detail (an on-demand job exposes no retention field and is eventually pruned to
    its latest recovery point; pass run_on_demand=False only when a test needs >1 coexisting RP)."""
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


def recover_to_share(
    page,
    job_name: str,
    path_segments: list[str],
    filenames: list[str] | None,
    share_type: str,
    nth: int = 0,
) -> bool:
    """Open FLR for `job_name`, drill to `path_segments`, select `filenames` (or the whole root
    if None), and execute a real 'Recover to custom location (CIFS/NFS)' recovery to the win-fs3
    export target. Returns whether the wizard confirmed the recovery started — callers assert on
    this. Does not verify destination content (see module docstring). Cloned from FLRFunctional's
    recover_to_share() minus the rp_index picker arg this suite has no use for."""
    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name, nth=nth)
    page.wait_for_timeout(2000)
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
