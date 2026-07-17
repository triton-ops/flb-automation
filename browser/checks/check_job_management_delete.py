"""Calibration/regression check for JobManagementPage.delete_job() — CALIBRATED live
2026-07-15 against nbr-84.

Builds a throwaway AUTO_FLB_ job, deletes it via the Manage -> Delete UI flow, and confirms it
is gone from the Jobs list afterward. Also confirms the safety-fence check refuses a
non-AUTO_FLB_/AUTO_FSB_ name without touching the browser at all.

Run: cd browser && python checks/check_job_management_delete.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.backup_types.flb_wizard_page import FlbWizardPage
from pom.base.config import load_app_config
from pom.base.driver import browser_page
from pom.common.data_protection_page import DataProtectionPage
from pom.common.job_management_page import JobManagementPage
from pom.common.locators import DataProtectionLocators
from pom.common.login_page import LoginPage

TC = "check_job_management_delete"
JOB_NAME = "AUTO_FLB_CHECK_JOB_MGMT_DELETE"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_app_config().flb
    results = []

    # 1) safety fence: no browser needed, must raise before touching anything
    with browser_page(headless=not args.headed) as page:
        jm = JobManagementPage(page)
        try:
            jm.delete_job("FLB_SomeDiscoveredJob")
            results.append(("safety fence rejects non-AUTO_FLB_/AUTO_FSB_ name", False))
        except ValueError:
            results.append(("safety fence rejects non-AUTO_FLB_/AUTO_FSB_ name", True))

        # 2) build a throwaway job, then delete it via the UI
        LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
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

        DataProtectionPage(page).open()
        page.wait_for_timeout(1500)
        found_before = page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count() > 0
        results.append((f"job {JOB_NAME} exists after build", found_before))

        jm.delete_job(JOB_NAME)
        page.wait_for_timeout(1500)
        DataProtectionPage(page).open()
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
