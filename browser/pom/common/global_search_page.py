"""GlobalSearchPage — Global Search feature ('/c/globalsearch', left-nav 'Search').

CALIBRATED live 2026-07-21 against nbr-84 (NJM-70399/70402/70385 — suite L, NJM-182729). See
GlobalSearchLocators' own docstring in locators.py for the full DOM/structure writeup (result
grid shape, per-row popover, filter-panel toggle quirks) — this module only adds the driver
methods on top of it.

Downstream-flow findings (read-only exploration; every wizard opened during calibration was
cancelled before Finish):
  - NJM-70399 (Jobs & Groups -> 'Run'): pops the SAME 'Run this job?' confirm dialog
    DataProtectionPage.run_job() already drives (RunDialogLocators.RUN) — reused as-is.
  - NJM-70402 (Backups -> 'Backup copy'): navigates straight to
    '/c/jobEditor?...jobType=BACKUP_COPY...' — the SAME 'New Backup Copy Job Wizard'
    BackupCopyPage already drives, landing on step '1. Backups' with the searched backup
    ALREADY ticked in the right-hand selected-items panel (CONFIRMED live this entry point
    renders the identical `pessSelViewHeader` markup FLB's Source step uses, e.g.
    '1  Window11' — see BackupCopyPage.pre_selected_backup_names()). A caller can skip
    expand_all_backup_groups()/select_backup() entirely and go straight to
    select_repository()/click_next() for step 2 onward.
  - NJM-70385 (Backups -> 'File level recovery', under 'GRANULAR RECOVERY'): navigates to
    '/c/jobEditor?...jobType=FILE_LEVEL_RECOVERY...' — the SAME 'File Level Recovery Wizard'
    FileLevelRecoveryPage already drives, landing on step '1. Backup' with the SAME backup and
    its latest recovery point already pre-selected (confirmed via the Table-view picker showing
    real recovery points, one pre-selected by radio). FileLevelRecoveryPage.wait_files_ready()/
    click_cancel() work UNCHANGED from this entry point (click_cancel()'s existing 'Close the
    wizard? ... its own button is labelled Cancel, not Close' handling — already written for the
    FSB case — applies identically here).
No new wizard-side locators were needed for either downstream flow: both existing page objects
work AS-IS once launched from Global Search.
"""
from __future__ import annotations

from ..base.base_page import BasePage
from .locators import GlobalSearchLocators as L
from .locators import RunDialogLocators


class GlobalSearchPage(BasePage):
    # ---------- entry ----------
    def open(self):
        """Click the left-sidebar 'Search' nav item."""
        self.click(L.NAV_SEARCH)
        self.wait(1500)
        return self

    def _ensure_search_field_open(self):
        """Reveal the collapsed top-right search field if it isn't already visible — CALIBRATED
        live: the toggle icon (div.searchButton, inside div.searchControl — see
        GlobalSearchLocators.SEARCH_TOGGLE_ICON's own docstring for why this is NOT
        div.searchIcon, an unrelated element) show/hides the field on each click, so this only
        clicks it when the field isn't already showing."""
        if not self.is_visible(L.SEARCH_INPUT):
            self.click_visible(L.SEARCH_TOGGLE_ICON)
            self.wait(400)
        return self

    def search(self, query: str):
        """Reveal the search field if needed, type `query`, and submit (Enter)."""
        self._ensure_search_field_open()
        inp = self.page.locator(L.SEARCH_INPUT).locator("visible=true").first
        inp.click()
        inp.fill("")
        inp.press_sequentially(query, delay=30)
        self.page.keyboard.press("Enter")
        self.wait(1500)
        return self

    # ---------- Display filter panel ----------
    def select_only_filter(self, label: str):
        """Show only the named category (e.g. 'Jobs & Groups' / 'Backups') — clicks
        'Deselect all' (whichever of Select-all/Deselect-all is currently offered — see
        GlobalSearchLocators.SELECT_ALL_FILTERS/DESELECT_ALL_FILTERS's docstring) then
        force-ticks just `label`'s own checkbox."""
        deselect = self.page.locator(L.DESELECT_ALL_FILTERS).locator("visible=true")
        if deselect.count():
            deselect.first.click()
            self.wait(300)
        self.click_force(L.filter_checkbox(label))
        self.wait(300)
        return self

    # ---------- results ----------
    def no_matching_items(self) -> bool:
        return self.is_visible(L.NO_MATCHING_ITEMS)

    def result_row_count(self, item_name: str, category: str | None = None) -> int:
        return self.page.locator(L.result_row(item_name, category)).count()

    def result_category(self, item_name: str, nth: int = 0) -> str:
        """The Category-column text of the nth row matching `item_name` (any category)."""
        rows = self.page.locator(L.result_row(item_name))
        return rows.nth(nth).locator(
            "xpath=.//td[contains(@class,'x-grid-cell-last')]"
        ).inner_text().strip()

    def open_result_popup(self, item_name: str, category: str | None = None, nth: int = 0):
        """Click the nth result row's own name link (opens its action popover)."""
        rows = self.page.locator(L.result_row(item_name, category))
        rows.nth(nth).locator("xpath=.//a[contains(@class,'linkInText')]").click()
        self.wait(800)
        return self

    def click_popup_action(self, label: str, timeout: int = 15000):
        """Click a link inside the currently-open result popover (e.g. 'Run' / 'Backup copy' /
        'File level recovery' / 'Delete backup' / 'Open job dashboard')."""
        self.click_visible(L.popup_action_link(label), timeout=timeout)
        self.wait(800)
        return self

    def find_backup_row_by_job(self, backup_name: str, job_name: str, max_rows: int = 30) -> int:
        """Return the 0-based index of the Backups-category row named `backup_name` whose own
        popover 'JOBS' section link reads exactly `job_name` — disambiguates the common case
        where several backups share the same displayed machine name, one per job that has ever
        targeted it (e.g. 12 different 'Window11' rows on nbr-84 as of this calibration pass —
        see GlobalSearchLocators.result_row()'s own docstring). Raises ValueError if no matching
        row is found among the first `max_rows` rows. Leaves no popup open on return (closes it
        after each check, whether or not it matched)."""
        count = self.result_row_count(backup_name, category="Backups")
        for i in range(min(count, max_rows)):
            self.open_result_popup(backup_name, category="Backups", nth=i)
            job_link = self.page.locator(L.POPUP_JOB_LINK).locator("visible=true")
            text = job_link.first.inner_text().strip() if job_link.count() else ""
            self.close_popup()
            if text == job_name:
                return i
        raise ValueError(
            f"no {backup_name!r} row (category=Backups) owned by job {job_name!r} "
            f"found in the first {min(count, max_rows)} rows"
        )

    def close_popup(self):
        """Best-effort dismiss an open popover without triggering any of its links.

        FOUND LIVE 2026-07-21: an earlier version clicked a raw (10, 10) screen coordinate —
        that corner sits over the collapsible left-nav rail on this page, not empty canvas, so
        it could silently collapse/navigate the sidebar instead of just dismissing the popover.
        A caller that then kept iterating result rows (find_backup_row_by_job()'s own loop) saw
        later rows fail to resolve correctly once that happened. Click the results panel's own
        static heading instead (GlobalSearchLocators.RESULTS_HEADER) — always present, never
        itself a link/nav target."""
        try:
            self.page.locator(L.RESULTS_HEADER).locator("visible=true").first.click(timeout=3000)
            self.wait(300)
        except Exception:  # noqa: BLE001
            pass
        return self

    # ---------- high-level flows (TC-facing) ----------
    def run_job(self, job_name: str, nth: int = 0):
        """NJM-70399: search result row (Jobs & Groups) -> 'Run' -> confirm the 'Run this job?'
        dialog (same RunDialogLocators.RUN confirm DataProtectionPage.run_job() already uses)."""
        self.open_result_popup(job_name, category="Jobs & Groups", nth=nth)
        self.click_popup_action(L.RUN_ACTION)
        self.click_visible(RunDialogLocators.RUN, timeout=30000)
        self.wait(1500)
        return self

    def open_backup_copy(self, backup_name: str, nth: int = 0):
        """NJM-70402: search result row (Backups) -> 'Backup copy' -> lands on the New Backup
        Copy Job Wizard's step 1 with `backup_name` already pre-selected (see module docstring).
        Caller continues by wrapping `self.page` in a BackupCopyPage."""
        self.open_result_popup(backup_name, category="Backups", nth=nth)
        self.click_popup_action(L.BACKUP_COPY_ACTION, timeout=15000)
        self.wait(2000)
        return self

    def open_file_level_recovery(self, backup_name: str, nth: int = 0):
        """NJM-70385: search result row (Backups) -> 'File level recovery' -> lands on the File
        Level Recovery Wizard's step 1 with `backup_name` and its latest recovery point already
        pre-selected. Caller continues by wrapping `self.page` in a FileLevelRecoveryPage."""
        self.open_result_popup(backup_name, category="Backups", nth=nth)
        self.click_popup_action(L.FILE_LEVEL_RECOVERY_ACTION, timeout=15000)
        self.wait(2000)
        return self
