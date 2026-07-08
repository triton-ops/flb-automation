"""FileShareRecoveryPage — File Share Recovery flow (NBR 11.2.1). CALIBRATED live 2026-07-08
against nbr-5 (job 22, 'Backup job for file share' -> BACKUP_OBJECT-26, savepoint 44 — see
test-data/environment.md).

Entry: on Data Protection, select an FSB job -> 'Recover' -> 'File share recovery'. This is
FSB's distinctly-WORDED equivalent of FLB's 'File level recovery' menu item — same GRANULAR
RECOVERY submenu, but opens a 'File Share Recovery Wizard' instead of a 'File Level Recovery
Wizard'. Confirmed at the RPC layer too: FileLevelRecoveryManagement.createSession needs
hvType:"NAS" (not "PHYSICAL") for an FSB backup object — see recipes/file-backup-recipes.md R7.

The underlying wizard shares the IDENTICAL 4-step DOM/behavior as FileLevelRecoveryPage
otherwise (Files-step mount detection, the reactive selection gate, Options recovery types),
so this extends that class and only overrides the entry point and step-1 handling:
  1. Backup  (calendar/table recovery-point picker — NOT a flat backup-name list; comes
             PRE-SELECTED to the latest recovery point when entered via a specific job's own
             Recover button, so Next is already enabled without calling select_backup())
  2. Files   (WAITS for the recovery point to MOUNT, then browse/select files — inherited as-is)
  3. Options (Recovery type combo — inherited as-is)
  4. Finish

⚠ SAFETY: same as FileLevelRecoveryPage — 'Recovery to original location' OVERWRITES the
source. This page object only NAVIGATES and SELECTS options; no auto-finish for
original-location.
"""
from __future__ import annotations

from ..common.locators import FileLevelRecoveryLocators as L
from .file_level_recovery_page import FileLevelRecoveryPage


class FileShareRecoveryPage(FileLevelRecoveryPage):
    def recover_file_share(self, job_name: str, nth: int = 0):
        """From Data Protection: select an FSB job, open Recover, choose 'File share
        recovery'.

        Also: this wizard's Cancel button pops a 'Close the wizard?' confirm whose OWN button
        is (confusingly) ALSO labeled 'Cancel' rather than 'Close' — click_cancel() (inherited
        from FileLevelRecoveryPage) handles this generically, no special handling needed by
        the caller."""
        self._select_job_and_open_recover_menu(job_name, nth)
        self.click_visible(L.MENU_FILE_SHARE); self.wait(4000)
        return self
