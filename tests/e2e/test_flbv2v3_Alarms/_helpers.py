"""Shared build/run/verify helpers for the FLBv2v3_Alarms suite (NJM-182728, "Alarms /
notifications / events").

`build_flb_job()` is cloned (not imported) from the sibling suites deliberately, per this
project's documented per-suite `_helpers.py` convention.

Every TC in this suite provokes a real failure condition on a job targeting a dedicated,
disposable `<Name>_ForFLB` fixture folder on win11 (never a shared/production path), then reads
the resulting alarm via the new AlarmsPage (browser/pom/common/alarms_page.py — first POM
coverage for this area, CALIBRATED live 2026-07-21). No alarm CODE (e.g. 'ict45') is ever shown
literally in the UI — only a human-readable message naming the failure — so tests assert against
that message's real content (the fixture folder's own path/name), not an assumed code string.
"""
from __future__ import annotations

from browser.pom.backup_types.flb_wizard_page import FlbWizardPage
from browser.pom.common.alarms_page import AlarmsPage
from browser.pom.common.data_protection_page import DataProtectionPage
from tests.e2e._lib._shared_helpers import attach_test_data, run_and_wait_flb_job

__all__ = ["attach_test_data", "build_flb_job", "read_job_alarm_text", "run_and_wait_flb_job"]


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
    """Build (but do not run) an FLB job via the wizard through Finish. Same shape as every
    sibling suite's build_flb_job()."""
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


def read_job_alarm_text(page, job_name: str) -> str:
    """Select `job_name`'s dashboard, open its Issues panel, and return the full panel text for
    the caller to search (e.g. `assert "AlarmTest45_ForFLB" in text`). Closes the panel again
    before returning, leaving the Jobs sidebar reachable for whatever the test does next (same
    discipline as this project's other FLR-wizard-close lessons — never leave a panel/dialog open
    for the next action to trip over)."""
    dp = DataProtectionPage(page)
    dp.select_job_row(job_name)
    page.wait_for_timeout(1500)
    alarms = AlarmsPage(page)
    alarms.open_issues_panel()
    text = alarms.issues_panel_text()
    alarms.close_issues_panel()
    return text
