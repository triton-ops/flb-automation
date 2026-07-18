"""Calibration/regression check for RepositoryManagementPage -- Self-Healing (NJM-85730) and
Reclaim unused space (NJM-85733). CALIBRATED live 2026-07-18 against nbr-84.

Part A (Self-Healing): triggers 'Run repository self-healing' on Local-Immutable (a LOCAL-type
repo -- self-healing is confirmed LOCAL-repo-only, see RepositoryManagementLocators' docstring)
and polls the global Activities panel for its 0%->Completed transition.

Part B (Reclaim unused space): the action is confirmed to exist in the DOM but renders
hidden+disabled ('No space can be reclaimed') whenever a repository has nothing reclaimable --
which is the default/observed state for every repo checked live. To actually exercise it, this
script builds one small, dedicated, safety-fenced AUTO_FLB_RECLAIM_CALIB job against the Onboard
repository, runs it once, deletes the job+backup (freeing space), and then checks whether
'Reclaim unused space' becomes enabled -- reporting exactly what is observed either way.

Run: cd browser && python checks/check_repository_reclaim_and_selfheal.py   (add --headed)
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
from pom.common.locators import RepositoryManagementLocators as RL
from pom.common.login_page import LoginPage
from pom.common.repository_management_page import RepositoryManagementPage

TC = "check_repository_reclaim_and_selfheal"
JOB_NAME = "AUTO_FLB_RECLAIM_CALIB"
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

        # ---------------- Part A: Self-Healing (NJM-85730) ----------------
        rp = RepositoryManagementPage(page)
        rp.open()
        rp.open_repository("Local-Immutable")
        page.screenshot(path=str(SHOTS / f"{TC}_A_repo_before.png"), full_page=False)

        available = rp.self_healing_available()
        check("Local-Immutable: 'Run repository self-healing' offered (LOCAL-type repo)", available)
        rp.close_overflow_menu()

        if available:
            rp.open_overflow_menu()
            page.locator(RL.RUN_SELF_HEALING).locator("visible=true").first.click()
            page.wait_for_timeout(700)
            page.screenshot(path=str(SHOTS / f"{TC}_A_confirm_dialog.png"), full_page=False)
            page.locator(RL.SELF_HEALING_START_BUTTON).first.click()
            page.wait_for_timeout(1500)

            rp.open_activities()
            page.wait_for_timeout(1500)
            txt = rp.activities_text()
            check("Activities panel shows a 'Backup repository self-healing: Local-Immutable' entry",
                  "self-healing" in txt.lower() and "local-immutable" in txt.lower())
            page.screenshot(path=str(SHOTS / f"{TC}_A_activities_running.png"), full_page=False)

            waited, done = 0, False
            while waited < 60000:
                page.reload()
                page.wait_for_timeout(1500)
                txt = rp.activities_text()
                idx = txt.lower().find("self-healing")
                snippet = txt[max(0, idx - 10):idx + 120] if idx >= 0 else ""
                if "completed" in snippet.lower():
                    done = True
                    break
                page.wait_for_timeout(5000)
                waited += 6500
            check("Repository self-healing reached 'Completed' in the Activities panel", done,
                  f"waited~{waited}ms")
            page.screenshot(path=str(SHOTS / f"{TC}_A_activities_final.png"), full_page=False)

        # ---------------- Part B: Reclaim unused space (NJM-85733) ----------------
        # baseline: confirm current (expected) hidden/disabled state on Onboard repository
        rp.open()
        rp.open_repository("Onboard repository")
        baseline_available = rp.reclaim_available()
        baseline_reason = rp.menu_item_disabled_reason(RL.RECLAIM_UNUSED_SPACE)
        check("Onboard repository: 'Reclaim unused space' baseline is hidden/disabled "
              "(No space can be reclaimed)", not baseline_available, f"reason={baseline_reason!r}")
        rp.close_overflow_menu()

        # build + run + delete a tiny dedicated job to free some space, then re-check
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
        flb.set_run_on_demand()
        flb.click_next()  # Options
        flb.set_job_name(JOB_NAME)
        flb.finish_and_run()
        page.wait_for_timeout(1500)
        try:
            flb.confirm_run()
        except Exception as exc:  # noqa: BLE001
            print("confirm_run note:", exc)

        dp = DataProtectionPage(page)
        dp.open()
        page.wait_for_timeout(1500)
        status = dp.wait_for_job_status(JOB_NAME, timeout_ms=180_000, poll_ms=10_000)
        check(f"job {JOB_NAME} reached a terminal status", status == "Successful", f"status={status!r}")

        jm = JobManagementPage(page)
        jm.delete_job(JOB_NAME)
        page.wait_for_timeout(2000)

        rp.open()
        rp.open_repository("Onboard repository")
        after_delete_available = rp.reclaim_available()
        after_delete_reason = rp.menu_item_disabled_reason(RL.RECLAIM_UNUSED_SPACE)
        check("Onboard repository: 'Reclaim unused space' becomes available after deleting a backup",
              after_delete_available, f"reason={after_delete_reason!r}")
        page.screenshot(path=str(SHOTS / f"{TC}_B_after_delete.png"), full_page=False)

        if after_delete_available:
            page.locator(RL.RECLAIM_UNUSED_SPACE).locator("visible=true").first.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=str(SHOTS / f"{TC}_B_reclaim_clicked.png"), full_page=False)
            rp.open_activities()
            page.wait_for_timeout(1500)
            txt = rp.activities_text()
            has_entry = "reclaim" in txt.lower()
            check("Activities panel shows a reclaim-related entry after clicking it", has_entry,
                  "(see printed text below)" if has_entry else "no 'reclaim' text found in Activities")
            print("---- activities text after reclaim click ----")
            print(txt[:1200])
            page.screenshot(path=str(SHOTS / f"{TC}_B_activities_after_reclaim.png"), full_page=False)
        else:
            print("Reclaim unused space did NOT become available after deleting one small backup -- "
                  "documenting as an honest open finding (may need aged/expired recovery points, "
                  "not just a deleted backup, or a longer async delay before it's recalculated).")

    print(f"\n[{TC}] results:")
    for label, passed, detail in r:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}   {detail}")
    allpass = all(p for _, p, _ in r)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL/FINDINGS -- see above, this is exploratory'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
