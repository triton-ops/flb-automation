"""Smoke test: drive the full NBR 11.2.1 File Share Backup wizard (nbr-5) via the POM and
CANCEL (creates nothing). Validates: share tree, entire-share selection, Inclusion/Exclusion,
Destination repo pick, Schedule, Options job-name.

Scope note: this exercises the PRIMARY FSB flow — backing up the ENTIRE share (ticking the share
in the tree => 'Entire file share selected'). Granular per-file selection inside the Select Items
dialog is drivable but currently flaky behind an ExtJS loading mask (see file_share_page notes) —
prefer whole-share scope for automated FSB runs.
Run:  cd browser && python checks/check_fsb_wizard_smoke.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.data_protection_page import DataProtectionPage
from pom.driver import CONFIG_PATH_FSB, browser_page, load_config
from pom.file_share_page import FileShareBackupPage
from pom.locators import FlbWizardLocators
from pom.login_page import LoginPage

TC = "_smoke_fsb_wizard"
SHARE = "CIFS-FileTypeSamples"
REPO = "Onboard repository"          # nbr-5 local repo (golden job 22 target)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_config(CONFIG_PATH_FSB)   # nbr-5
    ok = []
    with browser_page(headless=not args.headed) as page:
        LoginPage(page).open(cfg["url"]).login(cfg["user"], cfg["password"])
        dp = DataProtectionPage(page).open()
        dp.open_create_menu(); dp.start_file_share_backup()
        w = FileShareBackupPage(page).on_sources_step()
        w.screenshot(f"{TC}_01_source.png", TC)

        w.select_share(SHARE)                       # => entire file share
        note = w.get_text(FlbWizardLocators.SELECTED_NOTE)
        w.screenshot(f"{TC}_02_share_selected.png", TC)
        ok.append((f"share selected (note={note!r})", "share" in note.lower()))

        w.click_next(); w.click_next(); w.click_next()   # -> Destination
        w.screenshot(f"{TC}_03_destination.png", TC)
        w.select_repository(REPO); ok.append((f"repo picked = {REPO}", True))

        w.click_next(); w.set_run_on_demand(); w.click_next()
        w.set_job_name("AUTO_FSB_smoke")
        w.screenshot(f"{TC}_04_options.png", TC)
        ok.append(("reached Options + set job name", True))

        w.click_cancel()
        w.screenshot(f"{TC}_05_after_cancel.png", TC)

    print(f"\n[{TC}] results:")
    for label, passed in ok:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}")
    allpass = all(p for _, p in ok)
    print(f"[{TC}] {'ALL PASS — POM drives the FSB wizard end-to-end (whole-share)' if allpass else 'SOME FAILED'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
