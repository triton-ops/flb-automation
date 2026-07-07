"""FLR flow check (NBR 11.2.1, nbr-84): validate the File-Level Recovery entry + wizard
navigation + recovery-point mount, against the read-only golden job FLB_NFS_REPO. Executes NO
recovery and selects NO recovery type (never touches 'original location').

Verified milestones (headless, reliable): job -> Recover -> File level recovery opens the wizard;
step 1 Backup; Next -> step 2 Files; the recovery point MOUNTS ('preparing' clears); Files gates
the footer until a file/folder is picked.

Step 3 Options was CALIBRATED HEADED 2026-07-07 (see file_level_recovery_page): Recovery type =
{'Recovery to original location' (default, ⚠ overwrites source, reveals 'Overwrite behavior'),
'Recover to custom location (CIFS/NFS)', 'Download', 'Forward via email'}; final action is
'Recover'. This headless check stops at the Files gate to stay fast/reliable and NEVER executes.
Run:  cd browser && python checks/check_flr_flow.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.data_protection_page import DataProtectionPage
from pom.driver import browser_page, load_config
from pom.file_level_recovery_page import FileLevelRecoveryPage
from pom.locators import FileLevelRecoveryLocators as L
from pom.login_page import LoginPage

JOB = "FLB_NFS_REPO"
BACKUP = "Windown"
TC = "_flr_flow"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    ok = []
    with browser_page(headless=not args.headed, trace_name=TC) as page:
        LoginPage(page).open(cfg["url"]).login(cfg["user"], cfg["password"])
        DataProtectionPage(page).open()
        flr = FileLevelRecoveryPage(page)
        flr.recover_file_level(JOB)
        ok.append(("FLR wizard opened (Recover -> File level recovery)", flr.exists(L.STEP_BACKUP)))
        flr.screenshot(f"{TC}_01_backup.png", TC)
        flr.select_backup(BACKUP)
        flr.click_next()                       # -> Files
        ok.append(("reached Files step", flr.is_visible(L.STEP_FILES)))
        flr.screenshot(f"{TC}_02_files_mounting.png", TC)
        flr.wait_files_ready(timeout=180000)   # wait for RP mount
        ok.append(("recovery point mounted", flr.files_ready()))
        ok.append(("Files gates Next until a file is picked", flr.files_awaiting_selection()))
        flr.screenshot(f"{TC}_03_files_ready.png", TC)
        flr.click_cancel()                     # discard — execute nothing

    print(f"\n[{TC}] results:")
    for label, passed in ok:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}")
    allpass = all(p for _, p in ok)
    print(f"[{TC}] {'ALL PASS — FLR entry/nav/mount verified' if allpass else 'PARTIAL — see above'}")
    print(f"[{TC}] NOTE: step 3 Options recovery-type calibrated headed 2026-07-07 — "
          f"'Recovery to original location' (default, ⚠ overwrites source, reveals 'Overwrite behavior'), "
          f"'Recover to custom location (CIFS/NFS)', 'Download', 'Forward via email'. Never auto-executed.")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
