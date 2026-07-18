"""FlbWizardPage — File-Level Backup job wizard (NBR 11.2.1, 6-step).

CALIBRATED live 2026-07-06 against nbr-84. Flow:
  Source (pick machine -> Select Items dialog: drill + tick folders/files -> Apply)
  -> Inclusion -> Exclusion -> Destination (pick repo) -> Schedule -> Options (name)
  -> Finish / Finish & Run (-> Run dialog).

ExtJS quirks handled: all step panels live in the DOM at once (use .first); tree checkboxes
and the hover-revealed edit pencil need force/hover clicks (see BasePage helpers).
"""
from __future__ import annotations

from ..common.locators import (
    DestinationLocators,
    FlbWizardLocators,
    InclusionExclusionLocators,
    OptionsLocators,
    RunDialogLocators,
    ScheduleLocators,
    SelectItemsLocators,
    WizardLocators,
)
from ..common.wizard_page import WizardPage


class FlbWizardPage(WizardPage):
    # Explicit WizardLocators (not FlbWizardLocators): keeps this reassignment from narrowing the
    # attribute's type for FlbWizardPage's own subclasses (e.g. FileShareBackupPage), which
    # legitimately assign a sibling WizardLocators subtype, not a further-narrowed FlbWizardLocators
    # subtype — see WizardPage.LOC's own comment for the same reasoning at the base.
    LOC: type[WizardLocators] = FlbWizardLocators

    # ---------- Source step: machine tree ----------
    def expand_windows(self):
        self.click(FlbWizardLocators.tree_expander("All Windows machines"))
        self.wait(1200)
        return self

    def expand_linux(self):
        self.click(FlbWizardLocators.tree_expander("All Linux machines"))
        self.wait(1200)
        return self

    def select_machine(self, name: str):
        """Tick a discovered machine (e.g. 'Windown'). The tree checkbox is force-clicked."""
        self.click_force(FlbWizardLocators.machine_checkbox(name))
        self.wait(1200)
        return self

    # ---------- Source step: Select Items dialog ----------
    def open_item_picker(self):
        """Open the per-machine 'Select Items' modal via the hover-revealed pencil icon."""
        self.reveal_and_click(FlbWizardLocators.SELECTED_HEADER, FlbWizardLocators.EDIT_ICON)
        self.wait(2000)
        return self

    def picker_drill(self, name: str):
        """Drill into a folder in the Select Items dialog (click its name link)."""
        self.click(SelectItemsLocators.drill(name))
        self.wait(800)
        self.wait_masks_gone()   # the folder contents load behind an x-mask overlay
        return self

    def picker_check(self, name: str):
        """Tick a folder or file row in the Select Items dialog. Waits for the loading mask to
        clear, then clicks the visible checkmark (falls back to force-clicking the input)."""
        self.wait_masks_gone()
        try:
            self.click_visible(SelectItemsLocators.checkmark(name), timeout=5000)
        except Exception:
            self.click_force(SelectItemsLocators.checkbox(name))
        self.wait(600)
        return self

    def picker_selected_count(self) -> str:
        return self.get_text(SelectItemsLocators.FOOTER_COUNT)

    # ---------- Select Items dialog: readers (CALIBRATED live 2026-07-18) ----------
    # All readers scope to the VISIBLE dialog copy: ExtJS keeps hidden duplicate windows in the
    # DOM (a fresh copy each time the picker is reopened). No asserts / no waits here — they return
    # UI state; assertions belong in the test.
    def _vis(self, selector: str):
        return self.page.locator(selector).locator("visible=true")

    def picker_dialog_open(self) -> bool:
        return self._vis(SelectItemsLocators.DIALOG).count() > 0

    def picker_title(self) -> str:
        loc = self._vis(SelectItemsLocators.TITLE)
        return loc.first.inner_text() if loc.count() else ""

    def picker_row_names(self) -> list[str]:
        """Visible name-link texts (a.slText) of the current FOLDER LISTING only, in order —
        includes the '[..]' up-level row when present. Used to assert the volume-view default
        (e.g. 'Local Disk (C:)'), that hidden folders appear (e.g. 'ProgramData' — NJM-70383), etc.

        RE-CALIBRATED live 2026-07-18: must scope to `.folderInfoItem` rows specifically — the
        bare 'a.slText' class is ALSO used by the Show/Hide/Clear-Selection control links that sit
        in a separate sibling container above the listing, so an unscoped query returns those 3
        extra strings alongside the real rows (caught live: a 200-item folder's exact-count
        listing came back as 203, not 200, before this fix)."""
        loc = self._vis(SelectItemsLocators.DIALOG +
                         "//div[contains(@class,'folderInfoItem')]//a[contains(@class,'slText')]")
        return [t.strip() for t in loc.all_inner_texts()]

    def picker_breadcrumb_text(self) -> str:
        loc = self._vis(SelectItemsLocators.BREADCRUMB_BAR)
        return loc.first.inner_text().strip() if loc.count() else ""

    def picker_up_one_level_present(self) -> bool:
        return self._vis(SelectItemsLocators.UP_ONE_LEVEL_ROW).count() > 0

    def picker_search_clear_visible(self) -> bool:
        loc = self._vis(SelectItemsLocators.SEARCH_CLEAR)
        return bool(loc.count()) and loc.first.is_visible()

    def picker_apply_enabled(self) -> bool:
        """True when the Apply button is NOT disabled (no 'x-btn-disabled' on its outer div.x-btn)."""
        loc = self._vis(SelectItemsLocators.APPLY_BUTTON)
        if not loc.count():
            return False
        cls = loc.first.get_attribute("class") or ""
        return "x-btn-disabled" not in cls

    def picker_row_disabled(self, name: str) -> bool:
        """True when the row named `name` (matched by its visible anchor text) has a disabled
        checkbox — i.e. a system folder or a row blocked by the 200-item cap."""
        loc = self._vis(SelectItemsLocators.checkbox_by_text(name))
        return bool(loc.count()) and (loc.first.get_attribute("disabled") is not None)

    def picker_row_tooltip(self, name: str) -> str:
        """The hover-tooltip @title on the row named `name` (matched by anchor text). For a
        selectable row this equals the folder name; for a disabled row it is the reason string
        ('System folder is not supported.' / 'Maximum selected items were reached.')."""
        loc = self._vis(SelectItemsLocators.name_link_by_text(name))
        return (loc.first.get_attribute("title") or "") if loc.count() else ""

    def picker_over_200_message_shown(self) -> bool:
        """RE-CALIBRATED live 2026-07-18: True when the current folder/volume listing shows the
        '>200 results' banner (SelectItemsLocators.OVER_200_MESSAGE) — real and matches the TC
        spec text verbatim (see that locator's docstring)."""
        return self._vis(SelectItemsLocators.OVER_200_MESSAGE).count() > 0

    def picker_selected_items_panel_expanded(self) -> bool:
        """True when the Selected Items grid (Name/Path columns) is currently expanded (the
        toggle link reads 'Hide'). RE-CALIBRATED live 2026-07-18 — corrects an earlier same-day
        pass that wrongly concluded no such panel exists (see SELECTED_ITEMS_TOGGLE's docstring)."""
        loc = self._vis(SelectItemsLocators.SELECTED_ITEMS_TOGGLE)
        return bool(loc.count()) and loc.first.inner_text().strip().lower() == "hide"

    def picker_selected_items_rows(self) -> list[dict]:
        """The expanded Selected Items grid's rows as [{'name','path'}, ...] (empty if the panel
        isn't expanded or nothing is selected). Reads the Name/Path grid cells directly — no
        assertions here, callers assert on the returned data."""
        rows = self._vis(SelectItemsLocators.SELECTED_ITEMS_ROWS)
        out: list[dict] = []
        for i in range(rows.count()):
            row = rows.nth(i)
            name_el = row.locator("xpath=.//span[@title]").first
            path_el = row.locator("xpath=.//p[contains(@class,'pathEl')]").first
            out.append({
                "name": name_el.get_attribute("title") or "",
                "path": path_el.inner_text().strip() if path_el.count() else "",
            })
        return out

    # ---------- Select Items dialog: extra actions (CALIBRATED live 2026-07-18) ----------
    def picker_toggle_selected_items(self):
        """Click the Show/Hide toggle to expand or collapse the Selected Items grid."""
        self.click_force(SelectItemsLocators.SELECTED_ITEMS_TOGGLE)
        self.wait(500)
        return self

    def picker_deselect_via_panel(self, name: str):
        """Deselect `name` directly from the expanded Selected Items grid's per-row delete icon
        (requires the panel to already be expanded — call picker_toggle_selected_items() first)."""
        self.click_force(SelectItemsLocators.selected_items_row_delete(name))
        self.wait(500)
        return self


    def picker_select_all(self):
        """Tick the list-header 'Select all' checkbox (selects from the top, capped at 200)."""
        self.wait_masks_gone()
        self.click_force(SelectItemsLocators.SELECT_ALL)
        self.wait(800)
        return self

    def picker_up_one_level(self):
        """Navigate up one folder via the synthetic '[..]' row (no dedicated toolbar button)."""
        return self.picker_drill("[..]")

    def picker_breadcrumb_click(self, name: str):
        """Jump to a named breadcrumb segment (e.g. 'C:')."""
        self.click_visible(SelectItemsLocators.breadcrumb_segment(name))
        self.wait(800)
        self.wait_masks_gone()
        return self

    def picker_search(self, text: str):
        """Type into the dialog search box with REAL per-character keystrokes. CALIBRATED live
        2026-07-18: the clear/X control (searchTrigger2) is revealed by the field's keyup
        handler, which a bare fill() does NOT fire (fill sets the value + one 'input' event only),
        so press_sequentially is required for the clear control to appear — same real-keystroke
        lesson as BasePage.fill_reliable(). NOTE: typing here does NOT filter the listing in this
        build (verified live — a matching and a non-matching term both leave the full listing
        unchanged); kept for completeness / future builds — do not rely on it narrowing results."""
        loc = self._vis(SelectItemsLocators.SEARCH_INPUT).first
        loc.click(force=True)
        loc.fill("")
        loc.press_sequentially(text, delay=60)
        self.wait(800)
        return self

    def picker_clear_search(self):
        """Empty the search box. CALIBRATED live 2026-07-18: clears via real keyboard input
        (select-all + Delete) on the field, which reliably empties it AND fires the keyup that
        hides the searchTrigger2 control. The searchTrigger2 div (SEARCH_CLEAR) is the on-screen
        control that appears with text, but its two sibling triggers carry no title/aria to
        distinguish clear-vs-search and force-clicking it was observed to disturb the listing —
        so the keyboard path is used for a dependable reset."""
        loc = self._vis(SelectItemsLocators.SEARCH_INPUT).first
        loc.click(force=True)
        loc.press("Control+a")
        loc.press("Delete")
        self.wait(500)
        return self

    def picker_apply(self):
        # RE-CALIBRATED live 2026-07-18: must use click_visible(), not click() — SelectItemsLocators
        # now scopes APPLY/CANCEL to DIALOG (fixing a real ambiguity with the wizard's own outer
        # Cancel button — see that locator's docstring), but the dialog CONTAINER itself still
        # accumulates hidden duplicate copies each time the picker is reopened within one wizard
        # session (this class's own docstring), so a bare click()/.nth(0) can still resolve a
        # stale, never-visible duplicate on a test that reopens the picker more than once.
        self.click_visible(SelectItemsLocators.APPLY)
        self.wait(1500)
        return self

    def select_items(self, drill_path: list[str], checks: list[str]):
        """High-level: from the machine root, drill through `drill_path` (folder titles, e.g.
        ['Local Disk (C:)','TestData_ForFLB']) then tick each name in `checks`.
        For items in different sub-folders, call picker_drill/picker_check directly instead."""
        for folder in drill_path:
            self.picker_drill(folder)
        for name in checks:
            self.picker_check(name)
        return self

    # ---------- Inclusion / Exclusion steps ----------
    def _blur_active_field(self):
        """Blur the currently-focused field by clicking a definitely-inert element (the wizard
        title text). CALIBRATED 2026-07-08: pressing Tab was tried first but its landing spot
        depends on this page's full tab order, which is large/unpredictable in this layout —
        one Tab press was observed landing focus on the 'Cancel' button (visible focus ring),
        which is far worse than not blurring at all. Clicking inert text has no such risk."""
        try:
            self.page.locator("//*[contains(normalize-space(.),'Job Wizard for')]").first.click(timeout=2000)
        except Exception:
            pass
        self.wait(600)

    def _tick_checkbox_robust(self, selector: str, timeout_ms: int = 15000):
        """Force-click a VISIBLE checkbox, polling until it actually appears first. Measured
        live 2026-07-08: right after an adjacent step does extra work (e.g. filling a textarea,
        which fires its own change/blur cycle), the NEXT step's transition can take noticeably
        longer than the standard post-click_next() wait — a bare force-click landing right at
        that boundary intermittently times out even though the element renders fine a moment
        later. Poll-and-retry instead of a single attempt."""
        self.wait_masks_gone()
        loc = self.page.locator(selector).locator("visible=true")
        waited = 0
        step = 500
        while waited < timeout_ms:
            if loc.count() > 0:
                try:
                    loc.first.click(timeout=2000, force=True)
                    return
                except Exception:
                    pass
            self.page.wait_for_timeout(step)
            waited += step
        loc.first.click(timeout=5000, force=True)   # final attempt — let it raise if still stuck

    def _enable_pattern_field(self, checkbox_loc: str, textarea_loc: str, patterns: list[str]):
        """Tick a wildcard-pattern checkbox (if not already ticked) and fill its textarea (one
        item per line, '*'/'?' wildcards) — shared by enable_inclusion()/enable_exclusion(),
        which are identical in shape and differ only in which pair of locators they pass here.

        FIXED 2026-07-15 (two bugs found live, correcting/retyping a pattern set within the
        same wizard visit — needed by TCs like the invalid-parameter-highlighting check):
        1. BasePage.fill() resolves an UNSCOPED `.first`, so a second call could silently
           fill a hidden duplicate instead of the visible textarea — resolve the VISIBLE
           textarea directly here instead of going through the unscoped self.fill().
        2. _tick_checkbox_robust() unconditionally force-clicks the checkbox every call. The
           checkbox's own `.checked` DOM property was verified live to NOT reflect the real
           state (reads false even while the textarea is visibly enabled — ExtJS tracks the
           actual on/off state some other way), so it can't be used as a guard either. The
           textarea's OWN visibility is the one reliable signal: a second call when the
           textarea is already visible must NOT click the checkbox again, or it silently
           toggles the field back OFF and hides it (content is retained but invisible, and
           the next .fill() times out waiting for it)."""
        textarea = self.page.locator(textarea_loc).locator("visible=true")
        if textarea.count() == 0:
            self._tick_checkbox_robust(checkbox_loc)
            self.wait(600)
            textarea = self.page.locator(textarea_loc).locator("visible=true")
        textarea.first.fill("\n".join(patterns))
        self._blur_active_field()
        return self

    def enable_inclusion(self, patterns: list[str]):
        """Tick 'Include items' (if not already ticked) and fill its wildcard-pattern textarea
        — see _enable_pattern_field()'s docstring for the two live-found bugs this guards
        against. The checkbox's label does not forward clicks — force-click the VISIBLE input
        directly (ExtJS keeps a hidden duplicate of this step in the DOM too; verified live
        2026-07-08)."""
        return self._enable_pattern_field(
            InclusionExclusionLocators.INCLUDE_CHECKBOX, InclusionExclusionLocators.INCLUDE_TEXTAREA, patterns
        )

    def enable_exclusion(self, patterns: list[str]):
        """Tick 'Exclude items' (if not already ticked) and fill its wildcard-pattern
        textarea. Same fixes as enable_inclusion() — see _enable_pattern_field()."""
        return self._enable_pattern_field(
            InclusionExclusionLocators.EXCLUDE_CHECKBOX, InclusionExclusionLocators.EXCLUDE_TEXTAREA, patterns
        )

    def _current_step_advances_on_next(self) -> bool:
        """Click Next once and report whether the active step tab actually changed — the
        ONLY reliable validation signal for Inclusion/Exclusion, CALIBRATED live 2026-07-15:
        this build shows NO CSS invalid-highlight and NO "Invalid parameters" message for a
        rejected entry (verified with a space-containing name, e.g. 'My file.xlsx' — the
        wizard silently refuses to advance past the step, with zero visual feedback anywhere
        in the DOM). A single click is enough here (not the retrying click_next()): an
        invalid entry never becomes valid by re-clicking, so there is no timing race to
        retry for — retrying would only waste time waiting out a block that will never lift.
        Side effect: if the content IS valid, this genuinely advances the wizard to the next
        step, same as click_next()."""
        before = self.current_step_title()
        self.click_visible(self.LOC.NEXT)
        self.wait(1500)
        after = self.current_step_title()
        return bool(after) and after != before

    def inclusion_advances_wizard(self) -> bool:
        """True if the current Inclusion-step content is accepted (Next actually advances
        to Exclusion). Named for the side effect, not a pure predicate — see
        _current_step_advances_on_next()'s docstring for why a behavioral check is the only
        one available in this build (no visible invalid-state feedback exists)."""
        return self._current_step_advances_on_next()

    def exclusion_advances_wizard(self) -> bool:
        """Same as inclusion_advances_wizard() but for the Exclusion step (advances to
        Destination on success)."""
        return self._current_step_advances_on_next()

    # ---------- Destination step ----------
    def select_repository(self, repo_name: str):
        # ExtJS keeps hidden duplicates of every step in the DOM -> click the VISIBLE combo/option.
        try:
            self.click_visible(DestinationLocators.COMBO, timeout=8000)
        except Exception:
            self.click_visible(DestinationLocators.COMBO_TRIGGER)
        self.wait(1000)
        self.click_visible(DestinationLocators.option(repo_name))
        self.wait(1000)
        return self

    # ---------- Schedule step ----------
    def set_run_on_demand(self):
        """Tick 'Do not schedule, run on demand', collapsing the recurring-schedule form.
        FIXED 2026-07-08: the label text renders twice in the DOM (once as the real checkbox,
        once as a permanently-disabled mirror) — must force-click the input scoped to
        'schedule-item-line', not rely on ci_exact text + click_visible (see locators.py)."""
        self._tick_checkbox_robust(ScheduleLocators.DO_NOT_SCHEDULE_CHECKBOX)
        self.wait(800)
        return self

    def set_retention(self, count: int, unit: str = "days"):
        """Set 'Keep backups for <count> <unit>' on the default recurring schedule (Schedule
        #1). Only visible when NOT in run-on-demand mode. `unit` must match a combo option
        exactly (e.g. 'days', 'weeks', 'months', 'years').

        Uses fill_reliable() rather than a bare fill(), not because a desync was ever observed
        here (this method has no test caller yet, so there's no evidence either way) but because
        the field shape — an ExtJS text input whose value must be read correctly by the wizard's
        own save/validation logic — is structurally the same as the confirmed-broken FLR CIFS
        credentials fields (see BasePage.fill_reliable()'s docstring). Precautionary, not a fix
        for an observed bug."""
        self.fill_reliable(ScheduleLocators.KEEP_BACKUPS_FOR_COUNT, str(count))
        self.click_visible(ScheduleLocators.KEEP_BACKUPS_FOR_UNIT_COMBO)
        self.wait(500)
        self.click(f"//li[normalize-space()='{unit}']")
        self.wait(500)
        return self

    def set_immutable(self, days: int):
        """Tick 'Immutable for <days> days' — maps to options.retentionPolicy.keepImmutableCount.
        Only visible when NOT in run-on-demand mode (same recurring-schedule retention block as
        set_retention). Force-click the checkbox — same non-native-checkbox caveat as elsewhere.

        Uses fill_reliable() for the days field for the same precautionary reason as
        set_retention() above — untested against the ExtJS-desync failure mode, same field
        shape as the confirmed-broken case."""
        self._tick_checkbox_robust(ScheduleLocators.IMMUTABLE_FOR_CHECKBOX)
        self.wait(500)
        self.fill_reliable(ScheduleLocators.IMMUTABLE_FOR_DAYS, str(days))
        return self

    # ---------- Options step ----------
    def set_job_name(self, name: str):
        loc = self.page.locator(OptionsLocators.JOB_NAME).locator("visible=true").first
        loc.click(); loc.fill(""); loc.type(name)
        return self

    def set_encryption(self, enabled: bool):
        """Toggle 'Backup encryption' Disabled/Enabled. Enabling reveals a 'settings' link for
        the password — NOT yet calibrated (see NJM-123510 / recipes.md follow-up)."""
        self.click(OptionsLocators.ENCRYPTION_COMBO_INPUT)
        self.wait(500)
        label = "Enabled" if enabled else "Disabled"
        self.click(OptionsLocators.encryption_option(label))
        self.wait(500)
        return self

    def finish(self):
        self.click(WizardLocators.FINISH)
        self.wait(2000)
        return self

    def finish_and_run(self):
        """Click 'Finish & Run' (builds the job AND immediately opens the 'Run this job?'
        confirm dialog — same dialog DataProtectionPage.run_job() confirms via confirm_run()
        below). CALIBRATED live 2026-07-18 for the immutability build/run calibration
        (NJM-70517): needed because finish() alone only saves the job without running it, and
        a separate DataProtectionPage.run_job() call would re-select the job from the sidebar
        redundantly when the wizard can launch the first run directly."""
        self.click(WizardLocators.FINISH_RUN)
        self.wait(2000)
        return self

    def confirm_run(self):
        self.click(RunDialogLocators.RUN)
        self.wait(2000)
        return self

    # ---------- EDIT mode (DataProtectionPage.edit_job()) ----------
    def goto_step(self, step_locator: str):
        """Click a step tab directly (e.g. WizardLocators.STEP_SOURCE) — needed when re-entering
        an EXISTING job's wizard via Edit, which does not reliably land on '1. Source' (see
        DataProtectionPage.edit_job()'s docstring). No-op-safe to call even if already on that
        step."""
        self.click_visible(step_locator)
        self.wait(1000)
        return self

    def save(self):
        self.click(WizardLocators.SAVE)
        self.wait(2000)
        return self

    def save_and_run(self):
        self.click(WizardLocators.SAVE_RUN)
        self.wait(2000)
        return self

    def set_run_dialog_backup_type(self, kind: str):
        """Set the 'Run this job?' dialog's 'Backup type' combo. `kind` is 'Incremental' or
        'Full' (exact dropdown option text). CALIBRATED live 2026-07-16: this combo is ONLY
        rendered when the job already has a prior recovery point (a RE-run via Save & Run/
        Manage -> Run — never shown on a job's very first run, see confirm_run()/RUN_BUTTON
        elsewhere). Used by this suite's edit_flb_job_and_rerun() to force a FULL re-scan after
        changing the job's Source-step item selection, so the new recovery point's file tree
        cleanly reflects the new selection rather than an incremental delta against the old
        one."""
        combo = self.page.locator(RunDialogLocators.BACKUP_TYPE_COMBO_INPUT).locator("visible=true").first
        combo.click()
        self.wait(500)
        self.page.locator(f"//li[normalize-space()='{kind}']").locator("visible=true").first.click()
        self.wait(500)
        return self
