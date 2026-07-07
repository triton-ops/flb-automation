"""FileShareBackupPage — 'Backup for file share' job wizard (NBR 11.2.1, 6-step).

CALIBRATED live 2026-07-06 against nbr-5. The FSB wizard is structurally identical to FLB
(Source / Inclusion / Exclusion / Destination / Schedule / Options) with the same tree +
Select Items dialog, so this reuses FlbWizardPage's generic step/picker methods. Differences:
- source nodes are file shares under 'All File shares' (usually expanded by default);
- the Select Items dialog opens at a 'root' node you drill into to reach the share's files.
"""
from __future__ import annotations
from .flb_wizard_page import FlbWizardPage
from .locators import FileShareBackupLocators, FlbWizardLocators


class FileShareBackupPage(FlbWizardPage):
    LOC = FileShareBackupLocators

    def expand_shares(self):
        """Expand 'All File shares' only if its children aren't already visible."""
        if not self.exists(FlbWizardLocators.machine_checkbox("")):
            try:
                self.click(FlbWizardLocators.tree_expander("All File shares"), timeout=5000)
                self.wait(1000)
            except Exception:
                pass
        return self

    def select_share(self, name: str):
        """Tick a file share (e.g. 'CIFS-FileTypeSamples'). Expands the group if needed."""
        sel = FlbWizardLocators.machine_checkbox(name)
        if self.page.locator(sel).count() == 0:
            try:
                self.click(FlbWizardLocators.tree_expander("All File shares"), timeout=5000)
                self.wait(1000)
            except Exception:
                pass
        self.click_force(sel)
        self.wait(1200)
        return self

    # legacy compat
    def select_all_file_shares(self):
        self.click(FileShareBackupLocators.ALL_FILE_SHARES); self.wait(1500); return self
