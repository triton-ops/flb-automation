"""Calibration/regression check for the FLB Options step's 4 previously-uncovered controls
(suite D, NJM-182722) — CALIBRATED live 2026-07-19 against nbr-84:
  1. 'Access Control List:' combo          -> FlbWizardPage.set_acl_mode()/get_acl_mode()
  2. 'Full Backup Settings' section         -> set_full_backup_mode()/set_full_backup_frequency()
  3. 'App-aware mode:' combo                -> set_app_aware_mode()/get_app_aware_mode()
  4. 'Limit a concurrent task to' field      -> set_concurrent_task_limit()/get_concurrent_task_limit()

Builds a real AUTO_FLB_OPTIONS_STEP_CALIB job (Window11 -> TestData_ForFLB -> Onboard
repository, run-on-demand schedule) exercising all 4 controls at once, asserts each combo/field
reads back the value just set (on the Options step itself, before Finish), then runs the job to
completion via Finish & Run and inspects the resulting recovery point for any UI marker that
distinguishes an Active-full savepoint from a Synthetic-full one. Cleans up via
JobManagementPage.delete_job() on the way out regardless of pass/fail.

Frequency is deliberately kept on 'Job runs #' (with everyJobRuns=1) rather than one of the
calendar-based options (First/Second/.../Day #): those are GATED disabled under this job's
run-on-demand schedule (see OptionsLocators.CREATE_FULL_BACKUP_FREQUENCY_COMBO_INPUT's docstring)
— 'Job runs #' with N=1 is the one frequency that both works under run-on-demand AND forces the
very first (only) run to be a full backup, which is what we need to inspect the recovery point.

Run: cd browser && python checks/check_options_step_extended.py   (add --headed to watch)
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

TC = "check_options_step_extended"
JOB_NAME = "AUTO_FLB_OPTIONS_STEP_CALIB"
SHOTS = Path(__file__).resolve().parent.parent.parent / "results" / "screenshots"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_app_config().flb
    r: list[tuple[str, bool, str]] = []

    def check(label: str, passed: bool, detail: str = ""):
        r.append((label, bool(passed), detail))
        print(f"   {'PASS' if passed else 'FAIL'}  {label}  {detail}")

    with browser_page(headless=not args.headed, trace_name=TC) as page:
        LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
        jm = JobManagementPage(page)

        # idempotency: remove any leftover job from a previous/interrupted run first
        DataProtectionPage(page).open()
        page.wait_for_timeout(1500)
        if page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count() > 0:
            jm.delete_job(JOB_NAME)
            page.wait_for_timeout(1500)

        # --- build the job ---
        DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
        flb = FlbWizardPage(page).on_sources_step()
        flb.expand_windows()
        flb.select_machine("Window11")
        flb.open_item_picker()
        flb.wait(1500)
        flb.select_items(["Local Disk (C:)"], ["TestData_ForFLB"])
        flb.picker_apply()
        flb.click_next()  # Inclusion
        flb.click_next()  # Exclusion
        flb.click_next()  # Destination
        flb.select_repository("Onboard repository")
        flb.click_next()  # Schedule
        page.wait_for_timeout(800)
        flb.set_run_on_demand()
        flb.click_next()  # Options
        page.wait_for_timeout(1500)

        # 1) Access Control List
        flb.set_acl_mode("Back up folder and file permissions")
        acl_readback = flb.get_acl_mode()
        check("ACL combo reads back 'Back up folder and file permissions'",
              acl_readback == "Back up folder and file permissions", f"got {acl_readback!r}")

        # 2) App-aware mode (set_app_aware_mode() dismisses the 'Application-Aware Mode'
        # per-machine credentials dialog this pops — see its own docstring)
        flb.set_app_aware_mode("Enabled (proceed on error)")
        appaware_readback = flb.get_app_aware_mode()
        check("App-aware mode combo reads back 'Enabled (proceed on error)'",
              appaware_readback == "Enabled (proceed on error)", f"got {appaware_readback!r}")

        # 3) Full Backup Settings: mode + frequency
        flb.set_full_backup_mode("Active full")
        fullmode_readback = flb.get_full_backup_mode()
        check("Full backup mode combo reads back 'Active full'",
              fullmode_readback == "Active full", f"got {fullmode_readback!r}")

        flb.set_full_backup_frequency("Job runs #", every_job_runs=1)
        freq_readback = flb.get_full_backup_frequency()
        runs_readback = flb.get_full_backup_every_job_runs()
        check("Create-full-backup frequency combo reads back 'Job runs #'",
              freq_readback == "Job runs #", f"got {freq_readback!r}")
        check("everyJobRuns spinner reads back '1'", runs_readback == "1", f"got {runs_readback!r}")

        # 4) concurrent task limit
        flb.set_concurrent_task_limit(2)
        limit_readback = flb.get_concurrent_task_limit()
        check("concurrent-task-limit field reads back '2'", limit_readback == "2", f"got {limit_readback!r}")

        page.screenshot(path=str(SHOTS / f"{TC}_options_step_set.png"), full_page=True)

        flb.set_job_name(JOB_NAME)
        flb.finish_and_run()
        page.wait_for_timeout(1500)
        try:
            flb.confirm_run()
        except Exception as exc:  # noqa: BLE001
            print("confirm_run note:", exc)
        page.wait_for_timeout(2000)

        # --- confirm the job built and reached a terminal state ---
        dp = DataProtectionPage(page)
        dp.open()
        page.wait_for_timeout(1500)
        found = page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count() > 0
        check(f"job {JOB_NAME} exists in sidebar after build", found)

        status = dp.wait_for_job_status(JOB_NAME, timeout_ms=300_000, poll_ms=10_000)
        check(f"job {JOB_NAME} reached a terminal status", status == "Successful", f"status={status!r}")
        page.screenshot(path=str(SHOTS / f"{TC}_job_dashboard_final.png"), full_page=False)

        # --- inspect the recovery point for an Active-full vs Synthetic-full UI marker ---
        page.locator("//*[normalize-space()='Settings']").first.click()
        page.wait_for_timeout(1200)
        page.locator("//*[normalize-space()='Repositories']").first.click()
        page.wait_for_timeout(1800)
        page.locator("//*[normalize-space()='Onboard repository']").first.click()
        page.wait_for_timeout(1800)
        try:
            page.locator("//a[normalize-space()='Window11']").first.click()
            page.wait_for_timeout(1800)
            page.screenshot(path=str(SHOTS / f"{TC}_backup_detail.png"), full_page=True)
            backup_text = page.locator("body").inner_text()
            print("---- backup/recovery-point detail text (first 2000 chars) ----")
            print(backup_text[:2000])
            has_full_marker = ("full" in backup_text.lower())
            check("backup/recovery-point detail page mentions 'full' anywhere (candidate marker "
                  "text — inspect the printed detail/screenshot above to see if it actually "
                  "distinguishes Active vs Synthetic, or is just the generic 'Full' backup-type "
                  "column shared by both)", has_full_marker, "(see printed detail text/screenshot)")
        except Exception as exc:  # noqa: BLE001
            check("backup/recovery-point detail page inspected for a full-mode marker", False, f"EXCEPTION: {exc}")

        # --- cleanup ---
        dp.open()
        page.wait_for_timeout(1500)
        try:
            jm.delete_job(JOB_NAME)
            page.wait_for_timeout(1500)
            dp.open()
            page.wait_for_timeout(1500)
            still_there = page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count() > 0
            check(f"job {JOB_NAME} deleted (cleanup)", not still_there, f"still_there={still_there}")
        except Exception as exc:  # noqa: BLE001
            check(f"job {JOB_NAME} delete attempt raised — INSPECT MANUALLY, do not assume clean",
                  False, f"EXCEPTION: {exc}")

    print(f"\n[{TC}] results:")
    for label, passed, detail in r:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}   {detail}")
    allpass = all(p for _, p, _ in r)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL/FINDINGS — see above'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
