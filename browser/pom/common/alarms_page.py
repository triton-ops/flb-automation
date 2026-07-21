"""AlarmsPage — the "N Issue(s) requires your attention" panel, reachable via the stat-tile
labelled 'Issue'/'Issues' on a job's own Data Protection dashboard (top-right info row, alongside
'Servers'/'Last known ...'). CALIBRATED live 2026-07-21 against nbr-84 (NJM-182728, suite J
"Alarms / notifications / events" — first POM coverage for this area).

This panel appears to be a GLOBAL outstanding-issues list (not scoped to just the currently-open
job) — a search box + filter icon sit above a paginated list of alarm cards, each with a bold
title (e.g. 'File level backup of the "Window11" physical machine cannot be started'), a
timestamp, a per-card 'Dismiss' button, and a plain-text description line underneath (e.g. 'The
"C:/AlarmTest45_ForFLB" folder cannot be found. Make sure the folder is available. If it was
deleted, edit the job and remove this folder.') — this description line is where the real
human-readable alarm content lives; the TC's own 'alarm code' (e.g. 'ict45') is NOT displayed
anywhere in the UI as a literal code, only as this natural-language message.

⚠ SAFETY: this class intentionally has no Dismiss/Dismiss-All caller — clicking Dismiss removes
someone's outstanding issue notification, which could affect a DIFFERENT job's alarm if more than
one is outstanding at the time (the panel is global, not scoped to our own AUTO_FLB_* job). Only
ever read this panel's text; never dismiss.
"""
from __future__ import annotations

from ..base.base_page import BasePage
from .locators import ci_contains, ci_exact


class AlarmsLocators:
    # CALIBRATED live 2026-07-21: ci_contains("Issue") is too broad — its full-subtree-text XPath
    # matches a large ancestor container (the whole top-right stats card: '1 Issue 1 Servers 0.0
    # KB Last known ...'), not the small clickable stat tile itself, and clicking that ancestor
    # is a no-op. ci_exact("Issue") matches just the tile's own label text (confirmed live: 1
    # visible match, and clicking it reliably opens the panel).
    ISSUES_TRIGGER = ci_exact("Issue")
    PANEL_TITLE = ci_contains("requires your attention")
    # CALIBRATED live 2026-07-21: the close control is an <img class="x-tool-close">, not a
    # <div> — and the panel has no 'x-window'-classed ancestor at all (that first guess matched
    # 0 elements outright). Confirmed live via a direct element dump, not assumed.
    CLOSE_BUTTON = "//img[contains(@class,'x-tool-close')]"


class AlarmsPage(BasePage):
    def open_issues_panel(self):
        """Click the 'N Issue(s)' stat tile on the currently-open job's dashboard. Caller must
        already be on that job's dashboard (e.g. via DataProtectionPage.select_job_row()).

        The tile's label is singular 'Issue' for exactly 1 outstanding issue (CALIBRATED live)
        and presumably pluralizes to 'Issues' for 2+, not yet confirmed live — try the singular
        first (the common case for these single-alarm tests), falling back to plural."""
        loc = self.page.locator(AlarmsLocators.ISSUES_TRIGGER).locator("visible=true")
        if loc.count() == 0:
            loc = self.page.locator(ci_exact("Issues")).locator("visible=true")
        loc.first.click()
        self.wait(1200)
        return self

    def issues_panel_text(self) -> str:
        """Flat text dump of the open Issues panel — callers search it for their own job's alarm
        message (e.g. a folder path, machine name) rather than parsing individual alarm cards,
        matching this project's established pragmatic approach for panels with no stable
        per-row structure (see RepositoryManagementPage.activities_text())."""
        return self.page.locator("body").inner_text()

    def close_issues_panel(self):
        self.click_visible(AlarmsLocators.CLOSE_BUTTON)
        self.wait(500)
        return self
