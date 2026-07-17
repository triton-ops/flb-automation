"""Shared build/run/verify helpers for the FLBv2v3_Inventory suite (NJM-182726).

Each TC verifies FLB end-to-end workflow (create -> run -> FLR recover -> compare) on a specific
OS/filesystem source. Most Windows/Linux TCs share the same 7-file MixedTypes verification
fileset (see test-data/test-data.md's MixedTypes convention, seeded identically in shape across
every source in this suite).

NOTE — shared-source serialization: several TCs here target the SAME physical machine as other
TCs in this suite (e.g. NJM-67807 and NJM-68933 both use Linux_16.84/PM-2). Per the project's
"no concurrent jobs against the same source" finding (a source VID locks/stalls rather than
queueing), these tests must not be run concurrently with each other (e.g. via pytest-xdist) —
plain sequential `pytest` execution is safe since each test's build+run+poll+cleanup completes
before the next test starts.
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
    "MIXED_TYPES_FILES",
    "build_flb_job",
    "extract_item_names",
    "flr_browse",
    "run_and_wait_flb_job",
    "verify_checksum",
]

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
) -> FlbWizardPage:
    """Build (but do not run) an FLB job via the wizard through Finish."""
    attach_test_data(
        job_name=job_name, machine=machine, drill_path=drill_path, checks=checks,
        is_linux=is_linux, repository=repository,
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
    flb.finish()
    page.wait_for_timeout(2000)
    return flb
