"""NJM-70399 — Global Search, 'Jobs & Groups' filter: search for an existing FLB job by name,
confirm it appears in the results (scoped to the 'Jobs & Groups' category), click its row's own
'Run' action, confirm the 'Run this job?' dialog, and poll the job's dashboard until it reaches a
terminal status.

CALIBRATED live 2026-07-21 against nbr-84 — see GlobalSearchLocators'/GlobalSearchPage's own
docstrings in browser/pom/common/locators.py / global_search_page.py for the full DOM writeup.
Uses the pre-existing AUTO_FLB_GSEARCH_CALIB job (built once via a throwaway calibration script,
left in place for reuse — see this task's own report) — NEVER creates/deletes a job itself, so
there is nothing to clean up: the safety fence (CLAUDE.md) only allows touching AUTO_FLB_*
entities, and this one is intentionally left running/idle for future reuse.

Run: cd browser && python checks/check_global_search_run_job.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.base.config import load_app_config
from pom.base.driver import browser_page
from pom.common.data_protection_page import DataProtectionPage
from pom.common.global_search_page import GlobalSearchPage
from pom.common.login_page import LoginPage

TC = "check_global_search_run_job"
JOB_NAME = "AUTO_FLB_GSEARCH_CALIB"


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
        gs.select_only_filter("Jobs & Groups")
        gs.search(JOB_NAME)

        row_count = gs.result_row_count(JOB_NAME, category="Jobs & Groups")
        check(f"search for {JOB_NAME!r} (Jobs & Groups filter) returns >=1 result", row_count >= 1,
              f"row_count={row_count}")
        if row_count == 0:
            check("aborting — no row to act on", False, "see previous FAIL")
            allpass = all(p for _, p, _ in r)
            return 0 if allpass else 1

        category = gs.result_category(JOB_NAME)
        check("result row's own Category cell reads 'Jobs & Groups'", category == "Jobs & Groups",
              f"category={category!r}")

        # get a pre-run status baseline from the job's own dashboard (separate DataProtectionPage
        # instance — same page/session, just a different POM wrapper for the sidebar/dashboard;
        # dp.open() is required first — get_job_status()/select_job_row() assume the Data
        # Protection Jobs sidebar is already the active view, unlike Global Search's own pages)
        dp = DataProtectionPage(page)
        dp.open()
        pre_status = dp.get_job_status(JOB_NAME)
        print(f"   (info) job status before Run: {pre_status!r}")

        gs.open()  # back to Search
        gs.select_only_filter("Jobs & Groups")
        gs.search(JOB_NAME)
        gs.run_job(JOB_NAME)

        dp.open()  # back to Data Protection to poll the job's own dashboard
        status = dp.wait_for_job_status(JOB_NAME, timeout_ms=300_000, poll_ms=10_000)
        check(f"job {JOB_NAME} reached a terminal status after Global Search 'Run'",
              status in ("Successful", "Failed", "Stopped"), f"status={status!r}")
        check(f"job {JOB_NAME} run triggered from Global Search completed successfully",
              status == "Successful", f"status={status!r}")

    print(f"\n[{TC}] results:")
    for label, passed, detail in r:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}   {detail}")
    allpass = all(p for _, p, _ in r)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL — see above'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
