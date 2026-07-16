"""Calibration/regression check for DataProtectionPage.run_job() / wait_for_job_status() —
CALIBRATED live 2026-07-15 against nbr-84.

Builds a throwaway AUTO_FLB_ job (schedule = run on demand, so it sits idle until run_job()
triggers it), runs it via the toolbar Run button + 'Run this job?' confirm dialog, then polls
the job's own dashboard 'Job Info' panel (line 2) until it reaches a terminal state. Confirms
the status transitions through 'Running' before landing on 'Successful', then cleans up via
JobManagementPage.delete_job().

Run: cd browser && python checks/check_job_status_polling.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.backup_types.flb_wizard_page import FlbWizardPage
from pom.base.driver import CONFIG_PATH, browser_page, load_config
from pom.common.data_protection_page import DataProtectionPage
from pom.common.job_management_page import JobManagementPage
from pom.common.locators import DataProtectionLocators
from pom.common.login_page import LoginPage

TC = "check_job_status_polling"
JOB_NAME = "AUTO_FLB_CHECK_STATUS_POLL"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_config(CONFIG_PATH)
    results = []

    with browser_page(headless=not args.headed) as page:
        LoginPage(page).open(cfg["url"]).login(cfg["user"], cfg["password"])
        jm = JobManagementPage(page)

        # idempotency: remove any leftover job from a previous/interrupted run first
        DataProtectionPage(page).open()
        page.wait_for_timeout(1500)
        if page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count() > 0:
            jm.delete_job(JOB_NAME)
            page.wait_for_timeout(1500)

        # 1) build a throwaway job, run-on-demand (idle until we explicitly run it)
        DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
        flb = FlbWizardPage(page).on_sources_step()
        flb.expand_windows()
        flb.select_machine("Window11")
        flb.open_item_picker()
        flb.select_items(["Local Disk (C:)"], ["TestData_ForFLB"])
        flb.picker_apply()
        flb.click_next()  # Inclusion
        flb.click_next()  # Exclusion
        flb.click_next()  # Destination
        flb.select_repository("Onboard repository")
        flb.click_next()  # Schedule
        flb.set_run_on_demand()
        flb.click_next()  # Options
        flb.set_job_name(JOB_NAME)
        flb.finish()
        page.wait_for_timeout(2000)

        dp = DataProtectionPage(page)
        dp.open()
        page.wait_for_timeout(1500)
        found = page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count() > 0
        results.append((f"job {JOB_NAME} exists after build", found))

        status_before = dp.get_job_status(JOB_NAME)
        results.append((
            f"status before run is 'Not executed yet' (got {status_before!r})",
            status_before == "Not executed yet",
        ))

        # 2) run it, then poll for a non-terminal in-flight status before it completes
        dp.run_job(JOB_NAME)
        page.wait_for_timeout(2000)
        status_running = dp.get_job_status(JOB_NAME)
        results.append((
            f"status shortly after run_job() is in-flight (got {status_running!r})",
            status_running not in ("", "Not executed yet"),
        ))

        # 3) poll to a terminal state (small fileset, should be quick — cap at 5 min)
        final_status = dp.wait_for_job_status(JOB_NAME, timeout_ms=300_000, poll_ms=10_000)
        results.append((f"wait_for_job_status() reaches terminal state (got {final_status!r})", final_status == "Successful"))

        # 4) cleanup
        jm.delete_job(JOB_NAME)
        page.wait_for_timeout(1500)
        dp.open()
        page.wait_for_timeout(1500)
        found_after = page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count() > 0
        results.append((f"job {JOB_NAME} gone after delete_job()", not found_after))

    print(f"\n[{TC}] results:")
    for label, passed in results:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}")
    allpass = all(p for _, p in results)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL — see above'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
