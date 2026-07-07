"""BackupCopyPage — 'Backup copy' job wizard (extends WizardPage).

Source step lists existing BACKUPS to copy. Row selectors TODO (calibrate live).
"""
from __future__ import annotations
from .wizard_page import WizardPage
from .locators import BackupCopyLocators


class BackupCopyPage(WizardPage):
    LOC = BackupCopyLocators

    def select_backup(self, name: str):
        return self.select_item_by_label(name)
