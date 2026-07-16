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

from pathlib import Path

from ..base.base_page import BasePage
from ..common.locators import DataProtectionLocators, WizardLocators, ci_exact
from ..common.locators import FileLevelRecoveryLocators as L


class FileLevelRecoveryPage(BasePage):
    # ---------- entry ----------
    def _select_job_and_open_recover_menu(self, job_name: str, nth: int = 0):
        """Select a job row and click 'Recover' to open its GRANULAR RECOVERY submenu.

        `nth` (0-based) disambiguates when multiple jobs share the SAME display name — NBR
        assigns every job the generic default name (e.g. 'File level backup job for physical
        machine' / 'Backup job for file share') unless the wizard's Options step overrides it,
        so an environment with several ad-hoc/smoke-test jobs (none custom-named) can have >1
        row matching job_name. Uses DataProtectionLocators.sidebar_job_row() (scoped to the
        left Jobs list) rather than a bare ci_exact() text search — see that locator's
        docstring for why: an unscoped search for a non-unique name matches ~16 raw DOM nodes
        (row/cell/wrapper duplicates across the sidebar AND the wide job-overview grid), making
        plain nth() unreliable. Default 0 preserves correct behavior for a uniquely-named job.
        Note: sidebar index does NOT necessarily match job id order — a job whose most recent
        scheduled run failed can still have an earlier, perfectly recoverable savepoint; check
        each candidate's own recovery-point history rather than assuming index order."""
        self.click(DataProtectionLocators.sidebar_job_row(job_name), nth=nth)
        self.wait(2000)   # select the job row
        self.click_visible(L.RECOVER_BUTTON); self.wait(1500)
        return self

    def recover_file_level(self, job_name: str, nth: int = 0):
        """From Data Protection: select an FLB job, open Recover, choose 'File level
        recovery'."""
        self._select_job_and_open_recover_menu(job_name, nth)
        self.click_visible(L.MENU_FILE_LEVEL); self.wait(4000)
        return self

    # ---------- step 1: Backup ----------
    def select_backup(self, name: str):
        """Pick the backup on step 1 (e.g. the machine name) to load its recovery points.
        The latest recovery point is selected by default. FLB entry only — the FSB
        FileShareRecoveryPage pre-selects the share + latest recovery point automatically
        (calendar-based step 1, not a flat name to click), so it doesn't call this."""
        self.click_visible(ci_exact(name)); self.wait(2500)
        return self

    # ---------- step 2: Files (mount + select) ----------
    # The Files right pane is an ExtJS grid with a check-COLUMN (not the 'folderInfoCheckbox' used
    # by the backup-job Select Items dialog) — tick the top node via select_root(). Calibrated
    # headed 2026-07-07: entry, 4-step nav, backup select, RP mount, file select, and the step-3
    # recovery-type options (incl. 'Recovery to original location' + its 'Overwrite behavior').
    def wait_files_ready(self, timeout: int = 180000):
        """Wait for the recovery point to finish mounting ('Recovery point is being prepared'
        clears). Large recovery points can take minutes.

        CALIBRATED live 2026-07-08: L.PREPARING is a ci_contains() match, which tests every
        ANCESTOR's full concatenated text — not just the actual message element — so it
        matches ~11 elements (page/wizard/panel-level wrappers) whose count NEVER reaches 0
        even after the recovery point mounts, because ExtJS leaves the message markup in the
        DOM (hidden) rather than removing it. `exists()` (count-based) therefore always saw
        it as present and this loop always ran the full timeout regardless of actual mount
        state. The two genuine leaf/message-level matches are the LAST ones in document
        order (broad ancestors match first, the specific element last) and correctly report
        not-visible once mounted — check that instead of count."""
        waited, step = 0, 1500
        while waited < timeout:
            if not self.page.locator(L.PREPARING).last.is_visible():
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

    def _wait_right_panel_loading_gone(self, timeout_ms: int = 30_000):
        """Poll until the right-hand listing's 'Loading...' indicator disappears. CALIBRATED
        live 2026-07-16: navigating into a folder is genuinely async, and can take much longer
        than the short fixed waits used elsewhere in this POM (worsened by unrelated
        contention — e.g. another scheduled job running against the same source machine at the
        same time). A premature read during this window returns an empty listing that looks
        like "this folder has no content" but is really just "still loading" — confirmed live
        by re-reading the same folder again after the spinner actually cleared."""
        waited, step = 0, 1000
        while waited < timeout_ms:
            if self.page.get_by_text("Loading...", exact=False).locator("visible=true").count() == 0:
                self.wait(500)
                return self
            self.page.wait_for_timeout(step)
            waited += step
        return self

    def _drill_left_tree(self, name: str):
        """Expand `name` in the Files step's LEFT navigation tree (revealing its children so a
        deeper segment can be found), then select it via its RIGHT-PANEL row — NOT the left
        tree row — to refresh the right-hand listing. CALIBRATED live 2026-07-15/16 against
        nbr-84 (see FileLevelRecoveryLocators.left_tree_row's docstring for the two-grid
        layout): clicking the LEFT tree row to select a folder was found to be unreliable for
        at least one folder shape (a folder directly matched by an active Inclusion filter,
        rendered with a distinct "gear" icon) — it left the right-hand listing showing the
        PARENT's contents unchanged. Clicking the folder's own name in the RIGHT-hand listing
        instead (the same click a user would make to browse deeper, like a normal file
        explorer) reliably refreshes the view. Waits for the async load to genuinely finish
        (_wait_right_panel_loading_gone()) rather than a fixed sleep — a premature read looks
        exactly like an empty folder."""
        row = self.page.locator(L.left_tree_row(name)).locator("visible=true").first
        expander = row.locator("xpath=.//img[contains(@class,'x-tree-expander')]")
        if expander.count():
            expander.first.click()
            self.wait_masks_gone()
            self.wait(300)
        name_cell = self.page.locator(L.RIGHT_PANEL_ROW).locator("visible=true").locator(
            f"xpath=.//span[contains(@class,'ymiddle') and normalize-space()='{name}']"
        )
        if name_cell.count():
            name_cell.first.click()
        else:
            row.click()  # fallback: not yet shown in the right panel — select via the tree
        self._wait_right_panel_loading_gone()
        return self

    def _read_right_panel_rows(self) -> list[dict]:
        rows = self.page.locator(L.RIGHT_PANEL_ROW).locator("visible=true")
        out = []
        for i in range(rows.count()):
            tds = rows.nth(i).locator("xpath=./td")
            out.append({
                "name": tds.nth(1).inner_text().strip(),
                "modified": tds.nth(2).inner_text().strip(),
                "size": tds.nth(3).inner_text().strip(),
            })
        return out

    def drill_to(self, path_segments: list[str]):
        """Public wrapper: drill through `path_segments` (folder names from the machine root,
        e.g. ['C:', 'TestData_ForFLB']) via _drill_left_tree(), leaving the right-hand listing
        showing the final segment's contents. Browse-only — does not tick any checkbox."""
        for segment in path_segments:
            self._drill_left_tree(segment)
        return self

    def list_folder_contents(
        self, path_segments: list[str], retries: int = 2, retry_wait_ms: int = 5_000
    ) -> list[dict]:
        """Drill through `path_segments` (folder names from the machine root, e.g.
        ['C:', 'TestData_ForFLB']) — expanding via the left navigation tree, selecting via the
        right-hand listing's own row (see _drill_left_tree()) — then read back the right-hand
        listing's visible rows as [{'name', 'modified', 'size'}, ...]. Browse-only — does not
        tick any checkbox and does not affect what's selected for recovery. CALIBRATED live
        2026-07-15/16 against nbr-84 (AUTO_FLB_CHECK_FLR_BROWSE / TestData_ForFLB); assumes
        wait_files_ready() has already been called.

        If the read comes back empty, re-selects the LAST segment up to `retries` more times
        (waiting `retry_wait_ms` between attempts) before accepting it as genuinely empty —
        CALIBRATED live 2026-07-16: a savepoint that just finished (the common case in this
        test suite, which browses a job it built and ran moments earlier) can show an empty
        listing even after the 'Loading...' spinner clears and _wait_right_panel_loading_gone()
        returns, apparently because the FLR backend's own index for a brand-new savepoint isn't
        immediately ready — a separate settle delay from the UI's own loading state. A test
        whose expected result IS an empty folder (e.g. an Inclusion/Exclusion overrule case with
        no matching items) just harmlessly retries and still reads empty, at the cost of a few
        extra seconds."""
        self.drill_to(path_segments)
        out = self._read_right_panel_rows()
        attempt = 0
        while not out and attempt < retries and path_segments:
            self.wait(retry_wait_ms)
            self._drill_left_tree(path_segments[-1])
            out = self._read_right_panel_rows()
            attempt += 1
        return out

    def select_file_in_current_folder(self, filename: str):
        """Tick the checkbox for `filename`'s row in the currently-displayed right-hand
        listing (call list_folder_contents() or drill via _drill_left_tree() first). Locates
        the row via its name span (same pattern as _drill_left_tree()'s right-panel lookup),
        then walks up to the row and force-clicks its own tristatecheckcolumn checkbox input
        — a real user would tick the SAME row they just browsed into, not the name text."""
        name_cell = self.page.locator(L.RIGHT_PANEL_ROW).locator("visible=true").locator(
            f"xpath=.//span[contains(@class,'ymiddle') and normalize-space()='{filename}']"
        )
        row = name_cell.locator("xpath=ancestor::tr[contains(@class,'x-grid-row')]").first
        checkbox = row.locator("xpath=.//td[contains(@class,'tristatecheckcolumn')]//input")
        checkbox.first.click(force=True, timeout=10000)
        self.wait(500)
        return self

    def download_selected(self, save_dir, timeout_ms: int = 60_000) -> Path:
        """From the Files step with >=1 item already ticked (select_file_in_current_folder()),
        advance to Options, choose the 'Download' recovery type, click the final 'Recover'
        action, and capture the resulting browser download into `save_dir`. Returns the saved
        file's local Path. Unlike 'Recovery to original location' (deliberately never
        auto-executed by this POM — see module docstring), Download never touches the source,
        so it's safe to execute automatically."""
        self.click_next()  # Files -> Options
        self.choose_recovery_type("download")
        out_dir = Path(save_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with self.page.expect_download(timeout=timeout_ms) as dl_info:
            self.click_visible(L.RECOVER_ACTION)
        download = dl_info.value
        dest = out_dir / download.suggested_filename
        download.save_as(str(dest))
        self._close_finish_step()
        return dest

    def _close_finish_step(self):
        """Click 'Close' on the wizard's step 4 (Finish) — CALIBRATED live 2026-07-16: executing
        a recovery (e.g. via download_selected()) advances the wizard to step 4, which has NO
        'Cancel' button (only 'Close') — unlike the browse-only flow (flr_browse()), which stays
        on step 2 and exits via click_cancel(). Calling click_cancel() alone after a download
        silently failed to close anything (its 5s wait for a nonexistent 'Cancel' just times out
        and gets swallowed), leaving the wizard open — which then silently broke every
        SUBSEQUENT flb_job_cleanup teardown for that test (the Jobs sidebar isn't reachable from
        here), leaking the job. This is why every checksum-verifying Inventory TC leaked its
        AUTO_FLB_* job despite reporting PASS."""
        try:
            self.click_visible(ci_exact("Close"), timeout=10000)
            self.wait(1000)
        except Exception:
            pass
        return self

    # ---------- navigation ----------
    def click_next(self):
        self.click_visible(WizardLocators.NEXT); self.wait(2000)
        return self

    def click_cancel(self):
        """Cancel the wizard. Handles BOTH entry points: the FLB flow closes immediately on
        one click, but the FSB 'File Share Recovery Wizard' pops a 'Close the wizard?' confirm
        whose own button is ALSO labeled 'Cancel' (not 'Close') — CALIBRATED live 2026-07-08.
        After the first click, if a SECOND visible 'Cancel'-labeled element has appeared,
        click the LAST one (this app's broad/ancestor text matches consistently come first in
        document order, the specific popover button last — same pattern as elsewhere in this
        POM, e.g. BackupCopyPage's group-row state or FileLevelRecoveryLocators.PREPARING).
        A no-op click_visible(WizardLocators.CANCEL) alone would leave the FSB wizard open."""
        try:
            self.click_visible(WizardLocators.CANCEL, timeout=5000); self.wait(1000)
            confirm = self.page.locator(ci_exact("Cancel")).locator("visible=true")
            if confirm.count() > 1:
                confirm.last.click(timeout=3000)
                self.wait(1000)
        except Exception:
            pass
        return self

    def files_ready(self) -> bool:
        """True once the recovery point has mounted (the 'preparing' text is no longer
        visible). Checks .last, not the BasePage.is_visible() .first — see
        wait_files_ready()'s docstring for why a bare .first on this ci_contains() locator
        is unreliable."""
        return not self.page.locator(L.PREPARING).last.is_visible()

    def files_awaiting_selection(self) -> bool:
        """Files step gates progression until >=1 file/folder is ticked. CALIBRATED live
        2026-07-08 (behavior changed from the 2026-07-07 calibration): the 'Please select
        at least one file or folder' message is no longer shown proactively once the
        recovery point mounts, and Next is not visually disabled either — the gate is now
        REACTIVE, only appearing after an attempted Next click with nothing selected. This
        performs that (harmless — the step does not advance) attempt and reports whether
        the gate message appeared."""
        self.click_next()
        return self.page.locator(L.FILES_PROMPT).last.is_visible()

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
