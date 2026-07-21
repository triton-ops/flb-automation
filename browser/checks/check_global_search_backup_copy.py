"""NJM-70402 — Global Search, 'Backups' filter: search for an existing FLB job's backup, confirm
it appears in the results (scoped to the 'Backups' category, disambiguated by owning job — see
GlobalSearchPage.find_backup_row_by_job()'s docstring), click its row's own 'Backup copy' action,
confirm this launches the Backup Copy wizard PRE-SELECTED with that backup as source, then
complete the wizard through Finish & Run for real (Backup Copy jobs are covered by the
AUTO_FLB_* safety fence per CLAUDE.md Golden Rule 3 — this task's own instructions explicitly
authorize completing this one).

CALIBRATED live 2026-07-21 against nbr-84 — see GlobalSearchLocators'/GlobalSearchPage's own
docstrings for the full DOM writeup, and BackupCopyPage.pre_selected_backup_names()'s docstring
for the pre-selection finding (identical `pessSelViewHeader` markup FLB's own Source step uses —
no new locator needed for the wizard side, only a new reader method).

Uses the pre-existing AUTO_FLB_GSEARCH_CALIB job's backup as the source (see
check_global_search_run_job.py's own module docstring for how it was built). Creates
AUTO_FLB_GSEARCH_BACKUPCOPY_CALIB and LEAVES it in place afterward (not deleted by this script —
see this task's own report for why: both AUTO_FLB_* jobs are left for reuse by future runbooks,
matching the calibration job's own treatment).

⚠ NOT IDEMPOTENT / not safe to blindly re-run: (1) a second run will fail completing the wizard
since NBR job names must be unique and NEW_JOB_NAME already exists — this is a one-time build,
same as check_global_search_run_job.py's calibration job; (2) once this script HAS run, Global
Search's own 'Jobs' popover for the SOURCE backup (boId 436) switches its displayed owning-job
link from OWNING_JOB_NAME to NEW_JOB_NAME — a real, live product finding documented in full in
check_global_search_flr.py's own module docstring (which deliberately targets a DIFFERENT,
unaffected backup for exactly this reason) — not a defect in this script or its POM.

Run: cd browser && python checks/check_global_search_backup_copy.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.backup_types.backup_copy_page import BackupCopyPage
from pom.base.config import load_app_config
from pom.base.driver import browser_page
from pom.common.data_protection_page import DataProtectionPage
from pom.common.global_search_page import GlobalSearchPage
from pom.common.login_page import LoginPage

TC = "check_global_search_backup_copy"
SOURCE_BACKUP_NAME = "Window11"
OWNING_JOB_NAME = "AUTO_FLB_GSEARCH_CALIB"
# CALIBRATED live 2026-07-21: this wizard's own Destination combo does NOT list every repo from
# test-data/environment.md (NFS_REPO/Wasabi_Repo/CIFS_REPO were absent live, most likely gated by
# source-backup-type compatibility) — Local-Immutable IS present and is a fast, local, distinct-
# from-source (Onboard repository) disk target, so it's used here instead.
DESTINATION_REPO = "Local-Immutable"
NEW_JOB_NAME = "AUTO_FLB_GSEARCH_BACKUPCOPY_CALIB"


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

        gs = GlobalSearchPage(page)
        gs.open()
        gs.select_only_filter("Backups")
        gs.search(SOURCE_BACKUP_NAME)

        row_count = gs.result_row_count(SOURCE_BACKUP_NAME, category="Backups")
        check(f"search for {SOURCE_BACKUP_NAME!r} (Backups filter) returns >=1 result", row_count >= 1,
              f"row_count={row_count}")

        try:
            idx = gs.find_backup_row_by_job(SOURCE_BACKUP_NAME, OWNING_JOB_NAME)
            check(f"found a {SOURCE_BACKUP_NAME!r} backup row owned by {OWNING_JOB_NAME!r}", True, f"nth={idx}")
        except ValueError as exc:
            check(f"found a {SOURCE_BACKUP_NAME!r} backup row owned by {OWNING_JOB_NAME!r}", False, str(exc))
            print(f"\n[{TC}] ABORTING — cannot proceed without the owning row.")
            return 1

        gs.open_backup_copy(SOURCE_BACKUP_NAME, nth=idx)

        bc = BackupCopyPage(page)
        url = page.url
        check("clicking 'Backup copy' navigates to the New Backup Copy Job Wizard (jobType=BACKUP_COPY)",
              "jobType=BACKUP_COPY" in url, f"url={url}")

        step_title = bc.current_step_title()
        check("wizard opens on step '1. Backups'", step_title == "1. Backups", f"step_title={step_title!r}")

        pre_selected = bc.pre_selected_backup_names()
        check(f"step 1's selected-items panel is PRE-POPULATED with {SOURCE_BACKUP_NAME!r} "
              "(no manual tree selection needed)",
              any(SOURCE_BACKUP_NAME in name for name in pre_selected), f"pre_selected={pre_selected}")

        # --- complete the wizard for real (explicitly authorized by this task) ---
        bc.click_next()  # Backups -> Destination (source is already pre-selected, see above)
        step_title = bc.current_step_title()
        check("Next advances Backups -> Destination", step_title == "2. Destination", f"step_title={step_title!r}")

        bc.select_repository(DESTINATION_REPO)
        bc.click_next()  # Destination -> Schedule
        step_title = bc.current_step_title()
        check("Next advances Destination -> Schedule", step_title == "3. Schedule", f"step_title={step_title!r}")

        bc.set_run_on_demand()
        bc.click_next()  # Schedule -> Options
        step_title = bc.current_step_title()
        check("Next advances Schedule -> Options", step_title == "4. Options", f"step_title={step_title!r}")

        bc.set_job_name(NEW_JOB_NAME)
        bc.finish_and_run()
        page.wait_for_timeout(1500)
        try:
            bc.confirm_run()
        except Exception as exc:  # noqa: BLE001
            print("confirm_run note:", exc)
        page.wait_for_timeout(2000)

        dp = DataProtectionPage(page)
        dp.open()
        page.wait_for_timeout(1500)
        try:
            dp.select_job_row(NEW_JOB_NAME)
            exists = True
        except Exception:  # noqa: BLE001
            exists = False
        check(f"{NEW_JOB_NAME} exists in the Jobs sidebar after Finish & Run", exists)

        status = dp.wait_for_job_status(NEW_JOB_NAME, timeout_ms=300_000, poll_ms=10_000)
        check(f"job {NEW_JOB_NAME} reached a terminal status", status in ("Successful", "Failed", "Stopped"),
              f"status={status!r}")
        check(f"job {NEW_JOB_NAME} completed successfully", status == "Successful", f"status={status!r}")

    print(f"\n[{TC}] results:")
    for label, passed, detail in r:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}   {detail}")
    allpass = all(p for _, p, _ in r)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL — see above'}")
    print(f"[{TC}] job {NEW_JOB_NAME!r} was LEFT IN PLACE (not deleted) — see module docstring.")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
