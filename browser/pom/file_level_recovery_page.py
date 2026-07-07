"""FileLevelRecoveryPage — File-Level Recovery flow (NBR 11.2.1). CALIBRATED live 2026-07-06.

Entry: on Data Protection, select a backup job -> 'Recover' -> 'File level recovery'. Wizard:
  1. Backup  (select backup + recovery point)
  2. Files   (WAITS for the recovery point to MOUNT, then browse/select files)
  3. Options (Recovery type: Download / Recover to original location / Export to CIFS|NFS share)
  4. Finish

⚠ SAFETY: 'Recover to original location' OVERWRITES the source. Per CLAUDE.md this is gated —
never call finish()/execute an original-location recovery in automated runs without explicit
per-run authorization, and never against the read-only fixtures. This page object only NAVIGATES
and SELECTS options; it deliberately has no auto-finish for original-location.
"""
from __future__ import annotations
from .base_page import BasePage
from .locators import FileLevelRecoveryLocators as L, WizardLocators


class FileLevelRecoveryPage(BasePage):
    # ---------- entry ----------
    def recover_file_level(self, job_name: str):
        """From Data Protection: select the job, open Recover, choose 'File level recovery'."""
        self.click_visible(_ci(job_name)); self.wait(2000)   # select the job row
        self.click_visible(L.RECOVER_BUTTON); self.wait(1500)
        self.click_visible(L.MENU_FILE_LEVEL); self.wait(4000)
        return self

    # ---------- step 1: Backup ----------
    def select_backup(self, name: str):
        """Pick the backup on step 1 (e.g. the machine name) to load its recovery points.
        The latest recovery point is selected by default."""
        self.click_visible(_ci(name)); self.wait(2500)
        return self

    # ---------- step 2: Files (mount + select) ----------
    # The Files right pane is an ExtJS grid with a check-COLUMN (not the 'folderInfoCheckbox' used
    # by the backup-job Select Items dialog) — tick the top node via select_root(). Calibrated
    # headed 2026-07-07: entry, 4-step nav, backup select, RP mount, file select, and the step-3
    # recovery-type options (incl. 'Recovery to original location' + its 'Overwrite behavior').
    def wait_files_ready(self, timeout: int = 180000):
        """Wait for the recovery point to finish mounting ('Recovery point is being prepared'
        clears). Large recovery points can take minutes."""
        import time
        waited, step = 0, 1500
        while waited < timeout:
            if not self.exists(L.PREPARING):
                self.wait(500)
                return self
            self.page.wait_for_timeout(step); waited += step
        return self

    def select_root(self):
        """Tick the top-level backed-up node (e.g. 'C:') in the Files grid to satisfy the
        selection gate. Headed-verified; the grid checker input is force-clicked."""
        self.click_force(L.FILES_ROOT_CHECKBOX)
        self.wait(1000)
        return self

    # ---------- navigation ----------
    def click_next(self):
        self.click_visible(WizardLocators.NEXT); self.wait(2000)
        return self

    def click_cancel(self):
        try:
            self.click_visible(WizardLocators.CANCEL, timeout=5000); self.wait(1500)
        except Exception:
            pass
        return self

    def files_ready(self) -> bool:
        """True once the recovery point has mounted (the 'preparing' text is no longer visible)."""
        return not self.is_visible(L.PREPARING)

    def files_awaiting_selection(self) -> bool:
        """Files step is mounted but gates Next until a file/folder is ticked."""
        return self.is_visible(L.FILES_PROMPT)

    def on_options_step(self) -> bool:
        # step headers + the hidden Options panel are always in the DOM, so detect Options by the
        # ABSENCE of the Files-step selection prompt (you only leave Files once an item is picked).
        return not self.exists(L.FILES_PROMPT) and self.is_visible(L.STEP_OPTIONS)

    # ---------- step 3: Options (recovery type) ----------
    # Recovery type options (EXACT labels, verified live 2026-07-07):
    #   'Recovery to original location'          -> DEFAULT; ⚠ OVERWRITES SOURCE; reveals 'Overwrite behavior'
    #   'Recover to custom location (CIFS/NFS)'  -> export to a CIFS/NFS share (Share type/Path/Overwrite)
    #   'Download'                               -> browser download
    #   'Forward via email'                      -> email the items
    # The final footer action on Options is 'Recover' (NOT 'Next').
    def choose_recovery_type(self, kind: str):
        """Open the Recovery type combo and pick an option. kind in
        {'original','custom','download','email'}. Opens the combo (clicks the field showing the
        current value) then selects the option by its exact label.
        ⚠ 'original' overwrites the source — never select/execute without explicit authorization."""
        label = {"original": L.RT_ORIGINAL, "custom": L.RT_CUSTOM_CIFS_NFS,
                 "download": L.RT_DOWNLOAD, "email": L.RT_FORWARD_EMAIL}[kind]
        # open the combo: click the currently-displayed value (default 'Recovery to original location')
        try:
            self.click_visible(L.RT_ORIGINAL, timeout=5000)
        except Exception:
            self.click_visible(L.RECOVERY_TYPE_LABEL)
        self.wait(600)
        self.click_visible(label)
        self.wait(1000)
        return self

    def set_overwrite_behavior(self, option_locator: str):
        """Set the 'Overwrite behavior' combo (only shown for 'Recovery to original location').
        Pass one of L.OVERWRITE_RENAME / L.OVERWRITE_SKIP / L.OVERWRITE_OVERWRITE."""
        self.click_visible(L.OVERWRITE_RENAME)   # open (default value shown)
        self.wait(500)
        self.click_visible(option_locator)
        self.wait(600)
        return self

    def has_overwrite_behavior(self) -> bool:
        """True when the Overwrite behavior field is shown (i.e. original-location is selected)."""
        return self.is_visible(L.OVERWRITE_BEHAVIOR_LABEL)

    # ⚠ deliberately NO execute()/finish() for original-location — clicking L.RECOVER_ACTION with
    # 'Recovery to original location' OVERWRITES the source. Add an authorized, guarded caller only
    # when a test explicitly requires it, and never against read-only fixtures.

    # legacy compat
    def open_recover_menu(self):
        self.click(L.RECOVER_BUTTON); self.wait(2000); return self


def _ci(label: str) -> str:
    from .locators import ci_exact
    return ci_exact(label)
