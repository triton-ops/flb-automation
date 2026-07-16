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

    # 'Run' toolbar button, shown once a job row is selected (title attribute is unique/stable,
    # same rationale as MANAGE_BUTTON below). CALIBRATED live 2026-07-15.
    RUN_BUTTON = "//*[@title='Run']"
    # The selected job's own 'Job Info' dashboard portlet — two status lines. CALIBRATED live
    # 2026-07-15 against nbr-84: line 1 alone is AMBIGUOUS (a job with no run in flight always
    # shows its schedule label, e.g. 'Runs on demand', whether it has never been run OR just
    # finished a successful run — both look identical on line 1). Line 2 is what disambiguates,
    # via its own sentence: 'This job has not been executed yet' / 'This job has not finished
    # yet. Schedule: ...' (running) / 'Last run was successful. Schedule: ...'. Prefer reading
    # the job's own dashboard (these two locators) over the shared 'Job overview' content grid
    # — the grid requires extra navigation that can silently land back on a previously-selected
    # job's detail view instead of the grid (a real bug hit live 2026-07-15).
    JOB_INFO_LINE1 = "(//div[contains(@class,'jvgiItem')])[1]"
    JOB_INFO_LINE2 = "(//div[contains(@class,'jvgiItem')])[2]"
    STOP_BUTTON = "//*[@title='Stop']"
    # 'Stop this job?' confirm dialog — unlike RunDialogLocators.RUN (an ExtJS x-btn-inner
    # span), this one is a genuine <button> element. CALIBRATED live 2026-07-15.
    STOP_CONFIRM_BUTTON = "//button[normalize-space()='Stop']"

    # --- job management (Manage -> Delete) — CALIBRATED live 2026-07-15 against nbr-84 ---
    # The toolbar button's title attribute is the unique, stable target: a bare text search
    # for 'Manage' also matches a second DOM node (the button's own inner text span), so scope
    # to the title-bearing element specifically.
    MANAGE_BUTTON = "//*[@title='Manage']"
    # The Manage dropdown's own menu items: Clone / Merge / Rename / Create Report / Disable /
    # Delete (red text, always last). A bare ci_exact/ci_contains("Delete") is UNSAFE here: the
    # job's own name can legitimately contain the substring 'delete' case-insensitively (e.g. an
    # AUTO_FLB_*_DELETE_ME calibration job name) and a contains-style match will hit that grid
    # cell text too — normalize-space() exact-string equality on 'Delete' alone (never true for
    # a longer job-name string) is what actually disambiguates it, not case-folding.
    DELETE_MENU_ITEM = "//a[contains(@class,'slText') and normalize-space()='Delete']"
    # 'Delete this job?' confirm dialog — native-looking button, not an ExtJS x-btn-inner span.
    DELETE_CONFIRM_BUTTON = "//button[normalize-space()='Delete']"
    DELETE_CANCEL_BUTTON = "//button[normalize-space()='Cancel']"

    @staticmethod
    def sidebar_job_row(name: str) -> str:
        """Scoped to the left 'Jobs' sidebar list only (class 'jobDashboardNavigator').
        CALIBRATED live 2026-07-08: a bare ci_exact(name) text search matches ~3 DOM nodes
        per visible row (TR/TD/nested DIV) PLUS duplicates in the wide job-overview grid
        (class 'jobDashboardContentView') and any page heading showing the same job name —
        16 raw matches observed for one non-unique job name. Scoping to one <tr> per
        sidebar row (and requiring the x-grid-row class) collapses that back to exactly one
        match per actual job, so nth() reliably disambiguates jobs that share NBR's generic
        default name (e.g. multiple never-custom-named 'File level backup job for physical
        machine' jobs)."""
        return (f"//div[contains(@class,'jobDashboardNavigator')]"
                f"//tr[contains(@class,'x-grid-row')]"
                f"[.//*[normalize-space(translate(.,'{_UP}','{_LO}'))='{name.lower()}']]")


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
    # 'Close the wizard? All changes will be lost.' confirm — CALIBRATED live 2026-07-08 on the
    # Backup Copy wizard: Cancel pops this confirm once anything on the wizard was touched
    # (a source ticked, a repo picked, a field typed). Best-effort click-through in
    # WizardPage.click_cancel() — wizards/paths that don't trigger it just find nothing to click.
    CLOSE_CONFIRM = "//span[contains(@class,'x-btn-inner') and normalize-space()='Close']"


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
    # text: 'No item(s) selected' or 'N item(s) selected'
    SELECTED_NOTE = "//div[contains(@class,'pessSelViewFooterNoteForItem')]"


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
    """CALIBRATED live 2026-07-08 against nbr-84. The label 'Do not schedule, run on demand'
    renders TWICE in the DOM: once as the real, interactive checkbox (inside a
    'schedule-item-line' container) and once as a permanently-DISABLED mirror (inside a
    'manual-schedule' container, used elsewhere as a read-only indicator). The OLD
    DO_NOT_SCHEDULE_ROW (ci_exact text match + click_visible) could resolve either one first —
    live testing 2026-07-08 showed it silently landing on the disabled duplicate: the click
    reported success but the checkbox never toggled and the recurring-schedule form stayed
    visible. `check_flb_wizard_smoke.py` never caught this because it doesn't assert on the
    resulting state, only that the click didn't throw. Use DO_NOT_SCHEDULE_CHECKBOX (scoped to
    schedule-item-line, force-clicked) instead — verified live to actually toggle the checkbox
    and collapse the form.
    """
    # kept only for reference; do not use it for clicking (see the docstring above)
    DO_NOT_SCHEDULE_ROW = ci_exact("Do not schedule, run on demand")
    DO_NOT_SCHEDULE_CHECKBOX = ("//div[contains(@class,'schedule-item-line')]"
                                "//label[normalize-space()='Do not schedule, run on demand']"
                                "/preceding-sibling::input[1]")
    DO_NOT_SCHEDULE = "//div[contains(@class,'manual-schedule')]//input[contains(@class,'x-form-checkbox')]"

    # --- Recurring schedule (Schedule #1) retention/immutability fields — only rendered when
    # NOT in "do not schedule, run on demand" mode. VERIFIED live 2026-07-08: these map straight
    # to the job-level options.retentionPolicy JobDto fields (name attrs match 1:1) —
    # customKeepSavepointCount/TypeCombo -> keepDayCount/keepWeekCount/etc (per the chosen unit),
    # keepImmutableCount -> options.retentionPolicy.keepImmutableCount.
    KEEP_BACKUPS_FOR_COUNT = "//input[@name='customKeepSavepointCount']"
    KEEP_BACKUPS_FOR_UNIT_COMBO = "//input[@name='customKeepSavepointTypeCombo']"
    IMMUTABLE_FOR_CHECKBOX = ("//label[contains(normalize-space(.),'Immutable for')]"
                              "/preceding-sibling::input[1]")
    IMMUTABLE_FOR_DAYS = "//input[@name='keepImmutableCount']"


class OptionsLocators:
    # Job name text field: the input inside the x-field whose label is 'Job name:'
    JOB_NAME = ("//div[contains(@class,'x-field')][.//label[normalize-space()='Job name:']]"
                "//input[contains(@class,'x-form-text')]")

    # --- Backup encryption combo — CALIBRATED live 2026-07-08. Two options: 'Disabled'
    # (default) / 'Enabled'. Picking 'Enabled' reveals a 'settings' link (password config —
    # not yet calibrated, see NJM-123510).
    ENCRYPTION_COMBO_INPUT = ("//label[normalize-space()='Backup encryption:']"
                              "/following-sibling::div[contains(@class,'x-form-item-body')][1]//input")

    @staticmethod
    def encryption_option(label: str) -> str:
        return f"//li[normalize-space()='{label}']"


class InclusionExclusionLocators:
    """The Inclusion (step 2) and Exclusion (step 3) steps — CALIBRATED live 2026-07-08.
    Structurally identical: an 'Include items'/'Exclude items' checkbox that reveals a textarea
    ('Type item names or paths to include/exclude. One item per line. Use * for any number of
    characters. Use ? for a single character.'). Maps to options.enabledSourceItemsInclusion/
    sourceItemsInclusion (and the Exclusion equivalents) in the JobDto. The checkbox's <label>
    does NOT forward clicks to its sibling input (it's `type="button"`, not a native checkbox) —
    force-click the input directly, same lesson as ScheduleLocators.DO_NOT_SCHEDULE_CHECKBOX.
    """
    INCLUDE_CHECKBOX = "//label[normalize-space()='Include items']/preceding-sibling::input[1]"
    EXCLUDE_CHECKBOX = "//label[normalize-space()='Exclude items']/preceding-sibling::input[1]"
    INCLUDE_TEXTAREA = ("//div[contains(@class,'text-area-field')]"
                        "[.//label[contains(normalize-space(.),'to include')]]//textarea")
    EXCLUDE_TEXTAREA = ("//div[contains(@class,'text-area-field')]"
                        "[.//label[contains(normalize-space(.),'to exclude')]]//textarea")


class RunDialogLocators:
    DIALOG = ("//div[contains(@class,'x-window')][.//*[contains(normalize-space(.),'Run this job?')]]")
    RUN = "//span[contains(@class,'x-btn-inner') and normalize-space()='Run']"


class FileShareBackupLocators(WizardLocators):
    TITLE = ci_contains("Backup Job Wizard for File Share")
    ALL_FILE_SHARES = ci_exact("All File shares")


class BackupCopyLocators(WizardLocators):
    """The 'Backup copy' job wizard — CALIBRATED live 2026-07-08 against nbr-84. FOUR steps
    (not FLB's six): 1. Backups -> 2. Destination -> 3. Schedule -> 4. Options.

    Step 1 ('Backups') is NOT a source-machine tree like FLB's Source step — it lists EXISTING
    backups as a treegrid grouped by job type (e.g. 'File level backup job for physical
    machine'), one leaf row per machine/share that has a backup. A leaf whose backup is
    currently unreadable is suffixed '(inaccessible)' and still renders a (non-functional)
    checkbox — pick an unsuffixed leaf (e.g. 'Linux_16.84', the linux-src FLB backup, i.e. the
    UI-visible name for BACKUP_OBJECT-8). The tree uses the IDENTICAL x-tree-expander /
    x-tree-checkbox DOM as FLB's source tree, so BackupCopyPage reuses
    FlbWizardLocators.tree_expander()/machine_checkbox() as-is instead of duplicating them here.

    Step 2 ('Destination') reuses DestinationLocators.COMBO/COMBO_TRIGGER/option() as-is (same
    'Select a target destination' combo/list). The step ALSO has its own 'Destination type:
    Disk/Tape' combo (own dropdown; same 'glT1' class as the repo combo but disambiguated by its
    'Disk'/'Tape' text vs. 'Select a target destination' — no locator collision). NOTE: Tape is
    NOT greyed out on this appliance as of 2026-07-08 (a VLT_Tape library + 'test1' media pool
    were added the same day, per environment.md) — this supersedes the 2026-07-08
    Claude-in-Chrome manual walk that found Tape disabled. Not calibrated further here: this POM
    targets Disk destinations only, matching the RPC-verified BC recipe (R4d).

    Step 3 ('Schedule') places BACKUP-COPY-ONLY retention-MODE radios above the SAME
    retention/immutability fields FLB renders under its 'Schedule #1' block — verified live to
    be the identical DOM (same field `name`s: `customKeepSavepointCount`,
    `customKeepSavepointTypeCombo`, `keepImmutableCount`), so ScheduleLocators'
    DO_NOT_SCHEDULE_CHECKBOX / KEEP_BACKUPS_FOR_COUNT / KEEP_BACKUPS_FOR_UNIT_COMBO /
    IMMUTABLE_FOR_CHECKBOX / IMMUTABLE_FOR_DAYS are reused UNCHANGED — do not duplicate them
    here. The retention-mode radios (Backup-Copy-only, no FLB equivalent):
      - 'Maintain exact copy of the source backup'
      - 'Keep <N> last recovery points' (the bare label text is just 'Keep' — the count spinner
        and 'last recovery points' trailer are separate sibling nodes)
      - 'Synchronize recovery points and apply custom retention' (DEFAULT-checked; this is the
        ONLY mode that reveals the 'Keep backups for' / 'Immutable for' fields — and, same as
        FLB, those fields disappear again if 'Do not schedule, run on demand' is ticked)
    All three are `type="button"` radios, same non-native-input caveat as every other ExtJS
    toggle in this app — force-click the input, never rely on the label to forward the click.

    Retention/immutability finding (live, 2026-07-08): 'Immutable for' is DISABLED when the
    step-2 destination repo has no Object Lock capability (verified against Cloudian, NFS_REPO,
    Onboard repository, Wasabi_Repo — all `objectLockSupported:false` per environment.md) and
    becomes ENABLED the moment an Object-Lock-capable repo is picked instead (verified against
    Cloudian-immutable — ticking it and typing a day count works). So the wizard's gate is real
    and repo-capability-driven, not a blanket-disabled dead control on this appliance — pick one
    of environment.md's `*_Immutable` repos to actually exercise it.

    Step 4 ('Options') reuses OptionsLocators.JOB_NAME as-is (same 'Job name:' x-field).

    TITLE corrects the old unverified 'Backup Copy Job Wizard' TODO guess — the real title is
    'New Backup Copy Job Wizard' (ci_contains still matches the old guess as a substring, so
    this is a strict superset fix, not a breaking rename).
    """
    TITLE = ci_contains("New Backup Copy Job Wizard")

    # step headers — Backup Copy has its OWN 4-step numbering, distinct from WizardLocators'
    # FLB-shaped STEP_SOURCE..STEP_OPTIONS ("6. Options" etc. would never match here)
    STEP_BACKUPS = ci_exact("1. Backups")
    STEP_DESTINATION = ci_exact("2. Destination")
    STEP_SCHEDULE = ci_exact("3. Schedule")
    STEP_OPTIONS = ci_exact("4. Options")

    # step 3: retention-mode radios (Backup-Copy-only — see class docstring)
    RETENTION_MODE_EXACT_COPY = ("//label[normalize-space()='Maintain exact copy of the source "
                                 "backup']/preceding-sibling::input[1]")
    RETENTION_MODE_KEEP_LAST = "//label[normalize-space()='Keep']/preceding-sibling::input[1]"
    RETENTION_MODE_SYNC_CUSTOM = ("//label[normalize-space()='Synchronize recovery points and "
                                  "apply custom retention']/preceding-sibling::input[1]")


class FileLevelRecoveryLocators:
    """File-Level Recovery flow — CALIBRATED live 2026-07-06 on nbr-84 (FLB); FSB entry point
    on nbr-5 CALIBRATED live 2026-07-08.

    Entry: select a job -> 'Recover' -> a GRANULAR RECOVERY submenu item. The menu label
    depends on the job's TYPE, not something inferable from job_name — FLB jobs (PHYSICAL)
    show 'File level recovery' (MENU_FILE_LEVEL); FSB jobs (NAS) show a DIFFERENTLY-WORDED
    'File share recovery' (MENU_FILE_SHARE) instead, opening a 'File Share Recovery Wizard'.
    Confirmed live on nbr-5: the RPC layer (FileLevelRecoveryManagement.createSession) needs
    hvType:"NAS" (not "PHYSICAL") for an FSB backup object — see recipes/file-backup-recipes.md
    R7. Once open, both wizards share the SAME FOUR-step flow and DOM (Files-step mount/gate,
    Options recovery-type combo, etc. — see FileLevelRecoveryPage.recover_file_share()'s
    docstring for the one real UI difference: step 1's picker is a calendar/table recovery-point
    view for FSB instead of FLB's flat backup-name list).
    1. Backup (pick backup + recovery point) -> 2. Files (WAITS for the recovery point to MOUNT,
    then browse/select) -> 3. Options (Recovery type: Download / Recover to original location /
    Export to CIFS|NFS share) -> 4. Finish.
    """
    RECOVER_BUTTON = ci_exact("Recover")                 # top action after selecting a job (VERIFIED)
    MENU_FILE_LEVEL = ci_exact("File level recovery")    # Recover -> GRANULAR RECOVERY submenu, FLB (VERIFIED)
    MENU_FILE_SHARE = ci_exact("File share recovery")    # Recover -> GRANULAR RECOVERY submenu, FSB (VERIFIED)
    # step headers (VERIFIED)
    STEP_BACKUP = ci_exact("1. Backup")
    STEP_FILES = ci_exact("2. Files")
    STEP_OPTIONS = ci_exact("3. Options")
    STEP_FINISH = ci_exact("4. Finish")
    # step 2 shows this mask text while the recovery point mounts — wait for it to clear
    PREPARING = ci_contains("Recovery point is being prepared")
    # once mounted, step 2 gates the footer until a file/folder is ticked (prompt shown meanwhile)
    FILES_PROMPT = ci_contains("Please select at least one file or folder")
    # Files right-pane is an ExtJS grid split into a locked check-column panel + the tree/name
    # panel (separate DOM subtrees, NOT the same <tr> — a row's checkbox is not inside the same
    # row element as its name). The check-column renders a real <input type="checkbox" class="gridCb">
    # inside a <td class="...tristatecheckcolumn...">, but WITHOUT role="checkbox" — a locator
    # relying on that ARIA role won't match. The original locator also hardcoded a Windows 'C:'
    # drive-letter text match, which never matches a Linux-sourced backup's tree (root node is
    # just named 'root'). RE-CALIBRATED 2026-07-08 against a Linux-sourced FLB backup — targets
    # the first checkbox input in the locked check-column panel (the top-level/root row), works
    # regardless of source OS. (headed-verified; force-click the checker input)
    FILES_ROOT_CHECKBOX = "//td[contains(@class,'checkcolumn')]//input[contains(@class,'gridCb')]"

    # ---- step 2 Files: browse-only folder listing (RE-CALIBRATED live 2026-07-15 against
    # nbr-84) ----
    # The Files step actually has TWO separate grids side by side: a LEFT navigation tree
    # (machine -> volumes -> folders, 'treecolumn' cells) and a RIGHT flat listing of whatever
    # node is currently selected on the left (columns in order: checkbox, Name, Modified, Size —
    # all in the SAME <tr>, unlike the older locked-panel/tree-panel split noted on
    # FILES_ROOT_CHECKBOX above, which no longer applies to this listing view in the current
    # build). Expanding a left-tree node (clicking its 'x-tree-expander' icon — note: that class
    # lives on an <img>, not a <div>) only reveals its children in the tree; the row itself must
    # also be clicked to SELECT it and refresh the right-hand listing.
    @staticmethod
    def left_tree_row(name: str) -> str:
        """A row in the Files step's LEFT navigation tree whose visible text contains `name`
        (e.g. 'C:', 'TestData_ForFLB'). Scoped to rows with a 'treecolumn' cell so it can't
        collide with the RIGHT listing's identically-named row (both trees can show a folder
        called 'C:')."""
        return (f"//tr[contains(@class,'x-grid-row')][.//td[contains(@class,'treecolumn')]]"
                f"[contains(normalize-space(.),'{name}')]")

    # RE-CALIBRATED live 2026-07-16: a bare FOLDER row in the right-hand listing carries the
    # 'flrGridContainer' class (e.g. class="x-grid-row  flrGridContainer"), but a FILE row does
    # NOT (e.g. class="x-grid-row  x-grid-row-over") — matching on 'flrGridContainer' alone
    # silently misses every file, only ever finding subfolders. Both row kinds share a
    # 'tristatecheckcolumn' checkbox cell as their first column (the left tree's rows never
    # have one), which is the reliable, kind-agnostic signal.
    RIGHT_PANEL_ROW = "//tr[contains(@class,'x-grid-row')][.//td[contains(@class,'tristatecheckcolumn')]]"

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
