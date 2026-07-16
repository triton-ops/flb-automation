"""Capture the R7.4(a) listing-screenshot-pair for one job: Select Items (Edit -> Source) vs.
FLR browse (Recover -> File level recovery), saved to results/screenshots/<TC>__<stamp>/.

Usage:
    python browser/checks/capture_evidence_pair.py --tc NJM-67813 --job-id 109 \
        --machine AlmaLinux9_16.48 --path TestData_ForFLB
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.base.driver import CONFIG_PATH, browser_page, load_config
from pom.common.locators import FlbWizardLocators, SelectItemsLocators, WizardLocators, ci_exact
from pom.common.login_page import LoginPage


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tc", required=True)
    ap.add_argument("--job-id", required=True, type=int)
    ap.add_argument("--machine", required=True, help="UI machine name, e.g. AlmaLinux9_16.48")
    ap.add_argument("--path", required=True, nargs="+", help="folder names to drill, in order")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    out_dir = (Path(__file__).resolve().parent.parent.parent / "results" / "screenshots"
               / f"{args.tc}__{date.today():%Y%m%d}")
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_config(CONFIG_PATH)
    base_url = cfg["url"].rstrip("/")

    with browser_page(headless=not args.headed) as page:
        LoginPage(page).open(cfg["url"]).login(cfg["user"], cfg["password"])

        # --- Screenshot A: Edit -> Source -> Select Items ---
        page.goto(f"{base_url}/c/jobEditor?action=EDIT&jobType=FILE_LEVEL&id={args.job_id}&type=JOB",
                   wait_until="domcontentloaded")
        page.wait_for_timeout(4000)
        try:
            page.locator(ci_exact("1. Source")).first.click(timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        page.locator(FlbWizardLocators.SELECTED_HEADER).first.hover()
        page.wait_for_timeout(500)
        page.locator(FlbWizardLocators.EDIT_ICON).first.click(force=True)
        page.wait_for_timeout(2500)
        page.screenshot(path=str(out_dir / "02_selected_items.png"), full_page=False)
        print(f"Saved {out_dir / '02_selected_items.png'}")
        try:
            page.locator(SelectItemsLocators.CANCEL).first.click(timeout=3000)
        except Exception:
            pass
        page.wait_for_timeout(500)
        try:
            page.locator(WizardLocators.CANCEL).first.click(timeout=3000)
        except Exception:
            pass

        # --- Screenshot B: Recover -> File level recovery -> Files ---
        page.goto(f"{base_url}/c/main?id={args.job_id}&t=JOB", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        page.locator(ci_exact("Recover")).first.click()
        page.wait_for_timeout(1000)
        page.locator(ci_exact("File level recovery")).first.click()
        page.wait_for_timeout(3000)
        page.locator(WizardLocators.NEXT).locator("visible=true").first.click()
        page.wait_for_timeout(5000)
        # drill the tree
        for name in args.path:
            page.locator(f"//*[normalize-space(.)='{name}']").first.click()
            page.wait_for_timeout(1500)
        page.screenshot(path=str(out_dir / "03_flr_browse.png"), full_page=False)
        print(f"Saved {out_dir / '03_flr_browse.png'}")
        try:
            page.locator(WizardLocators.CANCEL).first.click(timeout=3000)
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
