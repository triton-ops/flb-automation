"""Shared build/run/verify helpers for the FLBv2v3_BackupExecution suite (NJM-182722,
execution D — "Backup exec / schedule / retention").

`build_flb_job()` is cloned (not imported) from the sibling suites deliberately, per
tests/e2e/_lib/_shared_helpers.py's own documented convention (build_flb_job() diverges per
suite and the FLB wizard UI can still drift). Reuses the same `Onboard repository` +
`Window11`/`flb-linux` + `TestData_ForFLB`/`MixedTypes` fixtures every other suite already
relies on (test-data/environment.md, test-data/test-data.md) — this suite's own variable is job
CONFIGURATION (item scope, options, retention), not the destination or source content.
"""
from __future__ import annotations

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.data_protection_page import DataProtectionPage
from tests.e2e._lib._shared_helpers import (
    attach_test_data,
    extract_item_names,
    flr_browse,
    run_and_wait_flb_job,
    verify_checksum,
)

__all__ = [
    "attach_test_data",
    "build_flb_job",
    "extract_item_names",
    "flr_browse",
    "run_and_wait_flb_job",
    "verify_checksum",
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
    run_on_demand: bool = True,
    retention: tuple[int, str] | None = None,
    acl_mode: str | None = None,
    app_aware_mode: str | None = None,
    concurrent_task_limit: int | None = None,
    full_backup_mode: str | None = None,
) -> FlbWizardPage:
    """Build (but do not run) an FLB job via the wizard through Finish. Same contract as the
    sibling suites' build_flb_job(), plus optional Options/Schedule-step params added 2026-07-19
    to back suite D's Options-step TCs (NJM-67678/67583/185052/182439/185036/128606-128609/
    128614/128615), all no-op/default for callers that don't pass them:
      - `retention=(count, unit)`: FlbWizardPage.set_retention(count, unit) on the Schedule step
        — implicitly skips set_run_on_demand() (same real-schedule-block precondition immutable_days
        uses in the ObjectStorage suite's build_flb_job()), since retention only renders under a
        real recurring schedule.
      - `acl_mode` / `app_aware_mode` / `concurrent_task_limit`: FlbWizardPage.set_acl_mode() /
        set_app_aware_mode() / set_concurrent_task_limit() on the Options step (CALIBRATED live
        2026-07-19 — see OptionsLocators' own docstring in locators.py).
      - `full_backup_mode` ('Active full' / 'Synthetic full'): sets the Options step's Full
        Backup Settings mode combo, PLUS the 'Create full backup:' frequency to 'Job runs #' with
        every_job_runs=1 — i.e. every single run produces a new full backup, in the chosen mode.
        Deliberately uses 'Job runs #' (not 'Always') because it's one of only two frequency
        options confirmed live to work under run-on-demand scheduling (see
        OptionsLocators.CREATE_FULL_BACKUP_FREQUENCY_COMBO_INPUT's gating-finding docstring) — no
        real recurring schedule needed, run_on_demand stays untouched."""
    attach_test_data(
        job_name=job_name, machine=machine, drill_path=drill_path, checks=checks,
        is_linux=is_linux, repository=repository, run_on_demand=run_on_demand,
        retention=retention, acl_mode=acl_mode, app_aware_mode=app_aware_mode,
        concurrent_task_limit=concurrent_task_limit, full_backup_mode=full_backup_mode,
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
    if retention is not None:
        flb.set_retention(retention[0], retention[1])
    elif run_on_demand:
        flb.set_run_on_demand()
    flb.click_next()  # Options
    flb.set_job_name(job_name)
    if acl_mode is not None:
        flb.set_acl_mode(acl_mode)
    if app_aware_mode is not None:
        flb.set_app_aware_mode(app_aware_mode)
    if concurrent_task_limit is not None:
        flb.set_concurrent_task_limit(concurrent_task_limit)
    if full_backup_mode is not None:
        flb.set_full_backup_mode(full_backup_mode)
        flb.set_full_backup_frequency("Job runs #", every_job_runs=1)
    flb.finish()
    page.wait_for_timeout(2000)
    return flb
