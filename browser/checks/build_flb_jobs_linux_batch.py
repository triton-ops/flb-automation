"""Batch-build FLB jobs from Linux sources via the REAL Director UI wizard (Playwright),
looping over multiple machines in ONE script run — the scripted alternative to raw RPC
`JobManagement.saveJob` requested 2026-07-14.

Why this exists: raw RPC-built FLB jobs on Linux sources have a confirmed UI-only defect
(indeterminate/"partial selected" checkboxes in Select Items, and an empty File Level
Recovery browse) that does NOT reproduce on jobs built through the wizard. Manually
clicking through Claude-in-Chrome proved the UI path is correct but is one-job-at-a-time
and slow. This script drives the SAME wizard via Playwright/POM instead, so multiple Linux
jobs can be built back-to-back in a single unattended run — batchable, like RPC, but
going through the real UI so it does not carry the RPC-only defect.

Each entry in MACHINES:
  ui_name    — exact machine name as shown in the Source tree (e.g. 'Rocky_Linux9')
  drill_path — folder titles to click through from the source root (e.g. ['TestData_ForFLB'])
  checks     — item name(s) to tick once inside drill_path (e.g. ['MixedTypes'])
  job_name   — must start with AUTO_FLB_ per CLAUDE.md safety fence

Builds only (Finish, not Finish & Run) — jobs from DIFFERENT source machines can be run
together afterward via RPC R5 (JobManagement.run); the "run sequentially" rule only applies
to jobs sharing the same source physical machine (not the case here — 3 distinct Linux
sources).

Run:  cd browser && python checks/build_flb_jobs_linux_batch.py   (add --headed to watch)
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
from pom.common.login_page import LoginPage

REPO = "Onboard repository"

MACHINES = [
    {
        "ui_name": "AlmaLinux9_16.48",
        "drill_path": ["TestData_ForFLB"],
        "checks": ["MixedTypes"],
        "job_name": "AUTO_FLB_NJM-67813",
    },
    {
        "ui_name": "Ubuntu2204Desktop_16.98",
        "drill_path": ["TestData_ForFLB"],
        "checks": ["MixedTypes"],
        "job_name": "AUTO_FLB_NJM-67816",
    },
    {
        "ui_name": "Ubuntu2404Desktop_16.119",
        "drill_path": ["TestData_ForFLB"],
        "checks": ["MixedTypes"],
        "job_name": "AUTO_FLB_NJM-67817",
    },
    {
        "ui_name": "Linux_16.84",
        "drill_path": [],
        "checks": ["TestData_ForFLB"],
        "job_name": "AUTO_FLB_NJM-68933",
    },
    {
        "ui_name": "Ubuntu2204Desktop_16.98",
        "drill_path": ["mnt", "xfs_testdata"],
        "checks": ["TestData_XFS"],
        "job_name": "AUTO_FLB_NJM-68934",
    },
]

TC = "_build_flb_linux_batch"


def build_one(page, m: dict) -> tuple[str, bool, str]:
    """Build one job through the wizard. Returns (job_name, ok, note)."""
    try:
        DataProtectionPage(page).open()
        DataProtectionPage(page).open_create_menu().start_file_level_backup()
        flb = FlbWizardPage(page)
        flb.on_sources_step()
        flb.expand_linux()
        flb.select_machine(m["ui_name"])
        flb.open_item_picker()
        flb.select_items(m["drill_path"], m["checks"])
        count = flb.picker_selected_count()
        flb.picker_apply()
        flb.click_next()          # -> Inclusion
        flb.click_next()          # -> Exclusion
        flb.click_next()          # -> Destination
        flb.select_repository(REPO)
        flb.click_next()          # -> Schedule
        flb.set_run_on_demand()
        flb.click_next()          # -> Options
        flb.set_job_name(m["job_name"])
        flb.finish()
        return (m["job_name"], True, f"selected={count.strip()}")
    except Exception as exc:  # noqa: BLE001 — record and continue to the next machine
        return (m["job_name"], False, f"EXCEPTION: {exc}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_app_config().flb

    results = []
    with browser_page(headless=not args.headed, trace_name=TC) as page:
        LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
        for m in MACHINES:
            name, ok, note = build_one(page, m)
            results.append((name, ok, note))
            page.screenshot(path=str(Path(__file__).resolve().parent.parent.parent
                                     / "results" / "screenshots" / f"{TC}__{name}.png"))

    print(f"\n[{TC}] results:")
    for name, ok, note in results:
        print(f"   {'PASS' if ok else 'FAIL'}  {name}  ({note})")
    allpass = all(ok for _, ok, _ in results)
    if allpass:
        summary = f"ALL PASS — batch build of {len(results)} Linux jobs via UI wizard succeeded"
    else:
        summary = "PARTIAL — see above"
    print(f"[{TC}] {summary}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
