"""Calibration/regression check for FileLevelRecoveryPage.list_folder_contents() — CALIBRATED
live 2026-07-15 against nbr-84.

Builds a throwaway AUTO_FLB_ job over the seeded TestData_ForFLB fileset, runs it to completion,
then browses into it via the File Level Recovery wizard's Files step (C: -> TestData_ForFLB) and
confirms the listing shows real rows. Browse-only — ticks nothing, executes no recovery. Cleans
up the job via JobManagementPage.delete_job() regardless of outcome.

Run: cd browser && python checks/check_flr_folder_browse.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from pom.backup_types.flb_wizard_page import FlbWizardPage
from pom.base.config import load_app_config
from pom.base.driver import browser_page
from pom.common.data_protection_page import DataProtectionPage
from pom.common.job_management_page import JobManagementPage
from pom.common.locators import DataProtectionLocators
from pom.common.login_page import LoginPage

TC = "check_flr_folder_browse"
JOB_NAME = "AUTO_FLB_CHECK_FLR_BROWSE"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_app_config().flb
    results = []

    with browser_page(headless=not args.headed) as page:
        LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
        jm = JobManagementPage(page)
        dp = DataProtectionPage(page)
        dp.open()
        page.wait_for_timeout(1500)

        if page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count() == 0:
            dp.open_create_menu().start_file_level_backup()
            flb = FlbWizardPage(page).on_sources_step()
            flb.expand_windows()
            flb.select_machine("Window11")
            flb.open_item_picker()
            flb.select_items(["Local Disk (C:)"], ["TestData_ForFLB"])
            flb.picker_apply()
            flb.click_next()
            flb.click_next()
            flb.click_next()
            flb.select_repository("Onboard repository")
            flb.click_next()
            flb.set_run_on_demand()
            flb.click_next()
            flb.set_job_name(JOB_NAME)
            flb.finish()
            page.wait_for_timeout(2000)
            dp.open()
            page.wait_for_timeout(1500)

        status = dp.get_job_status(JOB_NAME)
        if status != "Successful":
            dp.run_job(JOB_NAME)
            status = dp.wait_for_job_status(JOB_NAME, timeout_ms=300_000, poll_ms=10_000)
        results.append((f"job has a successful backup (got {status!r})", status == "Successful"))

        flr = FileLevelRecoveryPage(page)
        flr.recover_file_level(JOB_NAME)
        page.wait_for_timeout(2000)
        flr.click_next()
        page.wait_for_timeout(2000)
        flr.wait_files_ready(timeout=120_000)

        c_rows = flr.list_folder_contents(["C:"])
        results.append((
            f"C: listing shows TestData_ForFLB (got {[r['name'] for r in c_rows]!r})",
            any(r["name"] == "TestData_ForFLB" for r in c_rows),
        ))

        data_rows = flr.list_folder_contents(["TestData_ForFLB"])
        results.append((
            f"TestData_ForFLB listing is non-empty (got {len(data_rows)} rows)",
            len(data_rows) > 0,
        ))
        if data_rows:
            print(f"[{TC}] TestData_ForFLB contents: {data_rows}")

        flr.click_cancel()
        page.wait_for_timeout(1000)

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
