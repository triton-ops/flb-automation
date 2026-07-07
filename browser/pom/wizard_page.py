"""WizardPage — shared base for all job wizards (FLB / File Share / Backup Copy). XPath-based.

Shared Sources-step validation surface. Subclasses set LOC and add source specifics.
Verdict for UI checks is the VISION read of screenshot(); these helpers corroborate it.
"""
from __future__ import annotations

from .base_page import BasePage
from .locators import WizardLocators, ci_exact


class WizardPage(BasePage):
    LOC = WizardLocators

    def on_sources_step(self):
        self.wait(2000)
        return self

    def next_disabled(self) -> bool:
        """Best-effort DOM signal (ExtJS disabled class). Vision is authoritative."""
        return self.exists(self.LOC.NEXT_DISABLED)

    def next_enabled(self) -> bool:
        return not self.next_disabled()

    def needs_selection_hint(self) -> bool:
        """True while 'Select at least one item' is shown (nothing selected yet)."""
        return self.exists(self.LOC.SELECT_AT_LEAST_ONE)

    def select_item_by_label(self, label: str):
        self.click(ci_exact(label))
        self.wait(1500)
        return self

    def click_next(self):
        self.click_visible(self.LOC.NEXT)   # visible-scoped: ExtJS keeps hidden step duplicates
        self.wait(2000)
        return self

    def click_cancel(self):
        try:
            self.click_visible(self.LOC.CANCEL, timeout=5000)
            self.wait(1500)
        except Exception:
            pass
        return self
