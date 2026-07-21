"""NJM-70385 — Global Search, 'Backups' filter: search for an existing FLB job's backup, confirm
it appears in the results (scoped to the 'Backups' category, disambiguated by owning job — see
GlobalSearchPage.find_backup_row_by_job()'s docstring), click its row's own 'File level recovery'
action (under 'GRANULAR RECOVERY'), and confirm this launches the File Level Recovery wizard for
that backup, pre-selected with its latest recovery point.

Browse-only, per this task's explicit constraint: ticks the root node to reach the Files step and
satisfy its selection gate, but NEVER clicks the final 'Recover' action — cancels out via
click_cancel() instead (the existing 'browse != execute' distinction this project already uses
elsewhere, e.g. check_overwrite_behavior_combo.py).

CALIBRATED live 2026-07-21 against nbr-84 — see GlobalSearchLocators'/GlobalSearchPage's own
docstrings for the full DOM writeup. No new FileLevelRecoveryPage locators/methods were needed:
this entry point renders the IDENTICAL step 1/2 markup ('Recovery point is being prepared for
file recovery. Please wait...', the Table-view recovery-point picker, etc.) the existing
Data-Protection-launched flow already drives, and click_cancel() already handles this entry's own
'Close the wizard?' confirm (its own button reads 'Cancel', not 'Close' — the same finding
already documented for the FSB 'File Share Recovery Wizard' case).

Uses the pre-existing, read-only reference job FLB_Win11's own backup as the search target — NOT
the AUTO_FLB_GSEARCH_CALIB calibration job's backup. This is deliberate, not an oversight: FLR is
strictly browse-only (never executes a recovery, per this task's own constraint), so reading
FLB_Win11's backup via Global Search is safe under the safety fence (no Run/Edit/Manage/Delete is
ever touched — see CLAUDE.md Golden Rule 3), and it sidesteps a REAL, LIVE product finding hit
during this task's own calibration: once check_global_search_backup_copy.py's Backup Copy job has
run against AUTO_FLB_GSEARCH_CALIB's backup, that SAME backup object's own 'Jobs' popover section
in Global Search switches from showing 'AUTO_FLB_GSEARCH_CALIB' to showing the Backup Copy job's
name instead (confirmed via the FLR wizard's own boId query-string parameter staying IDENTICAL
before/after — same backup object, 436, just a different 'owning job' label shown). NBR's Global
Search appears to attribute a backup's 'Jobs' link to whichever job MOST RECENTLY referenced it,
not a fixed creator/owner or an exhaustive list of every job that has ever touched it — worth
flagging as a genuine UX/product finding (a user relying on this popover to identify "which job
made this backup" could be misled once ANY other job, including a Backup Copy job, has since
touched the same backup), not a POM bug. Targeting FLB_Win11 (a job this pass never runs a Backup
Copy job against) avoids depending on that attribution staying stable across repeat runs of this
script. Creates/deletes nothing of its own — nothing to clean up.

Run: cd browser && python checks/check_global_search_flr.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from pom.base.config import load_app_config
from pom.base.driver import browser_page
from pom.common.global_search_page import GlobalSearchPage
from pom.common.locators import GlobalSearchLocators
from pom.common.login_page import LoginPage

TC = "check_global_search_flr"
SOURCE_BACKUP_NAME = "Window11"
OWNING_JOB_NAME = "FLB_Win11"


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

        gs.open_file_level_recovery(SOURCE_BACKUP_NAME, nth=idx)

        flr = FileLevelRecoveryPage(page)
        url = page.url
        check("clicking 'File level recovery' navigates to the FLR Wizard (jobType=FILE_LEVEL_RECOVERY)",
              "jobType=FILE_LEVEL_RECOVERY" in url, f"url={url}")

        step_title = flr.current_step_title()
        check("wizard opens on step '1. Backup'", step_title == "1. Backup", f"step_title={step_title!r}")

        points = flr.list_recovery_points()
        check("step 1's recovery-point picker is PRE-POPULATED with >=1 real recovery point "
              "(no manual job/machine selection needed)", len(points) >= 1, f"points={points}")
        check("one recovery point is pre-selected by default", any(p["selected"] for p in points),
              f"points={points}")

        flr.click_next()  # Backup -> Files
        page.wait_for_timeout(1000)
        step_title = flr.current_step_title()
        check("Next advances Backup -> Files", step_title == "2. Files", f"step_title={step_title!r}")

        flr.wait_files_ready(timeout=180_000)
        check("recovery point finished mounting ('preparing' message cleared)", flr.files_ready())

        flr.select_root()  # satisfy the Files-step selection gate — browse-only, no download

        # --- browse-only: cancel out, never click the final 'Recover' action ---
        flr.click_cancel()
        page.wait_for_timeout(1000)
        still_in_wizard = "jobType=FILE_LEVEL_RECOVERY" in page.url
        check("wizard closed cleanly via Cancel (never executed a recovery)", not still_in_wizard,
              f"final_url={page.url}")

        # confirm we're back somewhere the Search nav/left sidebar is reachable (not stuck)
        nav_reachable = page.locator(GlobalSearchLocators.NAV_SEARCH).locator("visible=true").count() > 0
        check("left-nav 'Search' item is reachable again after Cancel (page not stuck)", nav_reachable)

    print(f"\n[{TC}] results:")
    for label, passed, detail in r:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}   {detail}")
    allpass = all(p for _, p, _ in r)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL — see above'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
