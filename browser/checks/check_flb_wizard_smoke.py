"""Smoke test: drive the full NBR 11.2.1 FLB wizard via the POM and CANCEL (creates nothing).

Validates every calibrated selector end-to-end: machine tree, Select Items dialog (drill +
folder/file tick), Inclusion/Exclusion, Destination repo pick, Schedule, Options job-name.
Run:  cd browser && python checks/check_flb_wizard_smoke.py   (add --headed to watch)
"""
from __future__ import annotations
import sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pom.driver import browser_page, load_config, load_values
from pom.login_page import LoginPage
from pom.data_protection_page import DataProtectionPage
from pom.flb_wizard_page import FlbWizardPage

TC = "_smoke_flb_wizard"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg, val = load_config(), load_values()
    win = val["sources"]["windows"]["display_name"]
    repo = val["repository"]["name"]
    ok = []

    with browser_page(headless=not args.headed) as page:
        LoginPage(page).open(cfg["url"]).login(cfg["user"], cfg["password"])
        dp = DataProtectionPage(page).open()
        dp.open_create_menu(); dp.start_file_level_backup()
        w = FlbWizardPage(page).on_sources_step()
        w.screenshot(f"{TC}_01_source.png", TC)

        # Source: select machine + open Select Items + tick a FOLDER and a FILE
        w.expand_windows(); w.select_machine(win)
        ok.append(("machine selected", True))
        w.open_item_picker()
        w.picker_drill("Local Disk (C:)"); w.picker_drill("TestData_ForFLB")
        w.picker_check("ft_code")                       # FOLDER
        w.picker_drill("ft_pdf"); w.picker_check("sample_pdf.pdf")  # FILE
        count = w.picker_selected_count()
        w.screenshot(f"{TC}_02_select_items.png", TC)
        ok.append((f"picker count = {count!r}", "2" in count))
        w.picker_apply()

        # Source -> Inclusion -> Exclusion -> Destination (3 Next clicks)
        w.click_next(); w.click_next(); w.click_next()
        w.screenshot(f"{TC}_03_destination.png", TC)
        w.select_repository(repo)
        ok.append((f"repo picked = {repo}", True))

        # Schedule -> Options
        w.click_next(); w.set_run_on_demand()
        w.click_next()
        w.set_job_name("AUTO_FLB_smoke")     # NOT saved — we cancel
        w.screenshot(f"{TC}_04_options.png", TC)
        ok.append(("reached Options + set job name", True))

        # discard — create nothing
        w.click_cancel()
        w.screenshot(f"{TC}_05_after_cancel.png", TC)

    print(f"\n[{TC}] results:")
    for label, passed in ok:
        print(f"   {'PASS' if passed else 'FAIL'}  {label}")
    allpass = all(p for _, p in ok)
    print(f"[{TC}] {'ALL PASS — POM drives the new wizard end-to-end' if allpass else 'SOME FAILED — see above'}")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
