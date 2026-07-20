"""Calibration/regression check for RepositoryManagementPage's delete-all-recovery-points
support (NJM-68621 step 3: "Manually delete all recovery points from the repository" for one
job, WITHOUT deleting the job itself). CALIBRATED live 2026-07-20 against nbr-84.

Uses the REAL, already-built `AUTO_FLB_NJM-68621_rerun-after-rp-delete` job (source Window11,
target Onboard repository) which has exactly 2 recovery points going into this run. Confirms the
count, drives RepositoryManagementPage.delete_all_recovery_points(), then re-reads the count.

CALIBRATED FINDING (see RepositoryManagementLocators'/RepositoryManagementPage's own docstrings
for the full writeup): the backup detail page's top-right '...' -> Delete operates on the WHOLE
backup object, not on individually-selected recovery points, and NBR blocks it outright with
'Cannot delete the backup. This backup is used by the following item(s): <job name>' while the
job still exists — confirmed identical for both a 1-of-2 and a 2-of-2 recovery-point selection.
A repository-wide 'Delete backups in bulk' action exists but was confirmed live to have no
per-job picker at all (only global age/criteria options), so it is deliberately not used here
(would risk touching every other backup in the repository). This script reports the REAL
before/after recovery_point_count() either way — do not assume 0 remain just because the click
sequence completed without an exception.

Run: cd browser && python checks/check_delete_all_recovery_points.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.base.config import load_app_config
from pom.base.driver import browser_page
from pom.common.login_page import LoginPage
from pom.common.repository_management_page import RepositoryManagementPage

TC = "check_delete_all_recovery_points"
JOB_NAME = "AUTO_FLB_NJM-68621_rerun-after-rp-delete"
REPO_NAME = "Onboard repository"
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
        try:
            LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
        except Exception as exc:  # noqa: BLE001
            # CALIBRATED live 2026-07-20: wait_for_load_state('networkidle') inside LoginPage
            # can time out on this appliance (continuous ExtJS dashboard polling never lets the
            # network go fully idle) even though the login itself has already succeeded --
            # not a real login failure, so don't fail the check over it.
            print(f"login wait_idle note (non-fatal): {exc}")
            page.wait_for_timeout(3000)

        rp = RepositoryManagementPage(page)
        rp.open()
        rp.open_repository(REPO_NAME)
        page.wait_for_timeout(1500)

        before = rp.recovery_point_count(JOB_NAME)
        page.screenshot(path=str(SHOTS / f"{TC}_before.png"), full_page=False)
        check(f"job {JOB_NAME!r} backup shows 2 recovery points before delete", before == 2,
              f"before={before}")

        # recovery_point_count() left the page on the BACKUP's own detail page --
        # delete_all_recovery_points() needs to start from the repo detail page's own 'Backups'
        # grid (same precondition as open_backup_by_job()/open_backup()) -- go back up one
        # drilldown level via the page's own '<' button rather than re-navigating from scratch.
        rp.go_back()
        rp.delete_all_recovery_points(JOB_NAME)
        page.screenshot(path=str(SHOTS / f"{TC}_after_delete_attempt.png"), full_page=False)

        # delete_all_recovery_points() leaves the page on the backup's own detail page (whether
        # the delete succeeded or was blocked) -- read the count directly from there, no
        # re-navigation (job_name=None) needed or possible from this page.
        after = rp.recovery_point_count()
        page.screenshot(path=str(SHOTS / f"{TC}_after.png"), full_page=False)
        deleted = after == 0
        check(f"job {JOB_NAME!r} backup shows 0 recovery points after delete_all_recovery_points()",
              deleted, f"after={after}")
        if not deleted:
            print(f"[{TC}] recovery points were NOT removed -- consistent with the calibrated "
                  "finding that NBR blocks backup deletion while the owning job still exists "
                  "('Cannot delete the backup. This backup is used by the following item(s): "
                  f"{JOB_NAME}'). This is a real, reportable product/UI finding, not a script bug.")

    print(f"\n[{TC}] results:")
    for label, passed, detail in r:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}   {detail}")
    allpass = all(p for _, p, _ in r)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL/FINDINGS -- see above'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
