"""DataProtectionPage — Jobs area + entry to every job wizard and the Recover (FLR) flow.

XPath selectors in locators.DataProtectionLocators; actions via BasePage. The Create control
is a '+' icon (no text) -> open_create_menu() uses a calibrated coordinate fallback.
"""
from __future__ import annotations
from .base_page import BasePage
from .locators import DataProtectionLocators as L


class DataProtectionPage(BasePage):
    def open(self):
        self.click(L.LEFT_NAV)
        self.wait(2500)
        return self

    def open_create_menu(self):
        # Stable class-based selector for the '+' create button (coordinate is banner-fragile).
        try:
            self.click(L.CREATE_ADD, timeout=8000)
        except Exception:
            self.click_xy(*L.CREATE_ADD_XY)   # last-resort fallback
        self.wait(1500)
        return self

    # --- wizard launchers (assume the create menu is open) ---
    def start_file_level_backup(self):
        self.click(L.MENU_FLB)
        self.wait(3000)
        return self

    def start_backup_copy(self):
        self.click(L.MENU_BACKUP_COPY)
        self.wait(3000)
        return self

    def start_file_share_backup(self):
        self.click(L.MENU_FILE_SHARE)
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
