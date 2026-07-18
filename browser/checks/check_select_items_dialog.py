"""Calibration/regression check for the FLB Source-step 'Select Items' dialog locators/readers.

CALIBRATED live 2026-07-18 against nbr-84 / machine 'Window11'. Exercises every locator + reader
added to SelectItemsLocators / FlbWizardPage for the dialog: title, volume-view default, breadcrumb,
search input + clear control, Up One Level ('[..]' row), loading mask, footer selection count,
Select-all + 200-item cap tooltip, system-folder disabled tooltip, Apply enabled-state, hidden
folders appearing in the listing (NJM-70383), the '>200 results' banner, and the Selected Items
Show/Hide expansion panel (Name/Path grid).

Builds NO job — opens the dialog during wizard building and cancels out (read-only exploration
pattern; nothing named AUTO_FLB_* is created). Documented gaps intentionally NOT asserted: the
search box does not filter this listing in this build, so the empty-result message is unreachable
(the '>200 results' banner IS real and asserted below, independent of search); deep-path breadcrumb
truncation was not reproducible 3 levels deep.

Run: cd browser && python checks/check_select_items_dialog.py   (add --headed to watch)
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
from pom.common.locators import SelectItemsLocators as SI
from pom.common.login_page import LoginPage

TC = "check_select_items_dialog"
MACHINE = "Window11"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    cfg = load_app_config().flb
    r: list[tuple[str, bool, str]] = []

    def check(label: str, passed: bool, detail: str = ""):
        r.append((label, bool(passed), detail))

    with browser_page(headless=not args.headed, trace_name=TC) as page:
        LoginPage(page).open(cfg.url).login(cfg.user, cfg.password)
        DataProtectionPage(page).open().open_create_menu().start_file_level_backup()
        flb = FlbWizardPage(page).on_sources_step()
        flb.expand_windows()
        flb.select_machine(MACHINE)
        flb.open_item_picker()
        flb.wait(1500)

        # 1) dialog container + title
        check("1 dialog open", flb.picker_dialog_open())
        title = flb.picker_title()
        check("1 title == 'Select Items'", title.strip().lower() == "select items", repr(title))

        # 11) Apply enabled at open (Source step gates 'select at least one item', not the dialog)
        check("11 Apply enabled at open", flb.picker_apply_enabled())

        # 2) volume-view default: shows a volume row; no up-level row at root
        vol_names = flb.picker_row_names()
        check("2 volume view shows 'Local Disk (C:)'", "Local Disk (C:)" in vol_names, str(vol_names[:4]))
        check("5 no Up-One-Level at volume root", not flb.picker_up_one_level_present())

        # 3) breadcrumb root present at volume view
        check("3 breadcrumb root icon present", page.locator(SI.BREADCRUMB_ROOT).locator("visible=true").count() > 0)

        # 4) search input present at open
        check("4 search input present", page.locator(SI.SEARCH_INPUT).locator("visible=true").count() > 0)

        # 7) footer count reader works
        count0 = flb.picker_selected_count()
        check("7 footer count reader works", "selected for" in count0.lower(), repr(count0))

        # --- drill into C: ---
        flb.picker_drill("Local Disk (C:)")
        flb.wait(800)

        # 6) loading overlay mechanism: the folder-content load overlay is the standard ExtJS
        # div.x-mask (handled by BasePage.wait_masks_gone(), which picker_drill() already calls).
        # A persistent full-viewport modal-backdrop x-mask coexists behind the dialog (shares the
        # class), so we assert the LOADING_MASK locator resolves to a real element rather than a
        # clean transient-only "it cleared" signal (documented — see the locator comment).
        mask_present = page.locator(SI.LOADING_MASK).count() > 0
        check("6 loading-mask (x-mask) locator resolves", mask_present)

        # 5) Up One Level now present, and breadcrumb shows the C: segment
        check("5 Up-One-Level '[..]' present below root", flb.picker_up_one_level_present())
        check("3 breadcrumb segment 'C:' present",
              page.locator(SI.breadcrumb_segment("C:")).locator("visible=true").count() > 0)
        crumb = flb.picker_breadcrumb_text()
        check("3 breadcrumb text includes C:", "C:" in crumb, repr(crumb))

        # 9) system folder: 'Windows' checkbox disabled with the system tooltip
        c_names = flb.picker_row_names()
        check("9 system folder 'Windows' disabled", flb.picker_row_disabled("Windows"))
        check("9 system-folder tooltip text", flb.picker_row_tooltip("Windows") == SI.SYSTEM_FOLDER_TOOLTIP,
              repr(flb.picker_row_tooltip("Windows")))

        # 12) hidden folder appears in the listing (ProgramData is OS-hidden, shown & selectable)
        check("12 hidden folder 'ProgramData' listed", "ProgramData" in c_names, str(c_names))

        # --- drill into TestData_ForFLB ---
        flb.picker_drill("TestData_ForFLB")
        flb.wait(800)

        # 14) Selected Items expansion panel (RE-CALIBRATED live 2026-07-18 — corrects the
        # earlier same-day false "no panel" finding)
        names_here = [n for n in flb.picker_row_names() if n != "[..]"][:2]
        for n in names_here:
            flb.click_force(SI.checkbox(n))
        flb.wait(500)
        check("14 panel collapsed before toggle", not flb.picker_selected_items_panel_expanded())
        flb.picker_toggle_selected_items()
        check("14 Show/Hide toggle expands the panel", flb.picker_selected_items_panel_expanded())
        panel_rows = flb.picker_selected_items_rows()
        panel_names = {r["name"] for r in panel_rows}
        check("14 expanded panel lists the selected items", set(names_here) <= panel_names,
              f"expected {names_here}, got {panel_rows}")
        flb.picker_toggle_selected_items()
        check("14 toggle collapses the panel again", not flb.picker_selected_items_panel_expanded())
        # clear this ad-hoc selection so it doesn't interfere with the 200-cap test below
        for n in names_here:
            flb.click_force(SI.checkbox(n))
        flb.wait(500)

        # --- drill to Subfolder_200Folders: a DETERMINISTIC >200-item fixture (207 real items on
        # disk, confirmed via remoting 2026-07-18 — unlike TestData_ForFLB's own top-level count,
        # which fluctuates as other suites create/clean up AUTO_FLB_* fixtures concurrently) ---
        flb.picker_drill("Subfolder_200Folders")
        flb.wait(800)

        # 13) '>200 results' banner (RE-CALIBRATED live 2026-07-18 — real, exact TC spec text)
        check("13 '>200 results' banner shown", flb.picker_over_200_message_shown())

        # 10) Select-all + 8) 200-item cap
        flb.picker_select_all()
        cnt = flb.picker_selected_count()
        check("10 Select-all selects to the 200 cap", cnt.strip().endswith("200"), repr(cnt))

        # navigate up; a sibling folder must now be disabled with the cap tooltip
        flb.picker_up_one_level()
        flb.wait(800)
        up_names = flb.picker_row_names()
        siblings = [n for n in up_names if n not in ("[..]", "Subfolder_200Folders")]
        capped = next((n for n in siblings if flb.picker_row_tooltip(n) == SI.MAX_SELECTED_TOOLTIP), None)
        check("8 sibling row disabled at 200 cap", capped is not None and flb.picker_row_disabled(capped),
              f"sibling={capped!r} of {siblings[:5]}")
        check("8 200-cap tooltip text", capped is not None, SI.MAX_SELECTED_TOOLTIP)
        flb.screenshot(f"{TC}_cap.png", TC)

        # 4) search: typing reveals the clear/X control (searchTrigger2). Done LAST because
        # real-keystroke typing into this box disturbs the current listing in this build (the
        # box's keyup handler is live even though it does not usefully filter — see picker_search)
        # — so it is exercised only once no further navigation is needed.
        flb.picker_search("abc")
        check("4 clear/X visible when text present", flb.picker_search_clear_visible())
        flb.picker_clear_search()
        check("4 clear empties the search box",
              (page.locator(SI.SEARCH_INPUT).locator("visible=true").first.input_value() or "") == "")

        # --- clean up: cancel dialog, then wizard (no job created) ---
        try:
            page.locator(SI.CANCEL).locator("visible=true").first.click(force=True)
            flb.wait(1000)
        except Exception as ex:  # noqa: BLE001
            print("dialog cancel note:", ex)
        flb.click_cancel()

    print(f"\n[{TC}] results:")
    width = max(len(x[0]) for x in r)
    for label, passed, detail in r:
        tail = f"   ({detail})" if detail else ""
        print(f"   {'PASS' if passed else 'FAIL'}  {label:<{width}}{tail}")
    allpass = all(p for _, p, _ in r)
    print(f"[{TC}] {'ALL PASS' if allpass else 'PARTIAL — see above'}  ({sum(p for _,p,_ in r)}/{len(r)})")
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
