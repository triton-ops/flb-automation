"""File Share Recovery check (NBR 11.2.1, nbr-5): validate the File Share Recovery entry +
wizard navigation + recovery-point mount, against the read-only reference job 22 ('Backup job
for file share' -> BACKUP_OBJECT-26, savepoint 44). Executes NO recovery and selects NO
recovery type (never touches 'original location').

CALIBRATED live 2026-07-08. This is FSB's distinctly-WORDED equivalent of FLB's File Level
Recovery (see check_flr_flow.py's historical structure, since deleted) — 'File share recovery'
opens a 'File Share Recovery Wizard', not a 'File Level Recovery Wizard'. Confirmed at the RPC
layer too: FileLevelRecoveryManagement.createSession needs hvType:"NAS" (not "PHYSICAL") for
an FSB backup object — see recipes/file-backup-recipes.md R7.

Verified milestones (headless, reliable): job -> Recover -> File share recovery opens the
wizard with the latest recovery point pre-selected (calendar-based step 1, not a flat
backup-name list like FLB's); Next -> step 2 Files; the recovery point MOUNTS in ~4s; Files
gates the footer reactively (only after an attempted Next click with nothing selected, same
behavior as the FLB flow's 2026-07-08 recalibration).

Job disambiguation: nbr-5 currently has 4 jobs all named 'Backup job for file share' (NBR's
generic default, never custom-named) — nth=0 is job 22 (Onboard repository, healthy). Other
indices target HPE_Repo-backed jobs not verified here.

Run:  cd browser && python checks/check_flr_file_share.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.backup_types.file_share_recovery_page import FileShareRecoveryPage
from pom.base.config import load_app_config
from pom.base.driver import browser_page
from pom.common.data_protection_page import DataProtectionPage
from pom.common.locators import FileLevelRecoveryLocators as L
from pom.common.login_page import LoginPage

JOB = "Backup job for file share"
JOB_NTH = 0   # job 22: Onboard repository, healthy, latest recovery point accessible
TC = "_flr_file_share"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_app_config().fsb
    ok = []
    with browser_page(headless=not args.headed, trace_name=TC) as page:
        LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
        DataProtectionPage(page).open()
        flr = FileShareRecoveryPage(page)
        flr.recover_file_share(JOB, nth=JOB_NTH)
        ok.append(("File Share Recovery wizard opened", flr.exists(L.STEP_BACKUP)))
        flr.screenshot(f"{TC}_01_backup.png", TC)

        flr.click_next()                       # -> Files (recovery point pre-selected on step 1)
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
    print(f"[{TC}] {'ALL PASS — File Share Recovery entry/nav/mount verified' if allpass else 'PARTIAL — see above'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
