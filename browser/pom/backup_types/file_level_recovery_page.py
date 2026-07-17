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

from ..common.locators import DataProtectionLocators, WizardLocators, ci_exact
from ..common.locators import FileLevelRecoveryLocators as L
from ..common.wizard_page import WizardPage


class FileLevelRecoveryPage(WizardPage):
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

    # ---------- step 1: Backup — job/machine tree + recovery-point picker (NJM-70312) ----------
    # CALIBRATED live 2026-07-16 against AUTO_FLB_NJM-70312_calib (built + cleaned up during
    # calibration; the real per-TC job is AUTO_FLB_NJM-70312, built by the test itself). The
    # Backup step has TWO independent widgets: a LEFT job/machine tree (View: 'Jobs & Groups' —
    # recover_file_level() already lands with the right job expanded and its machine row
    # selected) and a RIGHT recovery-point picker (Table view, one row per recovery point, a
    # radio per row). They never affect each other — proving TC NJM-70312 step 2's literal claim
    # that "both the backup job and a specific recovery point are independently selectable".
    def backup_step_machine_selected(self, machine_name: str) -> bool:
        """True if `machine_name`'s row in the Backup step's LEFT job/machine tree is selected
        (carries the 'x-grid-row-selected' class — same convention as the Jobs sidebar)."""
        row = self.page.locator(L.backup_step_machine_row(machine_name)).locator("visible=true").first
        return "x-grid-row-selected" in (row.get_attribute("class") or "")

    def list_recovery_points(self) -> list[dict]:
        """Read every recovery point row in the Backup step's RIGHT-hand picker (Table view):
        [{'date': <label text, e.g. '16 Jul 2026 at 6:04 pm (UTC +07:00)'>, 'selected': bool},
        ...] in DOM/display order — CALIBRATED live 2026-07-16: order is NEWEST FIRST (index 0
        = latest, matching the wizard's own default-selected radio on entry). Each row's radio
        is an <input type="button" role="radio" aria-checked="true|false"> — NOT a native
        checkbox/radio, so 'selected' is read via aria-checked, not Playwright's is_checked()."""
        rows = self.page.locator(L.RECOVERY_POINT_ROW).locator("visible=true")
        out = []
        for i in range(rows.count()):
            row = rows.nth(i)
            date_text = row.locator(L.RECOVERY_POINT_DATE_TEXT).inner_text().strip()
            radio = row.locator(L.RECOVERY_POINT_RADIO).first
            out.append({"date": date_text, "selected": radio.get_attribute("aria-checked") == "true"})
        return out

    def wait_for_recovery_point_count(
        self, job_name: str, min_count: int, timeout_ms: int = 240_000, poll_ms: int = 15_000
    ) -> list[dict]:
        """Poll (by fully CLOSING and REOPENING the FLR wizard for `job_name` — see below for
        why a same-session re-click isn't enough) until at least `min_count` recovery points are
        shown, or timeout. Returns whatever the LAST read produced.

        CALIBRATED LIVE 2026-07-16 for NJM-70312 (two separate findings):
        1. A run that just reached 'Successful' (per DataProtectionPage.wait_for_job_status())
           was repeatedly observed to still show only its OWN (latest) recovery point here —
           the PREVIOUS one temporarily missing — for well over 90 seconds afterward. This is a
           genuine appliance-side settle/indexing delay, not lost data: re-opening the same
           job's FLR wizard several minutes later (a separate, later manual check) showed both
           recovery points correctly.
        2. Simply re-clicking the (already-selected) machine row WITHIN the same still-open
           wizard instance was NOT enough to observe the delay clearing, even waiting up to 90s
           that way — only a FULL close-wizard-and-reopen-it cycle did. The picker's own data
           looks like it's fetched once when the wizard/session is first constructed and not
           re-fetched by a same-session row re-click; only a fresh session issues a fresh fetch.
        This method encapsulates that discovered protocol so callers don't have to: cancel the
        wizard, wait, reopen via recover_file_level(job_name), re-read, repeat."""
        points = self.list_recovery_points()
        waited = 0
        while len(points) < min_count and waited < timeout_ms:
            self.click_cancel()
            self.wait(poll_ms)
            waited += poll_ms
            self.recover_file_level(job_name)
            points = self.list_recovery_points()
        return points

    def select_recovery_point(self, index: int):
        """Select recovery point `index` (0-based, DOM order = newest first — see
        list_recovery_points()'s docstring) on the Backup step by clicking its radio.
        CALIBRATED live 2026-07-16: confirmed this correctly updates the Files-step header/tree
        (see current_recovery_point_label()) on the FIRST switch away from the wizard's default
        (latest) selection within a FRESH recover_file_level() session.
        ⚠ CAVEAT (found live, not exercised by NJM-70312's own test): switching AGAIN to a
        DIFFERENT recovery point after the Files step has already been visited once in the SAME
        wizard session was observed to sometimes leave the Files-step showing the PREVIOUSLY
        loaded recovery point's stale tree/header instead of the newly selected one — the
        Backup step's own radio state and the picker's list_recovery_points() readback update
        correctly every time, but the Files-step content did not always follow on a second
        switch. Open a fresh recover_file_level() session per recovery point you need to
        inspect rather than toggling back and forth within one session."""
        # CALIBRATED live 2026-07-16: the Table view's row renders partially outside the visible
        # viewport horizontally (a real horizontal scrollbar shown at the bottom of the picker).
        # Neither Playwright's own auto-scroll-into-view nor force=True alone was enough (both
        # still raise 'Element is outside of the viewport' — force=True skips actionability
        # checks but Playwright still needs real in-viewport coordinates to synthesize a mouse
        # click at all). Explicitly scroll_into_view_if_needed() first, then force-click; if
        # that somehow still fails, dispatch a real 'click' DOM event as a last resort (same
        # fallback pattern as BasePage.reveal_and_click()).
        rows = self.page.locator(L.RECOVERY_POINT_ROW).locator("visible=true")
        radio = rows.nth(index).locator(L.RECOVERY_POINT_RADIO).first
        radio.scroll_into_view_if_needed()
        try:
            radio.click(force=True, timeout=5000)
        except Exception:
            radio.dispatch_event("click")
        self.wait(800)
        return self

    def current_recovery_point_label(self, machine_name: str) -> str:
        """Read the Files-step LEFT tree's root node label (e.g. 'Window11 (Thu, 16 Jul at
        5:59 pm)') confirming which recovery point is actually loaded — CALIBRATED live
        2026-07-16. Call after click_next() from the Backup step."""
        return self.page.locator(L.files_step_root_label(machine_name)).last.inner_text().strip()

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
        """Tick the top-level backed-up node (e.g. 'C:') to satisfy the Files-step selection
        gate. CALIBRATED live 2026-07-16: L.FILES_ROOT_CHECKBOX (a 'checkcolumn' class) is stale
        — it targeted the OLD locked-panel/tree-panel split that RIGHT_PANEL_ROW's 2026-07-15
        recalibration already moved away from (current build uses 'tristatecheckcolumn', all
        columns in one <tr>). Never caught before because no passing test actually executed a
        real recovery (Download uses select_file_in_current_folder() on a named file instead).
        Ticks the FIRST row's checkbox in the right-hand listing (the root node, e.g. 'C:')."""
        row = self.page.locator(L.RIGHT_PANEL_ROW).locator("visible=true").first
        checkbox = row.locator("xpath=.//td[contains(@class,'tristatecheckcolumn')]//input")
        checkbox.first.click(force=True, timeout=10000)
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

    # ---------- step 2: Files — 'Selected for recovery' summary/list (NJM-70313) ----------
    def selected_items_count(self) -> int:
        """Read the 'Selected for recovery: N' header above the Files-step tree. CALIBRATED
        live 2026-07-16: the title element's inner_text also concatenates the adjacent 'Show'/
        'Hide'/'Clear Selection' links with no separator (e.g. 'Selected for recovery:
        2ShowClear Selection') — extract just the leading digits after the colon rather than
        matching the whole string."""
        import re
        text = self.page.locator(L.SELECTED_ITEMS_TITLE).locator("visible=true").first.inner_text()
        match = re.search(r"Selected for recovery:\s*(\d+)", text)
        return int(match.group(1)) if match else 0

    def open_selected_items_panel(self):
        """Expand the 'Selected for recovery' item list (click 'Show') if not already open.
        No-op-safe: does nothing if 'Hide' is already showing (panel already expanded)."""
        show = self.page.locator(L.SELECTED_ITEMS_SHOW_LINK).locator("visible=true")
        if show.count():
            show.first.click()
            self.wait(800)
        return self

    def selected_items_panel_text(self) -> str:
        """Open the 'Selected for recovery' panel (if needed) and return just ITS text — callers
        membership-test expected item names against it (`name in text`). CALIBRATED live
        2026-07-16 (two passes): the panel is a simple text list (Name/Path/Modified/Size
        columns) rather than a conventional ExtJS grid with per-row DOM elements — no stable
        per-row locator was found live, so this reads text rather than parsing structured rows.

        ⚠ Second-pass finding: L.SELECTED_ITEMS_PANEL's ancestor match (nearest ancestor div
        containing 'Modified') is too broad — it also captures the Files-step's LEFT-hand folder
        tree/right-hand listing above it, which has its OWN 'Name/Modified/Size' columns and
        genuinely contains files like 'atest1.txt' as real folder entries regardless of
        selection state. Reading that ancestor's raw inner_text() therefore always finds
        'atest1.txt' whether or not it's actually selected — a false positive that would make a
        deselect-assertion pass even if deselection were broken. Fix: the popup's own
        'Selected for recovery: N' header text is NOT repeated anywhere in the tree/listing
        above it, so slice from its LAST occurrence in the ancestor's text onward — this
        reliably isolates just the popup's own content, dropping everything from the ambient
        file browser above it."""
        self.open_selected_items_panel()
        full_text = self.page.locator(L.SELECTED_ITEMS_PANEL).locator("visible=true").first.inner_text()
        marker_index = full_text.rfind("Selected for recovery")
        return full_text[marker_index:] if marker_index >= 0 else full_text

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
    # click_next() is inherited from WizardPage — CONFIRMED LIVE 2026-07-17 that this wizard's
    # step header DOM does carry the same tabSwitchLinkActive-class active-tab pattern
    # WizardPage.current_step_title() depends on (title="1. Backup" resolved with the wizard
    # open), so the shared, retry-until-step-changes implementation applies here without
    # modification — this file previously carried its own weaker click()+fixed-2s-wait copy.

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

    def _select_share_type(self, share_type: str) -> str:
        """Open the 'Share type:' combo and pick 'CIFS' or 'NFS'. Returns the upper-cased target
        for the caller to branch on (e.g. whether to fill CIFS credentials).

        CALIBRATED live 2026-07-16: 'Share type:' does NOT render as a <label> element (unlike
        'Credentials type:'/'Username:'/'Password:', which do) — it's a plain x-box-item DIV in
        an HBox layout, located via its own ci_exact() text match then the FIRST VISIBLE sibling
        combo container. The combo's displayed value is an <input readonly> (its VALUE, not text
        content) — ci_exact() can't match that; open it by clicking the combo input itself, then
        pick the option from the real <li> dropdown items (those DO have real text)."""
        share_lbl = self.page.locator(L.SHARE_TYPE_LABEL).locator("visible=true").last
        combo_input = share_lbl.locator('xpath=following-sibling::div[contains(@class,"simple-combo")][1]//input')
        combo_input.first.click()
        self.wait(500)
        target = share_type.strip().upper()
        options = self.page.locator("//li[contains(@class,'x-boundlist-item')]").locator("visible=true")
        for i in range(options.count()):
            if options.nth(i).inner_text().strip().upper() == target:
                options.nth(i).click()
                break
        self.wait(800)
        return target

    def _fill_share_path(self, path: str):
        """Fill 'Path to the share:' — call after _select_share_type().

        CALIBRATED live 2026-07-16: like Share type, 'Path to the share:' isn't a <label> either
        — located via its own ci_exact() text match then the FIRST VISIBLE sibling x-field
        container (there are two sibling field DIVs at all times, a CIFS one and an NFS one;
        only one visible depending on the current Share type selection, and the field's `name`
        attribute isn't stable across a CIFS<->NFS toggle, so match by visibility, not name=).

        CALIBRATED live 2026-07-16 (multi-pass): .fill() sets the raw DOM value but never
        updates ExtJS's own internal component/data-model state for this widget — confirmed
        live via a Windows Security-log check on win-fs3 showing the SMB auth request actually
        reached the host (so the click/button-targeting was correct all along), plus explicit
        dispatch_event("change") making it WORSE (ExtJS's change handler re-read its own
        never-updated internal state and immediately overwrote the DOM back to empty). Only
        real keystroke simulation (press_sequentially) reliably updates ExtJS's model; a short
        per-keystroke delay is needed too (20ms silently dropped ~20% of characters, 80ms
        didn't). Without this, 'Test Connection' submits an EMPTY password (server-side error:
        "Password field is empty") even though the DOM shows the correct value right up until
        the click — this cost a long live-debugging session to pin down."""
        path_lbl = self.page.locator(L.PATH_TO_SHARE_LABEL).locator("visible=true").last
        path_input = path_lbl.locator(
            'xpath=following-sibling::div[contains(@class,"x-field")]'
        ).locator("visible=true").first.locator("xpath=.//input")
        path_input.first.click()
        path_input.first.press_sequentially(path, delay=80)

    def _fill_cifs_credentials(self, username: str, password: str | None):
        """Fill Username/Password — CIFS only (real <label>s, unlike Share type/Path above).
        Same press_sequentially(delay=80) requirement as _fill_share_path() — see that
        method's docstring for the full ExtJS-desync finding; applies identically here."""
        uname_field = self.page.locator("//input[@name='username']").locator("visible=true").last
        uname_field.click()
        uname_field.press_sequentially(username, delay=80)
        pwd_field = self.page.locator("//input[@name='password']").locator("visible=true").last
        pwd_field.click()
        pwd_field.press_sequentially(password or "", delay=80)

    def _click_test_connection_and_wait(self) -> bool:
        """Click 'Test Connection' and poll for the final 'Recover' action to become enabled.

        CALIBRATED live 2026-07-16: the 'Recover' button stays DISABLED until 'Test Connection'
        is clicked and succeeds (confirmed live: clicking Recover beforehand times out with
        "element is not enabled") — this applies to both CIFS and NFS. Poll for Recover to
        become enabled rather than trying to detect the success checkmark's exact DOM class — a
        more robust behavioral signal, matching this POM's established preference elsewhere
        (see _current_step_advances_on_next()'s docstring).

        CALIBRATED live 2026-07-16 (second pass): clicking TEST_CONNECTION_BUTTON via .first
        looked like it silently failed (Recover never became enabled) — but a Windows Security
        log check on win-fs3 proved the SMB auth request actually reached the host and
        succeeded. The real bug: .first on both the button and the enabled-check afterward
        resolve a stale/hidden duplicate instance, same root cause as the username/password
        fields above. Use .last consistently for every element in this CIFS/NFS block."""
        self.page.locator(L.TEST_CONNECTION_BUTTON).locator("visible=true").last.click()
        return self._wait_recover_enabled()

    def fill_custom_location(
        self, share_type: str, path: str, username: str | None = None, password: str | None = None
    ) -> bool:
        """Fill the Options step's 'Recover to custom location (CIFS/NFS)' fields — call after
        choose_recovery_type('custom'). `share_type` is 'cifs' or 'nfs'. CIFS additionally
        fills Credentials type/Username/Password; NFS has no auth, so username/password are
        ignored. Composed of _select_share_type()/_fill_share_path()/_fill_cifs_credentials()/
        _click_test_connection_and_wait() — see each method's own docstring for the specific
        live-calibration finding behind it (several cost a long live-debugging session to pin
        down; the details are preserved there, not repeated here)."""
        target = self._select_share_type(share_type)
        self._fill_share_path(path)
        if target == "CIFS" and username is not None:
            self._fill_cifs_credentials(username, password)
        return self._click_test_connection_and_wait()

    def _wait_recover_enabled(self, timeout_ms: int = 20_000) -> bool:
        recover_btn = self.page.locator(L.RECOVER_ACTION).locator("visible=true").last
        waited, step = 0, 500
        while waited < timeout_ms:
            if recover_btn.is_enabled():
                return True
            self.page.wait_for_timeout(step)
            waited += step
        return False

    def execute_custom_location_recovery(self) -> bool:
        """Click the final 'Recover' action for a filled-in custom-location (CIFS/NFS)
        recovery, confirm the wizard's own step-4 confirmation text ("The File Level recovery
        has started") appeared, then close via 'Close' (see _close_finish_step()'s docstring —
        this recovery type also lands on step 4, same as Download). Unlike 'Recovery to
        original location', this never touches the source. Returns whether the confirmation was
        seen — callers should assert on this rather than treating "no exception raised" as
        proof the recovery actually started."""
        self.page.locator(L.RECOVER_ACTION).locator("visible=true").last.click()
        self.wait(1500)
        started = self.page.get_by_text("The File Level recovery has started", exact=False).locator(
            "visible=true"
        ).count() > 0
        self._close_finish_step()
        return started

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
