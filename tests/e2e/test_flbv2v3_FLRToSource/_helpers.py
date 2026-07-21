"""Shared build/run/verify helpers for the FLBv2v3_FLRToSource suite (NJM-182724, "FLR to
source + overwrite").

`build_flb_job()` is cloned (not imported) from the sibling suites deliberately, per this
project's documented per-suite `_helpers.py` convention.

⚠ SAFETY — READ BEFORE ADDING A NEW TEST HERE: every TC in this suite exercises FLR's
'Recovery to original location' recovery type, which WRITES TO THE REAL SOURCE MACHINE'S
ORIGINAL FILE PATH (not a disposable `AUTO_FLB_*` job/backup — the actual filesystem of
`Window11`/win11). Per CLAUDE.md, this is gated and was only exercised after the user gave
EXPLICIT, SCOPED authorization (2026-07-20) covering exactly this: every test in this suite
targets ONLY files inside the dedicated, disposable `C:\\RecoverToSource_ForFLB\\` fixture
tree (plus the pre-existing `C:\\ACLTest_ForFLB\\secured` fixture for the one ACL-focused TC,
already established in `test_flbv2v3_FLRFunctional`) — never any other path. `recover_to_source()`
below is the one function in this suite that actually calls
`FileLevelRecoveryPage.execute_original_location_recovery()`; do not add a second call site
without re-confirming the same scoping discipline.
"""
from __future__ import annotations

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from tests.e2e._lib._shared_helpers import (
    attach_test_data,
    extract_item_names,
    flr_browse,
    run_and_wait_flb_job,
)

__all__ = [
    "build_flb_job",
    "extract_item_names",
    "flr_browse",
    "recover_to_source",
    "run_and_wait_flb_job",
]


def build_flb_job(
    page,
    job_name: str,
    machine: str,
    drill_path: list[str],
    checks: list[str],
    *,
    is_linux: bool = False,
    repository: str = "Onboard repository",
    acl_mode: str | None = None,
) -> FlbWizardPage:
    """Build (but do not run) an FLB job via the wizard through Finish. Same shape as every
    sibling suite's build_flb_job() — always run_on_demand, since this suite's variable is the
    FLR-side recovery type/overwrite behavior, not the job's own schedule. `acl_mode` (added for
    NJM-182440, the one ACL-focused TC in this suite) sets the Options step's Access Control List
    combo — see suite D's FlbWizardPage.set_acl_mode() for the accepted values."""
    attach_test_data(
        job_name=job_name, machine=machine, drill_path=drill_path, checks=checks,
        is_linux=is_linux, repository=repository, acl_mode=acl_mode,
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
    flb.set_run_on_demand()
    flb.click_next()  # Options
    flb.set_job_name(job_name)
    if acl_mode is not None:
        flb.set_acl_mode(acl_mode)
    flb.finish()
    page.wait_for_timeout(2000)
    return flb


def recover_to_source(
    page, job_name: str, flr_drill_path: list[str], file_names: list[str], overwrite_locator: str,
) -> bool:
    """Open FLR for `job_name`, drill to `flr_drill_path`, select each name in `file_names`,
    choose 'Recovery to original location', set the overwrite-behavior combo to
    `overwrite_locator` (one of FileLevelRecoveryLocators.OVERWRITE_RENAME/SKIP/OVERWRITE), then
    EXECUTE the recovery. Returns whether the wizard confirmed the recovery started.

    ⚠ This is the one call site in this suite that writes to the real source machine's original
    path — see this module's own docstring for the exact authorization scope. Every caller MUST
    pass a `flr_drill_path` rooted under RecoverToSource_ForFLB (or ACLTest_ForFLB for the ACL
    TC) — never anything else.

    Unlike every other suite's two-phase pattern (whose phase-2 test always calls
    run_and_wait_flb_job() first, which internally navigates to Data Protection before touching
    FLR), this suite's phase 2 never reruns the job — it recovers from the recovery point phase 1
    already made. A fresh `logged_in_page` for the phase-2 test lands on the post-login Overview
    page, not Data Protection, so recover_file_level() (which assumes the Jobs sidebar is already
    on-screen) would time out looking for a job row that isn't there yet. Navigate explicitly."""
    DataProtectionPage(page).open()
    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name)
    page.wait_for_timeout(2000)
    flr.click_next()
    page.wait_for_timeout(2000)
    flr.wait_files_ready(timeout=180_000)
    flr.drill_to(flr_drill_path)
    for name in file_names:
        flr.select_file_in_current_folder(name)
    flr.click_next()  # Options
    flr.choose_recovery_type("original")
    flr.set_overwrite_behavior(overwrite_locator)
    return flr.execute_original_location_recovery()
