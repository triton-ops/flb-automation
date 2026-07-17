"""WizardPage — shared base for all job wizards (FLB / File Share / Backup Copy). XPath-based.

Shared Sources-step validation surface. Subclasses set LOC and add source specifics.
Verdict for UI checks is the VISION read of screenshot(); these helpers corroborate it.
"""
from __future__ import annotations

from ..base.base_page import BasePage
from .locators import WizardLocators


class WizardPage(BasePage):
    # Explicit type: without it, mypy infers each subclass's own narrower LOC type (e.g.
    # FlbWizardPage's `type[FlbWizardLocators]`) as the attribute's type, which then rejects a
    # sibling subclass like FileShareBackupPage assigning `type[FileShareBackupLocators]` even
    # though both are valid WizardLocators subtypes.
    LOC: type[WizardLocators] = WizardLocators

    def on_sources_step(self):
        self.wait(2000)
        return self

    ACTIVE_STEP_TAB = "//a[contains(@class,'tabSwitchLinkActive')]"

    def current_step_title(self) -> str:
        """The active step tab's title attribute (e.g. '2. Inclusion'). CALIBRATED live
        2026-07-08 — the currently-active step's <a> tab carries 'tabSwitchLinkActive'
        (the other, already-visited steps only carry the weaker 'slActive')."""
        try:
            return self.page.locator(self.ACTIVE_STEP_TAB).first.get_attribute("title") or ""
        except Exception:
            return ""

    def click_next(self, timeout_ms: int = 10000):
        """Click Next and VERIFY the active step tab actually changed. Measured live
        2026-07-08: right after a step does extra work (typing into a field, an async
        server-side validation debounce), a bare click_next() can silently no-op — the click
        registers but the wizard doesn't advance, with no error raised. Retry the click until
        current_step_title() changes, instead of trusting a fixed sleep."""
        before = self.current_step_title()
        waited = 0
        step = 500
        while waited < timeout_ms:
            self.click_visible(self.LOC.NEXT)   # visible-scoped: ExtJS keeps hidden step duplicates
            self.page.wait_for_timeout(step)
            waited += step
            after = self.current_step_title()
            if after and after != before:
                self.wait(600)   # let the new step's fields finish rendering
                return self
        return self   # gave up retrying — caller's own assertions will surface the stall

    def click_cancel(self):
        try:
            self.click_visible(self.LOC.CANCEL, timeout=5000)
            self.wait(800)
            # Some wizards (CALIBRATED live 2026-07-08 on Backup Copy) pop a 'Close the
            # wizard? All changes will be lost.' confirm once anything was touched (a source
            # ticked, a repo picked, a field typed) — Cancel alone doesn't close them. Best-effort
            # click through it; wizards/paths that never trigger it just find nothing here.
            if self.exists(WizardLocators.CLOSE_CONFIRM):
                self.click_visible(WizardLocators.CLOSE_CONFIRM, timeout=3000)
            self.wait(1000)
        except Exception:
            pass
        return self
