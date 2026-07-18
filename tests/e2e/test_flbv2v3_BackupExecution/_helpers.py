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
) -> FlbWizardPage:
    """Build (but do not run) an FLB job via the wizard through Finish. Same contract as the
    sibling suites' build_flb_job() (see ObjectStorage's own copy) — no encryption/immutability
    params here since this suite's own variable is item-selection scope and job options, not
    destination-repo behavior."""
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
