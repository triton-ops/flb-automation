"""Calibration/regression check for FlbWizardPage.inclusion_advances_wizard() /
exclusion_advances_wizard() — CALIBRATED live 2026-07-15 against nbr-84.

Confirms the behavioral validation signal used by these methods: a valid Inclusion pattern
set lets Next advance to Exclusion; an invalid one (a name containing a space, e.g.
'My file.xlsx') blocks Next with NO visible red-box/"Invalid parameters" message anywhere in
the DOM (verified live — this build shows zero visual feedback for a rejected entry, contrary
to the naive assumption of red-highlight feedback).

Builds no job (cancels the wizard at the end without saving) — matches the "no job created"
cleanup convention for pure wizard-UI-behavior checks.

Run: cd browser && python checks/check_inclusion_exclusion_validation.py   (add --headed to watch)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.backup_types.flb_wizard_page import FlbWizardPage
from pom.base.driver import CONFIG_PATH, browser_page, load_config
from pom.common.data_protection_page import DataProtectionPage
from pom.common.login_page import LoginPage

TC = "check_inclusion_exclusion_validation"
MACHINE = "Window11"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_config(CONFIG_PATH)
    results = []

    with browser_page(headless=not args.headed, trace_name=TC) as page:
        LoginPage(page).open(cfg["url"]).login(cfg["user"], cfg["password"])
        DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
        flb = FlbWizardPage(page).on_sources_step()
        flb.expand_windows()
        flb.select_machine(MACHINE)
        flb.open_item_picker()
        flb.select_items([], ["Local Disk (C:)"])
        flb.picker_apply()
        flb.click_next()  # -> Inclusion

        # 1) a genuinely invalid entry (space in name) must NOT advance
        flb.enable_inclusion(["*.docx", "My file.xlsx"])
        blocked = not flb.inclusion_advances_wizard()
        results.append(("invalid entry (space in name) blocks Next", blocked))
        flb.screenshot(f"{TC}_01_invalid_still_step2.png", TC)

        # 2) removing the invalid line lets a valid pattern set advance normally
        if blocked:
            flb.enable_inclusion(["*.docx"])
            advanced = flb.inclusion_advances_wizard()
            results.append(("valid entry advances to Exclusion", advanced))
            flb.screenshot(f"{TC}_02_valid_advanced_step3.png", TC)

            if advanced:
                # 3) exclusion step: same behavioral check, valid pattern advances too
                flb.enable_exclusion(["*.tmp"])
                exc_advanced = flb.exclusion_advances_wizard()
                results.append(("valid exclusion advances to Destination", exc_advanced))
                flb.screenshot(f"{TC}_03_exclusion_advanced_step4.png", TC)

        flb.click_cancel()

    print(f"\n[{TC}] results:")
    for label, passed in results:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}")
    allpass = all(p for _, p in results)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL — see above'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
