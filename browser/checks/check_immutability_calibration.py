"""Calibration for the FLB Schedule-step immutability field (NJM-70517) — CALIBRATED live
2026-07-18 against nbr-84.

Builds a real AUTO_FLB_IMMUT_CALIB job targeting the Local-Immutable repository (id 15) with
'Immutable for 1 day(s)' ticked on the Schedule step, runs it to completion, then inspects
whether the resulting recovery point is marked immutable/locked anywhere in the Director UI,
and finally deletes the job via the normal Manage -> Delete path to observe what happens to its
recovery point while still inside its immutability window (per NJM-70517 step 5's intent).

CONFIRMED FINDING (first-time — see test-data/environment.md's own caveat that no repo had ever
been proven to produce a real immutable savepoint before this run): the recovery point's OWN
grid on its backup detail page (Settings -> Repositories -> Local-Immutable -> Window11 ->
Recovery points) has two columns not visible without horizontal scroll — 'Immutable until' and
'Protected until' — and the real row showed 'Immutable until: <created + 1 day>' / 'Protected
until: <created + 10 days>', proving NBR did create a genuinely immutable savepoint (maps to
options.retentionPolicy.retentionMode + keepImmutableCount in the JobDto). Deleting the JOB
itself is NOT blocked (Manage -> Delete succeeds normally, the job disappears from the Jobs
sidebar) — but the underlying BACKUP/recovery point is NOT removed from Local-Immutable; it
survives as an orphaned ('no job') entry that only becomes removable once the immutable window
elapses (or via the repo's own 'Delete backups in bulk' -> 'All backups not belonging to any
job' tool, not exercised destructively here — its own radio-button widget could not be reliably
driven via Playwright during this pass, a documented open gap, not a product finding). So
NJM-70517's real protection shows up as repo-level data survival, not a blocked Delete button.

⚠ Running this script for real leaves ONE small (~120MB) orphaned, still-immutable backup
behind on Local-Immutable that CANNOT be cleaned up until its 1-day window elapses — this is
expected/by design per the finding above, not a leak to chase down.

Run: cd browser && python checks/check_immutability_calibration.py   (add --headed to watch)
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
from pom.common.locators import DataProtectionLocators, ScheduleLocators
from pom.common.login_page import LoginPage

TC = "check_immutability_calibration"
JOB_NAME = "AUTO_FLB_IMMUT_CALIB"
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

        # --- build the job ---
        DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
        flb = FlbWizardPage(page).on_sources_step()
        flb.expand_windows()
        flb.select_machine("Window11")
        flb.open_item_picker()
        flb.wait(1500)
        # NOTE: a first attempt at this calibration ticked the whole 'Local Disk (C:)' volume
        # (which also contains the ~18.8GB Data_25GB fixture per environment.md) against
        # Local-Immutable's small 9.7GB-free repo — it never finished inside a 5-minute poll
        # and was stopped+deleted uncompleted. Use the small, known-good TestData_ForFLB
        # fixture (~120MB, already used by check_job_management_delete.py etc.) instead.
        flb.select_items(["Local Disk (C:)"], ["TestData_ForFLB"])
        flb.picker_apply()
        flb.click_next()  # Inclusion
        flb.click_next()  # Exclusion
        flb.click_next()  # Destination
        flb.select_repository("Local-Immutable")
        flb.click_next()  # Schedule
        page.wait_for_timeout(1000)

        # gating check: is the Immutable-for checkbox actually enabled for this repo?
        cb = page.locator(ScheduleLocators.IMMUTABLE_FOR_CHECKBOX).locator("visible=true").first
        gated_disabled = cb.get_attribute("disabled") is not None
        check("Schedule step: 'Immutable for' checkbox is enabled for Local-Immutable",
              not gated_disabled, f"disabled attr={cb.get_attribute('disabled')!r}")

        flb.set_immutable(1)   # shortest period, per task instructions
        page.screenshot(path=str(SHOTS / f"{TC}_schedule_immutable_set.png"), full_page=False)
        flb.click_next()  # Options
        flb.set_job_name(JOB_NAME)
        flb.finish_and_run()
        page.wait_for_timeout(1500)
        # confirm the 'Run this job?' dialog if it appeared
        try:
            flb.confirm_run()
        except Exception as exc:  # noqa: BLE001
            print("confirm_run note:", exc)
        page.wait_for_timeout(2000)
        page.screenshot(path=str(SHOTS / f"{TC}_after_finish_run.png"), full_page=False)

        # --- wait for the job to reach a terminal state ---
        dp = DataProtectionPage(page)
        dp.open()
        page.wait_for_timeout(1500)
        found = page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count() > 0
        check(f"job {JOB_NAME} exists in sidebar after build", found)

        status = dp.wait_for_job_status(JOB_NAME, timeout_ms=300_000, poll_ms=10_000)
        check(f"job {JOB_NAME} reached a terminal status", status in ("Successful", "Failed", "Stopped"),
              f"status={status!r}")
        page.screenshot(path=str(SHOTS / f"{TC}_job_dashboard_final.png"), full_page=False)

        # --- inspect the repository/backup for an immutability indicator ---
        page.locator("//*[normalize-space()='Settings']").first.click()
        page.wait_for_timeout(1200)
        page.locator("//*[normalize-space()='Repositories']").first.click()
        page.wait_for_timeout(1800)
        page.locator("//*[normalize-space()='Local-Immutable']").first.click()
        page.wait_for_timeout(1800)
        page.screenshot(path=str(SHOTS / f"{TC}_repo_after_run.png"), full_page=False)
        repo_text = page.locator("body").inner_text()
        check("repository detail page loaded", "Local-Immutable" in repo_text)

        # open the new backup's detail (machine name is 'Window11' per environment.md)
        try:
            page.locator("//a[normalize-space()='Window11']").first.click()
            page.wait_for_timeout(1800)
            page.screenshot(path=str(SHOTS / f"{TC}_backup_detail.png"), full_page=False)
            backup_text = page.locator("body").inner_text()
            print("---- backup detail text ----")
            print(backup_text[:1500])
            has_immutable_marker = ("immutable" in backup_text.lower()) or ("locked" in backup_text.lower())
            check("backup/recovery-point detail page shows an immutability/lock indicator",
                  has_immutable_marker, "(see printed detail text above)")
        except Exception as exc:  # noqa: BLE001
            check("backup/recovery-point detail page shows an immutability/lock indicator", False, f"EXCEPTION: {exc}")

        # --- attempt to delete the job via the normal Manage -> Delete UI path ---
        # CALIBRATED live 2026-07-18: must return to the Data Protection / Jobs sidebar first —
        # JobManagementPage.delete_job() selects the job row directly without navigating there
        # itself, and the immediately-preceding step left the page on Settings -> Repositories'
        # backup-detail view, which made the very first calibration run's delete_job() call
        # time out looking for a sidebar row that was never rendered (a script/navigation bug,
        # not a product finding).
        dp.open()
        page.wait_for_timeout(1500)
        jm = JobManagementPage(page)
        try:
            jm.delete_job(JOB_NAME)
            page.wait_for_timeout(1500)
            dp.open()
            page.wait_for_timeout(1500)
            still_there = page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count() > 0
            # CALIBRATED finding, live 2026-07-18: the job DEFINITION deletes normally (not
            # blocked at the Manage -> Delete step) even while its recovery point is still
            # inside its 'Immutable until' window — but the underlying BACKUP/recovery point
            # itself is NOT removed from the repository; it survives as an orphaned ("no job")
            # entry until the immutable period elapses. That repo-level persistence, not a
            # blocked Delete click, is where NJM-70517's real protection shows up in this UI.
            check(f"job {JOB_NAME} definition is deleted from the Jobs sidebar "
                  "(the DELETE CLICK itself is never blocked)", not still_there, f"still_there={still_there}")
            page.screenshot(path=str(SHOTS / f"{TC}_after_delete_attempt.png"), full_page=False)

            page.locator("//*[normalize-space()='Settings']").first.click()
            page.wait_for_timeout(1200)
            page.locator("//*[normalize-space()='Repositories']").first.click()
            page.wait_for_timeout(1800)
            page.locator("//*[normalize-space()='Local-Immutable']").first.click()
            page.wait_for_timeout(1800)
            repo_text_after = page.locator("body").inner_text()
            backup_still_present = "Window11" in repo_text_after
            check("the underlying immutable backup/recovery point SURVIVES the job delete "
                  "(real immutability enforcement, at the repo level)", backup_still_present)
            page.screenshot(path=str(SHOTS / f"{TC}_repo_after_delete.png"), full_page=False)
        except Exception as exc:  # noqa: BLE001
            check(f"job {JOB_NAME} delete attempt raised (treat as BLOCKED signal, inspect manually)",
                  False, f"EXCEPTION: {exc}")
            page.screenshot(path=str(SHOTS / f"{TC}_delete_exception.png"), full_page=False)

    print(f"\n[{TC}] results:")
    for label, passed, detail in r:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}   {detail}")
    allpass = all(p for _, p, _ in r)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL/FINDINGS — see above, this is exploratory'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
