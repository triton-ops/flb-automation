"""Regression check for FileLevelRecoveryPage.set_overwrite_behavior() — CALIBRATED live
2026-07-21 against nbr-84, job AUTO_FLB_NJM-182436_root (id=432, a real, pre-existing job kept
around for suite F / NJM-182724 investigation).

BUG FOUND+FIXED: the old set_overwrite_behavior() assumed clicking L.OVERWRITE_RENAME (the
combo's own currently-displayed value) would both find that text AND open the dropdown. Live DOM
inspection proved the combo's displayed value is rendered via a `title` ATTRIBUTE (on the
`.simple-combo-body` wrapper DIV and the combo's own readonly `<input>`), never as real text
content — ci_exact()/ci_contains() (text-content matching) can't see it, so every call burned a
real 10s timeout opening it, then another 10s failing to pick the option, and the wizard was left
showing whatever the DEFAULT value already was. Fixed to open the dropdown via the specific
arrow-trigger icon (class contains 'x-form-arrow-trigger') instead — see
FileLevelRecoveryPage.set_overwrite_behavior()'s own docstring for the full live-calibration
finding.

This check exercises all 3 real values (RENAME/SKIP/OVERWRITE) against the Options step, reading
back FileLevelRecoveryPage.overwrite_behavior_value() (the combo input's `title` attribute) after
each selection to confirm it's ACTUALLY reflected — not just "the click didn't throw".

Browse-only: ticks the root node to satisfy the Files-step selection gate, but the wizard is
CANCELLED before ever reaching/clicking the final 'Recover' action. Job id=432's real recovery
point is left completely untouched.

Run: cd browser && python checks/check_overwrite_behavior_combo.py   (add --headed to watch)
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
from pom.common.locators import FileLevelRecoveryLocators as L
from pom.common.login_page import LoginPage

TC = "check_overwrite_behavior_combo"
JOB_NAME = "AUTO_FLB_NJM-182436_root"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_app_config().flb
    r: list[tuple[str, bool]] = []

    def check(label: str, passed: bool):
        r.append((label, bool(passed)))
        print(f"   {'PASS' if passed else 'FAIL'}  {label}")

    with browser_page(headless=not args.headed, trace_name=TC) as page:
        LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
        DataProtectionPage(page).open()
        page.wait_for_timeout(1500)

        flr = FileLevelRecoveryPage(page)
        flr.recover_file_level(JOB_NAME)
        page.wait_for_timeout(2000)
        flr.click_next()  # Backup -> Files
        page.wait_for_timeout(1500)
        flr.wait_files_ready(timeout=180_000)
        flr.select_root()
        flr.click_next()  # Files -> Options
        page.wait_for_timeout(1500)
        flr.choose_recovery_type("original")
        page.wait_for_timeout(800)

        check("Overwrite behavior field is shown for 'Recovery to original location'",
              flr.has_overwrite_behavior())

        default_value = flr.overwrite_behavior_value()
        check(f"default value reads back a non-empty string (got {default_value!r})",
              bool(default_value))

        cases = [
            ("RENAME", L.OVERWRITE_RENAME, "Rename recovered item if such item exists"),
            ("SKIP", L.OVERWRITE_SKIP, "Skip recovered item if such item exists"),
            ("OVERWRITE", L.OVERWRITE_OVERWRITE, "Overwrite the original item if such item exists"),
        ]
        for name, locator, expected_text in cases:
            flr.set_overwrite_behavior(locator)
            actual = flr.overwrite_behavior_value()
            check(f"selecting {name} -> overwrite_behavior_value() == {expected_text!r} (got {actual!r})",
                  actual == expected_text)

        # switch back to RENAME (the wizard's own default) before cancelling, just to leave the
        # combo in a known state — cosmetic only, the wizard is cancelled either way.
        flr.set_overwrite_behavior(L.OVERWRITE_RENAME)

        flr.click_cancel()
        page.wait_for_timeout(1000)
        check("wizard closed cleanly after cancel (Options step no longer visible)",
              page.locator(L.STEP_OPTIONS).locator("visible=true").count() == 0)

    print(f"\n[{TC}] results:")
    for label, passed in r:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}")
    allpass = all(p for _, p in r)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL — see above'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
