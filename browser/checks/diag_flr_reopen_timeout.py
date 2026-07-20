"""Diagnostic script — reproduces the FLR-reopen timeout against AUTO_FLB_NJM-128609_active-full-
changes (id=379, already exists live with >=2 recovery points). Opens FLR once, cancels, then
tries to open it a SECOND time in the same session and captures screenshots + DOM state at every
step so the failure (or its absence) can be inspected directly, rather than guessed at.

Run: cd browser && python checks/diag_flr_reopen_timeout.py --headed
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from pom.base.config import load_app_config
from pom.base.driver import browser_page
from pom.common.data_protection_page import DataProtectionPage
from pom.common.locators import DataProtectionLocators
from pom.common.login_page import LoginPage

JOB_NAME = "AUTO_FLB_NJM-128609_active-full-changes"
OUT_DIR = Path(__file__).resolve().parent.parent.parent / "results" / "screenshots" / "diag_flr_reopen"


def dump(page, tag: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUT_DIR / f"{tag}.png"), full_page=False)
    # dump mask state + sidebar row state
    masks_all = page.locator("//div[contains(@class,'x-mask')]").count()
    masks_vis = page.locator("//div[contains(@class,'x-mask')]").locator("visible=true").count()
    rows_all = page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).count()
    rows_vis = page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).locator("visible=true").count()
    print(f"[{tag}] masks_all={masks_all} masks_vis={masks_vis} sidebar_rows_all={rows_all} "
          f"sidebar_rows_vis={rows_vis}")
    if masks_vis:
        try:
            html = page.locator("//div[contains(@class,'x-mask')]").locator("visible=true").first.evaluate(
                "el => el.outerHTML"
            )
            print(f"[{tag}] visible mask outerHTML (first 500 chars): {html[:500]}")
        except Exception as e:
            print(f"[{tag}] could not read mask outerHTML: {e}")
    if rows_vis:
        try:
            row = page.locator(DataProtectionLocators.sidebar_job_row(JOB_NAME)).locator("visible=true").first
            box = row.bounding_box()
            print(f"[{tag}] visible sidebar row bounding_box={box}")
            # what element is actually at that point (elementFromPoint) — reveals occlusion
            if box:
                cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                el_desc = page.evaluate(
                    "([x,y]) => { const el = document.elementFromPoint(x,y); "
                    "return el ? el.outerHTML.slice(0,300) : null; }",
                    [cx, cy],
                )
                print(f"[{tag}] elementFromPoint({cx:.0f},{cy:.0f}) = {el_desc}")
        except Exception as e:
            print(f"[{tag}] could not inspect sidebar row: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_app_config().flb

    with browser_page(headless=not args.headed) as page:
        LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
        dp = DataProtectionPage(page)
        dp.open()
        page.wait_for_timeout(1500)
        dump(page, "00_data_protection_open")

        flr = FileLevelRecoveryPage(page)

        print("\n=== FIRST: exercise wait_for_recovery_point_count() itself (the real code path,"
              " now fixed to close the wizard before returning) ===")
        pts = flr.wait_for_recovery_point_count(JOB_NAME, min_count=2)
        print(f"[wait_for_recovery_point_count] returned {len(pts)} points: {pts}")
        dump(page, "01_after_wait_for_recovery_point_count")

        print("\n=== waiting 3s exactly like test_after_source_changes does ===")
        page.wait_for_timeout(3000)
        dump(page, "02_after_3s_wait")

        print("\n=== SECOND FLR open (expected to time out) ===")
        try:
            flr.recover_file_level(JOB_NAME)
            page.wait_for_timeout(1500)
            dump(page, "03_second_flr_open_SUCCESS")
            print("SECOND OPEN SUCCEEDED (no repro)")
        except Exception as e:
            print(f"SECOND OPEN FAILED: {e}")
            dump(page, "03_second_flr_open_FAILURE")
            # extra: dump full sidebar HTML region so we can see stale/duplicate rows directly
            try:
                sidebar_html = page.locator("//div[contains(@class,'jobDashboardNavigator')]").first.evaluate(
                    "el => el.outerHTML"
                )
                (OUT_DIR / "sidebar_at_failure.html").write_text(sidebar_html, encoding="utf-8")
                print(f"[dump] wrote sidebar HTML to {OUT_DIR / 'sidebar_at_failure.html'}")
            except Exception as e2:
                print(f"[dump] could not dump sidebar HTML: {e2}")

        page.wait_for_timeout(3000)  # keep session open a moment for any final screenshot/state

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
