"""UI-validation check NJM-122652 (POM + screenshot + vision) — NBR 11.2.1.

Assertion (new wizard): on the FLB Source step you cannot proceed without selecting an ITEM.
With a machine ticked but NO item picked (right panel shows 'No item(s) selected'), clicking
'Next' must NOT advance to '2. Inclusion'. The PASS/FAIL is corroborated by the screenshot.
Run:  cd browser && python checks/check_njm_122652.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.data_protection_page import DataProtectionPage
from pom.driver import browser_page, load_config, load_values
from pom.flb_wizard_page import FlbWizardPage
from pom.locators import WizardLocators
from pom.login_page import LoginPage

TC = "NJM-122652"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg, val = load_config(), load_values()
    win = val["sources"]["windows"]["display_name"]

    with browser_page(headless=not args.headed, trace_name=TC) as page:
        LoginPage(page).open(cfg["url"]).login(cfg["user"], cfg["password"])
        dp = DataProtectionPage(page).open()
        dp.open_create_menu(); dp.start_file_level_backup()
        w = FlbWizardPage(page).on_sources_step()
        # select the machine but pick NO items
        w.expand_windows(); w.select_machine(win)
        w.screenshot(f"{TC}_01_machine_no_items.png", TC)
        no_items = w.exists(WizardLocators.NO_SELECTION)          # 'No item(s) selected'
        print(f"[{TC}] 'No item(s) selected' shown: {no_items}")
        # try to advance
        try:
            w.click_next()
        except Exception as e:
            print(f"[{TC}] click Next raised: {type(e).__name__}")
        # PASS if we did NOT advance to step 2 (Inclusion) -> still on Source. The Inclusion
        # step's 'Include items' toggle only shows once advanced; the simplest reliable signal
        # is whether the Select Items right-panel note is still present.
        still_source = w.exists(WizardLocators.NO_SELECTION)
        shot = w.screenshot(f"{TC}_02_after_click_next.png", TC)
        verdict = "PASS" if still_source else "FAIL"
        print(f"[{TC}] still on Source after Next (no item selected): {still_source}")
        print(f"[{TC}] VISION-VERDICT screenshot: {shot}")
        print(f"[{TC}] {verdict} — cannot proceed without selecting an item")
        w.click_cancel()
    return 0 if still_source else 1


if __name__ == "__main__":
    raise SystemExit(main())
