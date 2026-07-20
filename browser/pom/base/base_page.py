"""BasePage — the SINGLE place for all Playwright interaction methods.

Every page object inherits this and calls these wrappers only (never `self.page.<api>`
directly). Centralizing the Playwright API here means UI-driver changes, logging, retries,
or waits are maintained in ONE file. Selectors live in locators.py; data in config/ui_values.json.
"""
from __future__ import annotations

from pathlib import Path

from .driver import SHOTS_DIR


class BasePage:
    def __init__(self, page):
        self.page = page

    # --- navigation ---
    def goto(self, url: str, wait_until: str = "domcontentloaded"):
        self.page.goto(url, wait_until=wait_until)
        return self

    # --- waits ---
    def wait(self, ms: int = 2000):
        self.page.wait_for_timeout(ms)
        return self

    def wait_idle(self):
        self.page.wait_for_load_state("networkidle")
        return self

    def wait_for(self, selector: str, timeout: int = 20000):
        self.page.locator(selector).first.wait_for(timeout=timeout)
        return self

    def wait_masks_gone(self, timeout: int = 15000):
        """Poll until no VISIBLE ExtJS loading mask (div.x-mask) remains — masks intercept
        pointer events (e.g. after drilling into a folder in the Select Items dialog)."""
        deadline = timeout
        step = 300
        waited = 0
        while waited < deadline:
            try:
                vis = self.page.locator("//div[contains(@class,'x-mask')]").locator("visible=true").count()
            except Exception:
                vis = 0
            if vis == 0:
                return self
            self.page.wait_for_timeout(step)
            waited += step
        return self

    # --- actions ---
    def fill(self, selector: str, value: str):
        self.page.locator(selector).first.fill(value)
        return self

    def fill_reliable(self, selector: str, value: str, delay: int = 80, timeout: int = 10000):
        """Like fill(), but types `value` one real keystroke at a time instead of setting the
        DOM value directly — use this instead of fill()/self.fill() for any field whose value
        is read by a subsequent JS-driven action (a 'Test Connection'-style validation call, a
        save/submit gated by client-side validation, a spinner/number field feeding one) where
        that guarantee hasn't been proven for the specific ExtJS widget involved.

        CALIBRATED live 2026-07-16 (NJM-70307's FLR 'Recover to custom location (CIFS)'
        credentials fields — see FileLevelRecoveryPage.fill_custom_location()): Playwright's
        fill() sets only the raw DOM `value` and dispatches a single synthetic 'input' event.
        Some ExtJS widgets never update their OWN internal component/data-model state from that
        alone — the DOM shows the correct value right up until submission, but the widget's
        model still reports empty/stale to whatever reads it next (confirmed live: a CIFS 'Test
        Connection' call read an empty password despite the DOM showing the typed value; explicit
        dispatch_event("change") made it WORSE, since the widget's change handler re-read its own
        never-updated internal state and overwrote the DOM back to empty). Only real per-character
        keystroke simulation reliably drives ExtJS's own change-tracking, matching what a real
        user's keyboard actually does. delay=80 is the calibrated minimum found live — 20ms
        silently dropped roughly a fifth of the characters typed (confirmed via length-checking
        the resulting field value), 80ms did not; this default carries that finding forward so
        every future caller doesn't have to rediscover it.

        NOT a blanket replacement for fill()/self.fill() — plain fields whose value is read via a
        straightforward form submission (e.g. LoginPage's username/password, verified safe by
        every login this project has ever run; the Inclusion/Exclusion textareas, verified safe
        by 21 live-run TCs whose content was independently confirmed via FLR-browse) have no
        evidence of this failure mode and are deliberately left on fill() — switching a
        proven-working call site carries real regression risk for no measured benefit. Reach for
        this when a field is UNVERIFIED against this failure mode and structurally resembles the
        confirmed-broken case (an ExtJS text input feeding a subsequent validated action), not as
        a default for every fill()."""
        loc = self.page.locator(selector).locator("visible=true")
        loc.first.click(timeout=timeout)
        loc.first.fill("")  # clear only — clearing to empty has no internal-state-desync risk,
        # the confirmed failure mode is specifically a non-empty typed VALUE not being read back
        loc.first.press_sequentially(value, delay=delay)
        return self

    def click(self, selector: str, timeout: int = 15000, nth: int = 0):
        self.page.locator(selector).nth(nth).click(timeout=timeout)
        return self

    def click_xy(self, x: int, y: int):
        self.page.mouse.click(x, y)
        return self

    # --- ExtJS-friendly variants ---
    def click_force(self, selector: str, timeout: int = 10000):
        """Click bypassing visibility/actionability — needed for ExtJS inputs that are
        styled/covered (e.g. x-tree-checkbox, hover-revealed icons)."""
        self.page.locator(selector).first.click(timeout=timeout, force=True)
        return self

    def hover(self, selector: str, timeout: int = 10000):
        self.page.locator(selector).first.hover(timeout=timeout)
        return self

    def click_visible(self, selector: str, timeout: int = 10000):
        """Click the first VISIBLE match. ExtJS renders every wizard step in the DOM at once,
        so a plain .first often resolves a hidden duplicate — filter to visible first."""
        loc = self.page.locator(selector).locator("visible=true")
        loc.first.click(timeout=timeout)
        return self

    def click_visible_nth(self, selector: str, nth: int = 0, timeout: int = 15000):
        """Click the nth VISIBLE match — same rationale as click_visible(), but for call sites
        that also need `nth` to disambiguate multiple same-named live rows (e.g.
        DataProtectionLocators.sidebar_job_row() for jobs sharing NBR's generic default name).

        FOUND LIVE 2026-07-20 (Playwright trace analysis, not guessed): DataProtectionPage.
        select_job_row()/FileLevelRecoveryPage._select_job_and_open_recover_menu() used bare
        click() (nth=0, unscoped) on this exact locator. Across a session that reopens the Jobs
        sidebar / FLR wizard several times in a row (e.g. wait_for_recovery_point_count()'s own
        cancel+reopen retry loop), the first 3 reopens in one traced failure clicked fine, but a
        4th fresh open timed out — ExtJS accumulates a hidden, stale duplicate row per reopen
        (same class of bug as picker_apply()/CANCEL/APPLY's own history — see
        [[pom-locator-scoping-lesson]]), and plain nth=0 can end up resolving to an EARLIER,
        now-hidden copy instead of the current live row once enough stale copies have
        accumulated ahead of it in DOM order — a plain click() only checks 'is this node in the
        DOM', not 'is it the live, actionable one', so it hangs waiting for a node that will
        never become clickable. Scoping to visible=true first, then nth, fixes it the same way
        click_visible() already fixes the analogous wizard-step case."""
        loc = self.page.locator(selector).locator("visible=true")
        loc.nth(nth).click(timeout=timeout)
        return self

    def reveal_and_click(self, hover_selector: str, click_selector: str):
        """Hover a container to reveal an icon, then click it (force, then dispatch fallback).

        CALIBRATED live 2026-07-16 (NJM-70312): both steps are now scoped to VISIBLE matches
        (`.locator("visible=true").first`), not a bare `.first`. Found live: re-entering a job's
        wizard via Edit (DataProtectionPage.edit_job()) AFTER that same page had already visited
        a wizard once before (e.g. the CREATE-mode wizard used to build the job in the first
        place) leaves the OLD wizard's panel lingering hidden in the DOM — an unscoped `.first`
        on FlbWizardLocators.SELECTED_HEADER/EDIT_ICON can silently resolve that stale hidden
        copy instead of the current, visible one. The hover+click then appear to succeed (no
        exception) but the 'Select Items' dialog never actually opens, and the next
        picker_drill() call times out with no obvious cause. A fresh CREATE-mode wizard (the
        common case this method was first written for) never hit this because there was only
        ever one copy in the DOM at that point."""
        try:
            self.page.locator(hover_selector).locator("visible=true").first.hover(timeout=5000)
            self.wait(400)
        except Exception:
            pass
        try:
            self.page.locator(click_selector).locator("visible=true").first.click(timeout=4000, force=True)
        except Exception:
            self.page.locator(click_selector).locator("visible=true").first.dispatch_event("click")
        return self

    # --- queries ---
    def exists(self, selector: str) -> bool:
        return self.page.locator(selector).count() > 0

    def is_visible(self, selector: str) -> bool:
        loc = self.page.locator(selector).first
        return bool(loc.count()) and loc.is_visible()

    def is_disabled(self, selector: str) -> bool | None:
        loc = self.page.locator(selector).first
        return loc.is_disabled() if loc.count() else None

    def get_text(self, selector: str) -> str:
        loc = self.page.locator(selector).first
        return loc.inner_text() if loc.count() else ""

    # --- evidence ---
    def screenshot(self, name: str, subdir: str | None = None) -> Path:
        out_dir = SHOTS_DIR / subdir if subdir else SHOTS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / name
        self.page.screenshot(path=str(p), full_page=False)
        return p
