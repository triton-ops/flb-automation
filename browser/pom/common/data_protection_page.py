"""DataProtectionPage — Jobs area + entry to every job wizard and the Recover (FLR) flow.

XPath selectors in locators.DataProtectionLocators; actions via BasePage. The Create control
is a '+' icon (no text) -> open_create_menu() uses a calibrated coordinate fallback.
"""
from __future__ import annotations

from ..base.base_page import BasePage
from .locators import DataProtectionLocators as L
from .locators import RunDialogLocators as RunL


class DataProtectionPage(BasePage):
    def open(self):
        self.click(L.LEFT_NAV)
        self.wait(2500)
        return self

    def open_create_menu(self, attempts: int = 3):
        # Stable class-based selector for the '+' create button. The coordinate fallback is
        # banner-fragile (shifts whenever the license-expiring banner is shown, which is
        # always, in this environment) — retry the real locator before resorting to it.
        # CALIBRATED live 2026-07-15: running many wizard open/cancel cycles back-to-back
        # (e.g. a UI-validation test suite) intermittently sees this whole flow time out for
        # reasons that don't reproduce in an isolated single-shot script (not a lingering
        # mask/dialog — confirmed live) — most likely transient appliance-side load rather
        # than a deterministic client-side state bug. Retry generously rather than fail fast.
        for attempt in range(attempts):
            try:
                self.click(L.CREATE_ADD, timeout=15000)
                self.wait(1500)
                return self
            except Exception:
                self.wait(1500 * (attempt + 1))
        self.click_xy(*L.CREATE_ADD_XY)   # last-resort fallback
        self.wait(1500)
        return self

    # --- wizard launchers (assume the create menu is open) ---
    def _click_menu_item_robust(self, selector: str, attempts: int = 3):
        """Click a create-menu item, reopening the create menu fresh between attempts if it
        wasn't actually open/rendered yet. See open_create_menu()'s docstring for why this
        needs generous retries rather than a single fallback."""
        for attempt in range(attempts):
            try:
                self.click(selector, timeout=8000)
                return
            except Exception:
                if attempt == attempts - 1:
                    raise
                self.open_create_menu()

    def start_file_level_backup(self):
        self._click_menu_item_robust(L.MENU_FLB)
        self.wait(3000)
        return self

    def start_backup_copy(self):
        self._click_menu_item_robust(L.MENU_BACKUP_COPY)
        self.wait(3000)
        return self

    def start_file_share_backup(self):
        self._click_menu_item_robust(L.MENU_FILE_SHARE)
        self.wait(3000)
        return self

    # --- recovery entry (FLR) ---
    def select_job(self, job_name: str):
        self.click(L.job_row(job_name))
        self.wait(2000)
        return self

    def open_recover_menu(self):
        self.click(L.RECOVER_BUTTON)
        self.wait(2000)
        return self

    def run_job(self, job_name: str, nth: int = 0):
        """Select `job_name` in the Jobs sidebar and run it via the toolbar Run button,
        confirming the 'Run this job?' dialog (defaults: 'Run for all Servers', no schedule).
        CALIBRATED live 2026-07-15 against nbr-84.

        CALIBRATED live 2026-07-16: re-running the SAME job immediately after a prior run just
        completed (NJM-185023's 4 consecutive runs) can leave the toolbar's Run control not yet
        re-enabled for well past click_visible's normal 10s default — the same class of dashboard-
        state lag already documented on stop_job()'s docstring for Manage -> Delete (observed
        there to last "over a minute"). A single fresh-job run (every other test in this suite)
        is unaffected since there's no prior run to transition away from. Give this specific
        click extra patience rather than the shared default."""
        self.click(L.sidebar_job_row(job_name), nth=nth)
        self.wait(1500)
        self.click_visible(L.RUN_BUTTON, timeout=60_000)
        self.wait(1000)
        self.click_visible(RunL.RUN)
        self.wait(1500)
        return self

    def stop_job(self, job_name: str, nth: int = 0):
        """Select `job_name` and stop it via the toolbar Stop button, confirming the
        'Stop this job?' dialog (default: 'Stop for all Servers'). No-op-safe to call on a
        job that isn't running (Stop button click will just fail visibly — callers that need
        idempotency should check get_job_status() first). CALIBRATED live 2026-07-15: a job's
        Manage -> Delete option stays disabled (DOM title 'This job is locked by the "run"
        action.') until Stop has fully taken effect (status becomes 'Stopped'), so callers
        needing to delete a running job must stop_job() then wait_for_job_status(..., ("Stopped",
        "Successful", "Failed")) before delete_job()."""
        self.click(L.sidebar_job_row(job_name), nth=nth)
        self.wait(1500)
        self.click_visible(L.STOP_BUTTON)
        self.wait(1000)
        self.click_visible(L.STOP_CONFIRM_BUTTON)
        self.wait(1500)
        return self

    # --- job run-status polling (pure-UI replacement for the old RPC
    # JobSummaryManagement.getJobShortInfo poll) ---
    def get_job_status(self, job_name: str, nth: int = 0) -> str:
        """Select `job_name` and read its own dashboard 'Job Info' panel (line 2) to classify
        its run status as 'Not executed yet' / 'Running' / 'Successful' / 'Failed' / 'Stopped'.
        CALIBRATED live 2026-07-15 against nbr-84: line 1 (JOB_INFO_LINE1) is AMBIGUOUS — a job
        idle between runs always shows its schedule label there (e.g. 'Runs on demand'),
        whether it has never run OR just finished a successful run; line 2 is what actually
        disambiguates, via its own sentence ('This job has not been executed yet' / 'This job
        has not finished yet...' / 'Last run was successful...'). Returns the raw line 2 text
        if it doesn't match a known pattern (forward-compatible with a Failed/Stopped run,
        not yet confirmed live), or '' if the panel isn't found at all."""
        self.click(L.sidebar_job_row(job_name), nth=nth)
        self.wait(1000)
        loc = self.page.locator(L.JOB_INFO_LINE2).locator("visible=true").first
        if loc.count() == 0:
            return ""
        text = loc.inner_text().strip()
        low = text.lower()
        if text.startswith("This job has not been executed yet"):
            return "Not executed yet"
        if text.startswith("This job has not finished yet"):
            return "Running"
        if "successful" in low:
            return "Successful"
        if "failed" in low:
            return "Failed"
        if "stopped" in low:
            return "Stopped"
        return text

    def wait_for_job_status(
        self,
        job_name: str,
        terminal_statuses: tuple[str, ...] = ("Successful", "Failed", "Stopped"),
        timeout_ms: int = 600_000,
        poll_ms: int = 15_000,
        nth: int = 0,
    ) -> str:
        """Poll `job_name`'s own dashboard status (get_job_status()) until it reaches one of
        `terminal_statuses`, or timeout — the pure-UI equivalent of the old RPC poll on
        crState/lrState. Returns the final status seen (which may be non-terminal if the
        timeout was hit)."""
        waited = 0
        status = self.get_job_status(job_name, nth=nth)
        while status not in terminal_statuses and waited < timeout_ms:
            self.wait(poll_ms)
            waited += poll_ms
            status = self.get_job_status(job_name, nth=nth)
        return status
