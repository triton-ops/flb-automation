"""FlbWizardPage — File-Level Backup job wizard (NBR 11.2.1, 6-step).

CALIBRATED live 2026-07-06 against nbr-84. Flow:
  Source (pick machine -> Select Items dialog: drill + tick folders/files -> Apply)
  -> Inclusion -> Exclusion -> Destination (pick repo) -> Schedule -> Options (name)
  -> Finish / Finish & Run (-> Run dialog).

ExtJS quirks handled: all step panels live in the DOM at once (use .first); tree checkboxes
and the hover-revealed edit pencil need force/hover clicks (see BasePage helpers).
"""
from __future__ import annotations
from .wizard_page import WizardPage
from .locators import (FlbWizardLocators, SelectItemsLocators, DestinationLocators,
                       ScheduleLocators, OptionsLocators, RunDialogLocators, WizardLocators)


class FlbWizardPage(WizardPage):
    LOC = FlbWizardLocators

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

    def picker_apply(self):
        self.click(SelectItemsLocators.APPLY)
        self.wait(1500)
        return self

    def picker_cancel(self):
        self.click(SelectItemsLocators.CANCEL)
        self.wait(1000)
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
        # click the visible row label (the checkbox input itself is styled/hidden)
        self.click_visible(ScheduleLocators.DO_NOT_SCHEDULE_ROW)
        self.wait(800)
        return self

    # ---------- Options step ----------
    def set_job_name(self, name: str):
        loc = self.page.locator(OptionsLocators.JOB_NAME).locator("visible=true").first
        loc.click(); loc.fill(""); loc.type(name)
        return self

    def finish(self):
        self.click(WizardLocators.FINISH)
        self.wait(2000)
        return self

    def finish_and_run(self):
        self.click(WizardLocators.FINISH_RUN)
        self.wait(2000)
        return self

    def confirm_run(self):
        self.click(RunDialogLocators.RUN)
        self.wait(2000)
        return self

    # ---------- legacy (kept for compatibility) ----------
    def select_all_windows(self):
        self.click(FlbWizardLocators.ALL_WINDOWS_MACHINES); self.wait(1500); return self

    def select_all_linux(self):
        self.click(FlbWizardLocators.ALL_LINUX_MACHINES); self.wait(1500); return self
