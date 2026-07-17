"""JobManagementPage — select an existing job in the Jobs sidebar and remove it via the
Director UI's Manage -> Delete flow. CALIBRATED live 2026-07-15 against nbr-84.

Flow: select the job row (left 'Jobs' sidebar, scoped via
DataProtectionLocators.sidebar_job_row — see that locator's docstring for why a bare name
search is ambiguous) -> click 'Manage' (opens a dropdown: Clone / Merge / Rename /
Create Report / Disable / Delete) -> click 'Delete' -> confirm in the 'Delete this job?'
dialog.

⚠ SAFETY FENCE: delete_job() refuses to act on any job whose name doesn't start with
AUTO_FLB_ or AUTO_FSB_ — mirrors the exact prefix check browser/checks/cleanup_auto_flb_jobs.py
already enforces for its raw-RPC cleanup path. Discovered machines/repos/transporters are never
touched by this class; it only ever selects/deletes a JOB by name.
"""
from __future__ import annotations

from ..base.base_page import BasePage
from .data_protection_page import DataProtectionPage
from .locators import DataProtectionLocators as L

_SAFE_PREFIXES = ("AUTO_FLB_", "AUTO_FSB_")


class JobManagementPage(BasePage):
    def _open_manage_menu(self, job_name: str, nth: int = 0, wait_ms: int = 500):
        """Select `job_name` and open its Manage dropdown — the common first step of
        _delete_menu_disabled() and delete_job() below, extracted to avoid repeating the same
        select+click-Manage pattern twice (previously duplicated verbatim in both methods).

        Job-row selection itself delegates to DataProtectionPage.select_job_row() rather than
        keeping its own copy — this class already instantiates DataProtectionPage for
        stop_job() below, so reusing its (more heavily used, canonical) row-selection method
        removes a second independent copy of the exact same click+wait pattern rather than
        adding new coupling."""
        DataProtectionPage(self.page).select_job_row(job_name, nth=nth)
        self.click_visible(L.MANAGE_BUTTON)
        self.wait(wait_ms)
        return self

    def _delete_menu_disabled(self, job_name: str, nth: int = 0) -> bool:
        """Open Manage and read the Delete item's own disabled state directly (its CSS class
        gains 'disabled' and its title becomes 'This job is locked by the "run" action.' while
        a job is running), then close the dropdown without acting. This is the authoritative
        signal — the Job overview grid's Status cell can lag behind it by tens of seconds
        (CALIBRATED live 2026-07-15: a job stopped mid-transfer showed 'Running' in the grid
        for over a minute after Manage -> Delete had already re-enabled)."""
        self._open_manage_menu(job_name, nth=nth)
        item = self.page.locator(L.DELETE_MENU_ITEM).locator("visible=true").first
        disabled = "disabled" in (item.get_attribute("class") or "")
        self.page.mouse.click(10, 10)  # click empty space to close the dropdown
        self.wait(300)
        return disabled

    def delete_job(self, job_name: str, nth: int = 0):
        """Select `job_name`, open Manage, click Delete, confirm the dialog.

        ⚠ SAFETY FENCE: raises ValueError without touching anything if `job_name` doesn't
        start with AUTO_FLB_ or AUTO_FSB_ — this class must never be able to delete a
        discovered/reference job, matching the same prefix rule
        browser/checks/cleanup_auto_flb_jobs.py enforces on its raw-RPC path."""
        if not job_name.startswith(_SAFE_PREFIXES):
            raise ValueError(
                f"refusing to delete job {job_name!r} — safety fence requires one of "
                f"{_SAFE_PREFIXES} as a prefix"
            )
        # Manage -> Delete stays disabled while a job is running — stop it first, then poll
        # the Delete item's own disabled state (not the grid Status cell) until it clears.
        if self._delete_menu_disabled(job_name, nth=nth):
            DataProtectionPage(self.page).stop_job(job_name, nth=nth)
            waited, timeout_ms, poll_ms = 0, 120_000, 5_000
            while waited < timeout_ms and self._delete_menu_disabled(job_name, nth=nth):
                self.wait(poll_ms)
                waited += poll_ms

        self._open_manage_menu(job_name, nth=nth, wait_ms=600)
        self.click_visible(L.DELETE_MENU_ITEM)
        self.wait(800)
        self.click_visible(L.DELETE_CONFIRM_BUTTON)
        self.wait(1500)
        return self
