"""BackupCopyPage — 'Backup copy' job wizard (extends WizardPage).

CALIBRATED live 2026-07-08 against nbr-84. Flow (FOUR steps, not FLB's six):
  1. Backups (tick an existing backup leaf in the job-type-grouped tree — reuses the FLB
     source tree's DOM/locators, see BackupCopyLocators docstring)
  -> 2. Destination (pick a target repo — reuses DestinationLocators as-is)
  -> 3. Schedule (Backup-Copy-only retention-mode radios + the SAME retention/immutability
     fields FLB has, reusing ScheduleLocators as-is)
  -> 4. Options (job name — reuses OptionsLocators as-is).

See BackupCopyLocators' docstring in locators.py for the full calibration notes: the
existing-backups tree, the Disk/Tape destination-type combo (Tape is no longer greyed out as of
2026-07-08 — a tape library was added), the repo-capability-gated 'Immutable for' checkbox
(disabled on non-Object-Lock repos, enabled on `*_Immutable` ones), and the 'Close the wizard?'
confirm dialog that Cancel pops once anything was touched (handled generically in
WizardPage.click_cancel()).
"""
from __future__ import annotations

from ..common.locators import (
    BackupCopyLocators,
    DestinationLocators,
    FlbWizardLocators,
    OptionsLocators,
    ScheduleLocators,
)
from ..common.wizard_page import WizardPage


class BackupCopyPage(WizardPage):
    LOC = BackupCopyLocators

    # ---------- Step 1: Backups (existing-backup picker tree) ----------
    def expand_backup_group(self, group_label: str):
        """Expand a job-type group header (e.g. 'File level backup job for physical machine').
        Reuses FlbWizardLocators.tree_expander — identical x-tree-expander DOM to FLB's tree.
        NOTE: multiple groups can share the IDENTICAL label (one per underlying job of the same
        type) — this only expands the FIRST match; use expand_all_backup_groups() when the
        target leaf could be under any of several same-named groups (the common case)."""
        self.click(FlbWizardLocators.tree_expander(group_label))
        self.wait(1000)
        return self

    COLLAPSED_GROUP_ROW = ("//tr[contains(@class,'x-grid-row') and "
                           "not(contains(@class,'x-grid-tree-node-expanded'))]"
                           "[.//img[contains(@class,'x-tree-expander')]]")

    def expand_all_backup_groups(self, max_groups: int = 10):
        """Expand every top-level job-type group on the Backups step. CALIBRATED live
        2026-07-08: group headers are NOT unique by label (e.g. nbr-84 has TWO groups both
        titled 'File level backup job for physical machine', one per underlying job), so
        clicking by label text (expand_backup_group) only ever reaches the first one.

        The '+' glyph classes (x-tree-elbow-plus / x-tree-elbow-end-plus) are POSITIONAL
        (sibling order), not state — they never disappear or change when a row expands, and
        expanding a row triggers a full grid view refresh that detaches every row's DOM node
        (stale element handles from before the refresh silently no-op on click). An earlier
        version of this loop matched on those glyph classes and got stuck re-toggling the
        FIRST group open/closed forever, never reaching the second. The row's OWN class
        carries the real state instead: an expanded row gets 'x-grid-tree-node-expanded'
        added to it (verified live). Re-querying COLLAPSED_GROUP_ROW fresh each iteration
        (never caching a row/element handle across a click) correctly finds whichever group
        is still collapsed regardless of view refreshes, and terminates once none remain."""
        for _ in range(max_groups):
            collapsed = self.page.locator(self.COLLAPSED_GROUP_ROW)
            if collapsed.count() == 0:
                break
            try:
                collapsed.first.locator("xpath=.//img[contains(@class,'x-tree-expander')]").click(
                    force=True, timeout=3000)
            except Exception:
                break
            self.wait(500)
        return self

    def select_backup(self, name: str):
        """Tick an existing-backup leaf row (e.g. 'Linux_16.84'). Reuses
        FlbWizardLocators.machine_checkbox — identical x-tree-checkbox DOM to FLB's source tree.
        Force-click: the checkbox input is not Playwright-'visible' (same as FLB)."""
        self.click_force(FlbWizardLocators.machine_checkbox(name))
        self.wait(1200)
        return self

    # ---------- Step 2: Destination ----------
    def select_repository(self, repo_name: str):
        """Pick the target repository. ExtJS keeps hidden duplicates of every step in the DOM
        -> click the VISIBLE combo/option (same pattern as FlbWizardPage.select_repository)."""
        try:
            self.click_visible(DestinationLocators.COMBO, timeout=8000)
        except Exception:
            self.click_visible(DestinationLocators.COMBO_TRIGGER)
        self.wait(1000)
        self.click_visible(DestinationLocators.option(repo_name))
        self.wait(1000)
        return self

    # ---------- Step 3: Schedule / retention mode / immutability ----------
    def set_run_on_demand(self):
        """Tick 'Do not schedule, run on demand' — identical DOM/gotcha to FLB's (two DOM
        copies of the label; the real one is scoped to 'schedule-item-line'), reuse the same
        ScheduleLocators constant unchanged."""
        self.click_force(ScheduleLocators.DO_NOT_SCHEDULE_CHECKBOX)
        self.wait(800)
        return self

    def set_retention_mode_exact_copy(self):
        """'Maintain exact copy of the source backup' — mirrors the source's own retention,
        no extra fields revealed."""
        self.click_force(BackupCopyLocators.RETENTION_MODE_EXACT_COPY)
        self.wait(500)
        return self

    def set_retention_mode_keep_last(self):
        """'Keep <N> last recovery points' radio (the count spinner next to it is disabled
        unless this radio is selected — setting the count itself is not yet calibrated, this
        just selects the mode)."""
        self.click_force(BackupCopyLocators.RETENTION_MODE_KEEP_LAST)
        self.wait(500)
        return self

    def set_retention_mode_sync_custom(self):
        """'Synchronize recovery points and apply custom retention' — DEFAULT-checked mode, and
        the only one that reveals 'Keep backups for' / 'Immutable for' (same fields/gotchas as
        FLB — only rendered when NOT in run-on-demand mode)."""
        self.click_force(BackupCopyLocators.RETENTION_MODE_SYNC_CUSTOM)
        self.wait(500)
        return self

    def set_retention(self, count: int, unit: str = "days"):
        """Set 'Keep backups for <count> <unit>' (only visible under 'Synchronize recovery
        points and apply custom retention', and only when NOT in run-on-demand mode). Reuses
        ScheduleLocators — verified live to be the identical `customKeepSavepointCount`/
        `customKeepSavepointTypeCombo` fields FLB uses."""
        loc = self.page.locator(ScheduleLocators.KEEP_BACKUPS_FOR_COUNT).locator("visible=true").first
        loc.click(); loc.fill(str(count))
        self.click_visible(ScheduleLocators.KEEP_BACKUPS_FOR_UNIT_COMBO)
        self.wait(500)
        self.click(f"//li[normalize-space()='{unit}']")
        self.wait(500)
        return self

    def set_immutable(self, days: int):
        """Tick 'Immutable for <days> days'. CALIBRATED live 2026-07-08: this control is
        DISABLED whenever the step-2 destination repo has no Object Lock capability (Cloudian,
        NFS_REPO, Onboard repository, Wasabi_Repo all reproduce this) and becomes ENABLED the
        moment an Object-Lock-capable repo is picked instead (verified against
        Cloudian-immutable) — call select_repository() with one of environment.md's
        `*_Immutable` repos BEFORE calling this, or the force-click will tick a control the
        backend still won't honor. Reuses ScheduleLocators.IMMUTABLE_FOR_CHECKBOX/_DAYS
        unchanged — verified live to be the identical `keepImmutableCount` field FLB uses."""
        self.click_force(ScheduleLocators.IMMUTABLE_FOR_CHECKBOX)
        self.wait(500)
        loc = self.page.locator(ScheduleLocators.IMMUTABLE_FOR_DAYS).locator("visible=true").first
        loc.click(); loc.fill(str(days))
        return self

    # ---------- Step 4: Options ----------
    def set_job_name(self, name: str):
        loc = self.page.locator(OptionsLocators.JOB_NAME).locator("visible=true").first
        loc.click(); loc.fill(""); loc.type(name)
        return self
