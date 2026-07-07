"""Central locator repository for the NBR Director UI POM — XPATH, case-insensitive.

The NBR web UI is ExtJS: text is rendered in nested wrappers and often CSS-uppercased
(text-transform), so Playwright get_by_text AND raw-cased XPath text()='LOG IN' are unreliable.
We match on the leaf text node, lower-cased via translate() -> robust to casing/transform.

  ci_exact('Backup copy')    -> exact (lower-cased) text-node match; 'Backup copy' does NOT
                                match the 'BACKUP COPY JOB' header (exact, not substring).
  ci_contains('...')         -> substring match (titles, hints).

Page objects pass these to BasePage.click/fill/exists/is_visible (Playwright treats '//' as XPath).
"""

_UP = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_LO = "abcdefghijklmnopqrstuvwxyz"


def ci_exact(label: str) -> str:
    # Match on the element's full normalized string value '.' (not direct text()): ExtJS nests
    # the label in child spans, so text() misses it. '.' + exact avoids the 'BACKUP COPY JOB' header.
    return f"//*[normalize-space(translate(.,'{_UP}','{_LO}'))='{label.lower()}']"


def ci_contains(label: str) -> str:
    return (f"//*[contains(normalize-space(translate(.,'{_UP}','{_LO}')),"
            f"'{label.lower()}')]")


class LoginLocators:
    USERNAME = "//input[@name='username']"   # VERIFIED
    PASSWORD = "//input[@type='password']"   # VERIFIED
    SUBMIT = ci_exact("LOG IN")              # CI handles CSS-uppercased button text


class DataProtectionLocators:
    LEFT_NAV = ci_exact("Data Protection")
    CREATE_ADD = "//*[contains(@class,'create-btn')]"   # VERIFIED stable selector for the '+' button
    CREATE_ADD_XY = (494, 138)               # coordinate fallback (shifts when banners appear)
    MENU_FLB = ci_exact("File level backup for physical machine")
    MENU_BACKUP_COPY = ci_exact("Backup copy")          # exact -> not 'BACKUP COPY JOB' header
    MENU_FILE_SHARE = ci_exact("Backup for file share")
    RECOVER_BUTTON = ci_exact("Recover")

    @staticmethod
    def job_row(name: str) -> str:
        return ci_exact(name)


class WizardLocators:
    """Shared job-wizard controls. CALIBRATED against the NBR 11.2.1 FLB wizard (2026-07-06).

    The 11.2.1 FLB wizard has SIX steps: 1.Source 2.Inclusion 3.Exclusion 4.Destination
    5.Schedule 6.Options (the old nbr-149 2-step Source/Destination layout is gone). ExtJS
    renders ALL step panels in the DOM at once (hidden until active), so text selectors must
    use .first + a visibility check — a raw text match will also hit hidden steps.
    """
    NEXT = ci_exact("Next")
    NEXT_DISABLED = ("//*[normalize-space(translate(text(),'" + _UP + "','" + _LO + "'))='next']"
                     "/ancestor-or-self::*[contains(@class,'x-btn-disabled') or "
                     "contains(@class,'disabled')][1]")
    CANCEL = ci_exact("Cancel")
    FINISH = "//span[contains(@class,'x-btn-inner') and normalize-space()='Finish']"
    FINISH_RUN = "//span[contains(@class,'x-btn-inner') and normalize-space()='Finish & Run']"
    # step headers
    STEP_SOURCE = ci_exact("1. Source")
    STEP_INCLUSION = ci_exact("2. Inclusion")
    STEP_EXCLUSION = ci_exact("3. Exclusion")
    STEP_DESTINATION = ci_exact("4. Destination")
    STEP_SCHEDULE = ci_exact("5. Schedule")
    STEP_OPTIONS = ci_exact("6. Options")
    NO_SELECTION = ci_contains("No item(s) selected")
    SELECT_AT_LEAST_ONE = ci_contains("Select at least one item")
    SEARCH_BOX = "//input[@placeholder='Search']"


class FlbWizardLocators(WizardLocators):
    TITLE = ci_contains("New File Level Backup Job Wizard")
    ALL_LINUX_MACHINES = ci_exact("All Linux machines")
    ALL_WINDOWS_MACHINES = ci_exact("All Windows machines")

    # --- Source step: machine tree (ExtJS treegrid) ---
    @staticmethod
    def tree_expander(label: str) -> str:
        # the +/- expander img in the tree row whose cell text contains `label`
        return (f"//div[contains(@class,'x-grid-cell-inner') and "
                f"contains(normalize-space(.),'{label}')]//img[contains(@class,'x-tree-expander')]")

    @staticmethod
    def machine_checkbox(name: str) -> str:
        # the row checkbox (input.x-tree-checkbox) in the tree row for machine `name`.
        # NOTE: the input is not "visible" to Playwright — click with force=True.
        return (f"//tr[contains(@class,'x-grid-row')][.//div[contains(@class,'x-grid-cell-inner') "
                f"and contains(normalize-space(.),'{name}')]]//input[contains(@class,'x-tree-checkbox')]")

    # --- Source step: right-hand "selected machines" panel ---
    SELECTED_HEADER = "//div[contains(@class,'pessSelViewHeader')]"          # hover to reveal icons
    EDIT_ICON = "//div[contains(@class,'iconEdit24')]"                       # pencil -> opens Select Items
    SELECTED_NOTE = "//div[contains(@class,'pessSelViewFooterNoteForItem')]"  # 'No item(s) selected' / 'N item(s) selected'


class SelectItemsLocators:
    """The per-machine 'Select Items' modal (browse the source filesystem, tick folders/files)."""
    DIALOG = ("//div[contains(@class,'x-window')][.//span[contains(@class,'x-window-header-text') "
              "and normalize-space()='Select Items']]")
    APPLY = "//span[contains(@class,'x-btn-inner') and normalize-space()='Apply']"
    CANCEL = "//span[contains(@class,'x-btn-inner') and normalize-space()='Cancel']"
    # footer reads 'Selected for Physical Machine: N' (FLB) or 'Selected for File Share: N' (FSB)
    FOOTER_COUNT = ("//div[contains(@class,'textComment1') and "
                    "contains(normalize-space(.),'Selected for')]")

    @staticmethod
    def row(name: str) -> str:
        return (f"//div[contains(@class,'folderInfoItem')][.//div[contains(@class,'folderInfoItemName') "
                f"and @title='{name}']]")

    @staticmethod
    def drill(name: str) -> str:
        # clicking the name link drills into a folder
        return SelectItemsLocators.row(name) + "//div[contains(@class,'folderInfoItemName')]"

    @staticmethod
    def checkbox(name: str) -> str:
        # the row's checkbox input (force-click; the visible mark is span.checkmark)
        return SelectItemsLocators.row(name) + "//input[@role='checkbox']"

    @staticmethod
    def checkmark(name: str) -> str:
        # the visible checkbox glyph in the row (preferred click target after masks clear)
        return SelectItemsLocators.row(name) + "//span[contains(@class,'checkmark')]"


class DestinationLocators:
    COMBO = ("//div[contains(@class,'glT1') and contains(normalize-space(.),'Select a target destination')]")
    COMBO_TRIGGER = "//div[contains(@class,'glTR') and contains(@class,'isTrigger')]"

    @staticmethod
    def option(repo_name: str) -> str:
        return ci_exact(repo_name)


class ScheduleLocators:
    # 'Do not schedule, run on demand' — anchored on the label text (two rows carry this label:
    # schedule-item-line + manual-schedule; click the VISIBLE one on the active Schedule step).
    DO_NOT_SCHEDULE_ROW = ci_exact("Do not schedule, run on demand")
    DO_NOT_SCHEDULE = "//div[contains(@class,'manual-schedule')]//input[contains(@class,'x-form-checkbox')]"


class OptionsLocators:
    # Job name text field: the input inside the x-field whose label is 'Job name:'
    JOB_NAME = ("//div[contains(@class,'x-field')][.//label[normalize-space()='Job name:']]"
                "//input[contains(@class,'x-form-text')]")


class RunDialogLocators:
    DIALOG = ("//div[contains(@class,'x-window')][.//*[contains(normalize-space(.),'Run this job?')]]")
    RUN = "//span[contains(@class,'x-btn-inner') and normalize-space()='Run']"


class FileShareBackupLocators(WizardLocators):
    TITLE = ci_contains("Backup Job Wizard for File Share")
    ALL_FILE_SHARES = ci_exact("All File shares")


class BackupCopyLocators(WizardLocators):
    TITLE = ci_contains("Backup Copy Job Wizard")   # TODO confirm


class FileLevelRecoveryLocators:
    """File-Level Recovery flow — CALIBRATED live 2026-07-06 on nbr-84.

    Entry: select a job -> 'Recover' -> 'File level recovery'. The FLR wizard has FOUR steps:
    1. Backup (pick backup + recovery point) -> 2. Files (WAITS for the recovery point to MOUNT,
    then browse/select) -> 3. Options (Recovery type: Download / Recover to original location /
    Export to CIFS|NFS share) -> 4. Finish.
    """
    RECOVER_BUTTON = ci_exact("Recover")                 # top action after selecting a job (VERIFIED)
    MENU_FILE_LEVEL = ci_exact("File level recovery")    # Recover -> GRANULAR RECOVERY submenu (VERIFIED)
    # step headers (VERIFIED)
    STEP_BACKUP = ci_exact("1. Backup")
    STEP_FILES = ci_exact("2. Files")
    STEP_OPTIONS = ci_exact("3. Options")
    STEP_FINISH = ci_exact("4. Finish")
    # step 2 shows this mask text while the recovery point mounts — wait for it to clear
    PREPARING = ci_contains("Recovery point is being prepared")
    # once mounted, step 2 gates the footer until a file/folder is ticked (prompt shown meanwhile)
    FILES_PROMPT = ci_contains("Please select at least one file or folder")
    # Files right-pane is an ExtJS grid with a check-column; the top-level row checkbox (e.g. 'C:').
    # (headed-verified; force-click the checker input)
    FILES_ROOT_CHECKBOX = ("//div[contains(@class,'x-grid-cell-inner')][contains(normalize-space(.),'C:')]"
                           "/preceding-sibling::*//input | //td[contains(@class,'x-grid-cell')]//input[@role='checkbox']")

    # ---- step 3 Options: 'Recovery type' combo — EXACT option labels VERIFIED live 2026-07-07 ----
    RECOVERY_TYPE_LABEL = ci_exact("Recovery type")
    # the four recovery types (combo options):
    RT_ORIGINAL = ci_exact("Recovery to original location")        # ⚠ OVERWRITES SOURCE — safety-gated (default)
    RT_CUSTOM_CIFS_NFS = ci_exact("Recover to custom location (CIFS/NFS)")   # export to a share
    RT_DOWNLOAD = ci_exact("Download")
    RT_FORWARD_EMAIL = ci_exact("Forward via email")
    # 'Recovery to original location' reveals an 'Overwrite behavior' combo — the 3 options are
    # VERIFIED live 2026-07-07 (exact labels):
    OVERWRITE_BEHAVIOR_LABEL = ci_exact("Overwrite behavior")
    OVERWRITE_RENAME = ci_exact("Rename recovered item if such item exists")      # default
    OVERWRITE_SKIP = ci_exact("Skip recovered item if such item exists")
    OVERWRITE_OVERWRITE = ci_exact("Overwrite the original item if such item exists")
    # the final action button on Options is 'Recover' (NOT 'Next'). ⚠ never auto-click for original-location.
    RECOVER_ACTION = "//span[contains(@class,'x-btn-inner') and normalize-space()='Recover']"
    # 'Recover to custom location (CIFS/NFS)' reveals: Share type / Path to the share / Overwrite behavior
    SHARE_TYPE_LABEL = ci_exact("Share type:")
    PATH_TO_SHARE_LABEL = ci_exact("Path to the share:")
