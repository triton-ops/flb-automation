"""Framework Health Check — run BEFORE starting a test suite/session, not as part of one.

Verifies the appliance/build/framework is in a state worth spending real TC time on: Director
reachable, login works, the core UI shell renders, the Create/Backup/Recovery wizards actually
open, and a curated set of the locators this project has repeatedly found DRIFT after a build
upgrade (see locators.py's own history of 3+ recalibration dates for the same Files-step grid)
still resolve. Distinguishes "the appliance/build changed" from "this one TC has a bug" BEFORE
burning 3-4 minutes building a real job to find out the hard way — exactly the gap this project's
own architecture review flagged (no proactive drift-detection layer existed before this script).

Verdicts, per check:
    PASS    — the check's core assertion succeeded cleanly.
    WARNING — succeeded via a degraded/fallback path, or a known, documented precondition is
              missing (e.g. the recovery-wizard sentinel job hasn't been created yet) — worth
              noting, not blocking.
    FAIL    — the check's core assertion did not hold — a real signal; investigate before
              running a suite, don't assume "just retry the TC."

Overall exit code: 0 unless any check is FAIL (1). Warnings never fail the run.

Recovery-wizard check needs ONE PRE-EXISTING job to open Recover on (opening a wizard read-only
still counts as "touching" a job per this project's safety fence — see CLAUDE.md Golden Rule 3 —
so this script never reuses a *_reference_/discovered job, and never builds one on the fly either,
since a real build+run is 3-4 minutes on its own, blowing the <1min budget). Instead it uses a
small, PERSISTENT, safety-fence-compliant sentinel job named AUTO_FLB_HEALTHCHECK, created once
(see --setup-sentinel below) and left in place indefinitely. Because it starts with AUTO_FLB_,
a *generic* `cleanup_auto_flb_jobs.py --execute` run WILL sweep it up along with everything
else — that's an accepted, documented tradeoff (the safety fence is stricter than "convenient to
protect"), not a bug: if it's ever missing, this check degrades to WARNING with the exact command
to recreate it, rather than failing the whole run.

Usage:
    python browser/checks/health_check.py                  # run the 8 checks (nbr-84, FLB)
    python browser/checks/health_check.py --headed          # watch it live
    python browser/checks/health_check.py --setup-sentinel  # one-time: build+run AUTO_FLB_HEALTHCHECK
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage  # noqa: E402
from pom.backup_types.flb_wizard_page import FlbWizardPage  # noqa: E402
from pom.base.config import load_app_config  # noqa: E402
from pom.base.driver import browser_page  # noqa: E402
from pom.common.data_protection_page import DataProtectionPage  # noqa: E402
from pom.common.locators import DataProtectionLocators as DP  # noqa: E402
from pom.common.locators import FileLevelRecoveryLocators as FLRL  # noqa: E402
from pom.common.locators import WizardLocators  # noqa: E402
from pom.common.login_page import LoginPage  # noqa: E402

SENTINEL_JOB = "AUTO_FLB_HEALTHCHECK"
SENTINEL_MACHINE = "Window11"
FAST_TIMEOUT_MS = 6000  # short, fail-fast budget per interaction — this script must stay under 1 min


class Check:
    def __init__(self, name: str):
        self.name = name
        self.status = "FAIL"
        self.detail = ""
        self.elapsed = 0.0


def run(name: str, checks: list[Check], fn):
    c = Check(name)
    t0 = time.time()
    try:
        c.status, c.detail = fn()
    except Exception as exc:  # noqa: BLE001 — a check's own failure IS the result, not a crash
        c.status, c.detail = "FAIL", f"{type(exc).__name__}: {exc}"
    c.elapsed = time.time() - t0
    checks.append(c)
    return c


def build_sentinel(page) -> None:
    """One-time setup: build + run the small, permanent AUTO_FLB_HEALTHCHECK job the
    recovery-wizard check opens. Takes a few minutes — NOT part of the <1min health-check
    budget itself, run this once (or again if the sentinel was ever swept by a generic cleanup
    pass) before relying on check 7."""
    dp = DataProtectionPage(page)
    dp.open()
    page.wait_for_timeout(1500)
    if page.locator(DP.sidebar_job_row(SENTINEL_JOB)).count() > 0:
        print(f"{SENTINEL_JOB} already exists — nothing to do.")
        return
    dp.open_create_menu().start_file_level_backup()
    flb = FlbWizardPage(page).on_sources_step()
    flb.expand_windows()
    flb.select_machine(SENTINEL_MACHINE)
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
    flb.set_job_name(SENTINEL_JOB)
    flb.finish()
    page.wait_for_timeout(2000)
    dp.open()
    page.wait_for_timeout(1500)
    dp.run_job(SENTINEL_JOB)
    status = dp.wait_for_job_status(SENTINEL_JOB, timeout_ms=300_000, poll_ms=10_000)
    print(f"{SENTINEL_JOB} built and run — final status: {status}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--setup-sentinel", action="store_true",
                     help="one-time: build+run the AUTO_FLB_HEALTHCHECK sentinel job, then exit")
    args = ap.parse_args()
    cfg = load_app_config().flb

    if args.setup_sentinel:
        with browser_page(headless=not args.headed) as page:
            LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
            build_sentinel(page)
        return 0

    checks: list[Check] = []
    canaries: list[tuple[str, bool]] = []
    t_start = time.time()

    def canary(page, label: str, locator: str) -> None:
        canaries.append((label, page.locator(locator).locator("visible=true").count() > 0))

    with browser_page(headless=not args.headed) as page:

        def check_reachable():
            page.goto(cfg.url, wait_until="domcontentloaded", timeout=FAST_TIMEOUT_MS)
            title = page.title()
            if "NAKIVO" not in title and page.locator("//input[@name='username']").count() == 0:
                return "FAIL", f"page loaded but doesn't look like the Director login page (title={title!r})"
            return "PASS", f"reached {cfg.url} (title={title!r})"

        run("Director reachable", checks, check_reachable)

        def check_login():
            LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
            # LoginPage.login() already waits for network-idle + a fixed settle delay; poll for
            # the login form to actually be gone rather than a URL/navigation-event wait (this
            # ExtJS SPA's client-side view transitions don't reliably fire the 'load' event
            # Playwright's wait_for_url waits on — confirmed live: it timed out here even though
            # login had genuinely succeeded).
            waited = 0
            while waited < FAST_TIMEOUT_MS:
                if page.locator("//input[@name='username']").locator("visible=true").count() == 0:
                    break
                page.wait_for_timeout(500)
                waited += 500
            if page.locator("//input[@name='username']").locator("visible=true").count() > 0:
                return "FAIL", "still showing the login form after login()"
            return "PASS", f"logged in, landed on {page.url}"

        login_check = run("Login works", checks, check_login)
        if login_check.status == "FAIL":
            # Everything downstream needs an authenticated session — no point pretending
            # otherwise, and each subsequent check would just report the same root cause.
            for name in ["Core menu exists", "Jobs page loads", "Create menu opens",
                         "Backup wizard opens", "Recovery wizard opens", "Core locators exist"]:
                c = Check(name)
                c.status, c.detail = "FAIL", "skipped — login did not succeed"
                checks.append(c)
            return report(checks, t_start)

        def check_core_menu():
            # The left nav's own icon containers — CALIBRATED live 2026-07-17: matches the
            # 'itemMenuSidebar' class observed on the Data Protection nav icon during this
            # session's own manual browser inspection.
            count = page.locator("//div[contains(@class,'itemMenuSidebar')]").locator("visible=true").count()
            if count == 0:
                return "FAIL", "no left-nav menu icons found"
            return "PASS", f"{count} left-nav menu icon(s) present"

        run("Core menu exists", checks, check_core_menu)

        def check_jobs_page():
            DataProtectionPage(page).open()
            page.wait_for_timeout(1500)
            found = page.locator("//div[contains(@class,'jobDashboardNavigator')]").count() > 0
            canary(page, "Jobs sidebar container (jobDashboardNavigator)",
                   "//div[contains(@class,'jobDashboardNavigator')]")
            if not found:
                return "FAIL", "Jobs sidebar container (jobDashboardNavigator) not found"
            return "PASS", "Jobs sidebar container present"

        run("Jobs page loads", checks, check_jobs_page)

        def check_create_menu():
            DataProtectionPage(page).open_create_menu()
            page.wait_for_timeout(800)
            # Real menu labels (DataProtectionLocators) — not guessed text. CALIBRATED live
            # 2026-07-17: the File Share item reads 'Backup for file share', not 'File share
            # backup' — an earlier version of this check used the wrong guessed string and
            # reported a false WARNING here.
            items = {
                "File level backup": page.locator(DP.MENU_FLB).locator("visible=true").count() > 0,
                "Backup copy": page.locator(DP.MENU_BACKUP_COPY).locator("visible=true").count() > 0,
                "Backup for file share": page.locator(DP.MENU_FILE_SHARE).locator("visible=true").count() > 0,
            }
            for label, ok in items.items():
                canaries.append((f"Create menu item: {label}", ok))
            # CALIBRATED live 2026-07-17: Escape does NOT close this ExtJS popup menu (it's a
            # custom floating layer, not a native dialog) — left it open, which then intercepted
            # every subsequent click and cascaded a false FAIL into the next two checks. A click
            # well outside the popup (ExtJS's own click-away dismissal) actually closes it.
            page.mouse.click(5, 5)
            page.wait_for_timeout(500)
            found = sum(items.values())
            if found == 0:
                return "FAIL", "Create menu opened but none of the expected job-type items appeared"
            if found < len(items):
                return "WARNING", f"only {found}/{len(items)} expected Create-menu items found: {items}"
            return "PASS", "all expected Create-menu items present"

        run("Create menu opens", checks, check_create_menu)

        def check_backup_wizard():
            DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
            flb = FlbWizardPage(page).on_sources_step()
            source_step_ok = page.locator(WizardLocators.STEP_SOURCE).locator("visible=true").count() > 0
            for label, loc in [("Wizard Next button", WizardLocators.NEXT),
                                ("Wizard Cancel button", WizardLocators.CANCEL),
                                ("Wizard step: 1. Source", WizardLocators.STEP_SOURCE),
                                ("Wizard step: 6. Options", WizardLocators.STEP_OPTIONS)]:
                canary(page, label, loc)
            flb.click_cancel()
            page.wait_for_timeout(800)
            if not source_step_ok:
                return "FAIL", "FLB wizard opened but the '1. Source' step tab never appeared"
            return "PASS", "FLB wizard opened on the Source step"

        run("Backup wizard opens", checks, check_backup_wizard)

        def check_recovery_wizard():
            DataProtectionPage(page).open()
            page.wait_for_timeout(1200)
            if page.locator(DP.sidebar_job_row(SENTINEL_JOB)).count() == 0:
                return ("WARNING",
                        f"sentinel job {SENTINEL_JOB!r} doesn't exist yet — run "
                        f"'python browser/checks/health_check.py --setup-sentinel' once, then rerun "
                        f"this check. Not treated as FAIL: this is a one-time local setup gap, not "
                        f"an appliance/build problem.")
            flr = FileLevelRecoveryPage(page)
            # NOTE: FLRL.RECOVER_BUTTON is deliberately NOT re-checked as a canary here —
            # recover_file_level() (below) already had to click it successfully to get this far,
            # so checking it again once the wizard modal covers it would just report a false
            # 'missing' (it's covered, not broken) for a locator already proven working this call.
            flr.recover_file_level(SENTINEL_JOB)
            page.wait_for_timeout(2000)
            backup_step_ok = page.locator(FLRL.STEP_BACKUP).locator("visible=true").count() > 0
            for label, loc in [("FLR step: 1. Backup", FLRL.STEP_BACKUP),
                                ("FLR step: 2. Files", FLRL.STEP_FILES),
                                ("FLR step: 3. Options", FLRL.STEP_OPTIONS)]:
                canary(page, label, loc)
            flr.click_cancel()
            page.wait_for_timeout(800)
            if not backup_step_ok:
                return "FAIL", "Recover > File level recovery opened but the '1. Backup' step never appeared"
            return "PASS", "FLR wizard opened on the Backup step"

        run("Recovery wizard opens", checks, check_recovery_wizard)

        def check_core_locators():
            total = len(canaries)
            passed = sum(1 for _, ok in canaries if ok)
            failed = [label for label, ok in canaries if not ok]
            detail = f"{passed}/{total} canary locators resolved" + (f" — missing: {failed}" if failed else "")
            if total == 0:
                return "WARNING", "no canary locators were collected (earlier checks may have failed first)"
            if passed == total:
                return "PASS", detail
            if passed >= total * 0.7:
                return "WARNING", detail
            return "FAIL", detail

        run("Core locators exist", checks, check_core_locators)

    return report(checks, t_start)


def report(checks: list[Check], t_start: float) -> int:
    total_elapsed = time.time() - t_start
    width = max(len(c.name) for c in checks)
    print(f"\n{'FRAMEWORK HEALTH CHECK':^{width + 30}}")
    print("-" * (width + 30))
    for c in checks:
        print(f"  [{c.status:^7}] {c.name:<{width}}  ({c.elapsed:.1f}s)  {c.detail}")
    print("-" * (width + 30))
    n_fail = sum(1 for c in checks if c.status == "FAIL")
    n_warn = sum(1 for c in checks if c.status == "WARNING")
    verdict = "FAIL" if n_fail else ("PASS (with warnings)" if n_warn else "PASS")
    print(f"  Overall: {verdict} — {len(checks) - n_fail - n_warn} pass, {n_warn} warning, "
          f"{n_fail} fail — total {total_elapsed:.1f}s")
    if total_elapsed > 60:
        print(f"  NOTE: exceeded the 1-minute budget ({total_elapsed:.1f}s) — appliance may be under load.")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
