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

    # 'Run' toolbar button, shown once a job row is selected. RE-CALIBRATED live 2026-07-19: the
    # real @title on this control is the STATIC combined tooltip 'Run/Stop' (one toggle-style
    # element serves both actions; only its inner visible label span actually reads 'Run' vs
    # 'Stop', not the title) — an exact @title='Run' match matches NOTHING, which had been
    # silently misdiagnosed as appliance/video-recording flakiness for a long time (the failure
    # only ever surfaces as a Playwright timeout, identical in shape to genuine dashboard-lag
    # flakiness elsewhere in this file, until the actual DOM is inspected directly). contains()
    # matches either title text a build might show without needing to know which is current.
    RUN_BUTTON = "//*[contains(@title,'Run')]"
    # 'Edit' toolbar button — reopens the job's build wizard in EDIT mode (same 6-step wizard
    # used to create it; URL becomes /c/jobEditor?action=EDIT&...). CALIBRATED live 2026-07-16
    # for NJM-70312 (need a SECOND, genuinely different recovery point for the SAME job without
    # any host-side content seeding — see FlbWizardPage.save()/save_and_run() and
    # test_flbv2v3_FLRFunctional/_helpers.py's edit_flb_job_and_rerun()). Same title-attribute
    # pattern as RUN_BUTTON/MANAGE_BUTTON/STOP_BUTTON.
    EDIT_BUTTON = "//*[@title='Edit']"
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
    # RE-CALIBRATED live 2026-07-19: same 'Run/Stop' combined-title finding as RUN_BUTTON above —
    # contains() is robust to either the standalone 'Stop' title (if it exists in some job state)
    # or the combined 'Run/Stop' one.
    STOP_BUTTON = "//*[contains(@title,'Stop')]"
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
    # RE-CALIBRATED live 2026-07-19: the 'Delete this job?' dialog only shows a bare Cancel/
    # Delete pair when the job has NO recovery points yet (never run). Once the job has actually
    # produced a backup, the SAME dialog additionally renders a 'Delete scope:' radio pair —
    # 'Delete the job and keep the backups' (the DEFAULT, pre-selected radio) / 'Delete the job
    # and the backups' — missed entirely by an earlier probe that tested against a never-run job.
    # This default is why routine test cleanup (JobManagementPage.delete_job(), used by every
    # suite's flb_job_cleanup fixture) had been silently leaving every backup behind on the
    # target repository for the whole life of this project — a real, now-fixed gap; see
    # delete_job()'s own docstring. The RPC-based standalone browser/checks/cleanup_auto_flb_jobs.py
    # was NOT affected — its keepPhysicalItems=False default already matches this radio's intent.
    DELETE_SCOPE_JOB_AND_BACKUPS = ci_exact("Delete the job and the backups")

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
    CANCEL = ci_exact("Cancel")
    FINISH = "//span[contains(@class,'x-btn-inner') and normalize-space()='Finish']"
    FINISH_RUN = "//span[contains(@class,'x-btn-inner') and normalize-space()='Finish & Run']"
    # EDIT-mode equivalents of Finish/Finish & Run — CALIBRATED live 2026-07-16: reopening an
    # EXISTING job via DataProtectionLocators.EDIT_BUTTON shows 'Save'/'Save & Run' in the same
    # footer position instead of 'Finish'/'Finish & Run' (Cancel is unchanged).
    SAVE = "//span[contains(@class,'x-btn-inner') and normalize-space()='Save']"
    SAVE_RUN = "//span[contains(@class,'x-btn-inner') and normalize-space()='Save & Run']"
    # step headers
    STEP_SOURCE = ci_exact("1. Source")
    STEP_OPTIONS = ci_exact("6. Options")
    SELECT_AT_LEAST_ONE = ci_contains("Select at least one item")
    # 'Close the wizard? All changes will be lost.' confirm — CALIBRATED live 2026-07-08 on the
    # Backup Copy wizard: Cancel pops this confirm once anything on the wizard was touched
    # (a source ticked, a repo picked, a field typed). Best-effort click-through in
    # WizardPage.click_cancel() — wizards/paths that don't trigger it just find nothing to click.
    CLOSE_CONFIRM = "//span[contains(@class,'x-btn-inner') and normalize-space()='Close']"


class FlbWizardLocators(WizardLocators):
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


class SelectItemsLocators:
    """The per-machine 'Select Items' modal (browse the source filesystem, tick folders/files).

    Structure CALIBRATED live 2026-07-18 against nbr-84 / machine 'Window11' (dialog opened from
    the FLB Source step's edit pencil; cancelled without building a job). The dialog is a
    div.x-window.selectFolderDialog containing, top to bottom: a search field
    (div.inventorySearchBar), an address/breadcrumb bar (div.addressBar), a list header
    (div.listHeader: a single 'select all' globalCheckbox + Name/Modified Date/Modified Time
    column captions), the scrollable listing of div.folderInfoItem rows, and a bottom toolbar
    (Cancel / Apply). ExtJS keeps hidden DUPLICATE copies of this window in the DOM (a fresh copy
    each time the picker is reopened), so tests must scope reads to the VISIBLE dialog
    (FlbWizardPage's picker_* readers do this via .locator('visible=true')).
    """
    # --- dialog container + title — CALIBRATED live 2026-07-18 ---
    DIALOG = "//div[contains(@class,'x-window') and contains(@class,'selectFolderDialog')]"
    TITLE = DIALOG + "//span[contains(@class,'x-window-header-text')]"   # reads 'Select Items'

    # RE-CALIBRATED live 2026-07-18: these MUST be scoped to DIALOG. An earlier, unscoped version
    # (bare '//span[...=\"Cancel\"]') genuinely matched TWO visible elements at once — the dialog's
    # own Cancel span AND the outer wizard's unrelated Cancel button (both share the identical
    # ExtJS x-btn-inner/text markup) — so `.locator('visible=true').first.click()` could silently
    # click the WRONG one and leave the dialog open. This went undetected because the only two
    # call sites that clicked it either wrapped the click in a try/except that swallowed any
    # resulting failure (check_select_items_dialog.py's cleanup) or never asserted the dialog
    # actually closed afterward — caught live 2026-07-18 by a new test that DID assert closure and
    # failed reproducibly on a healthy appliance (test_dialog_apply_cancel.py::test_cancel_button).
    APPLY = DIALOG + "//span[contains(@class,'x-btn-inner') and normalize-space()='Apply']"
    CANCEL = DIALOG + "//span[contains(@class,'x-btn-inner') and normalize-space()='Cancel']"

    # footer reads 'Selected for Physical Machine: N' (FLB) or 'Selected for File Share: N' (FSB).
    # CALIBRATED live 2026-07-18: this count is rendered INSIDE the dialog, in the same
    # div.container that hosts the Show/Hide toggle (see SELECTED_ITEMS_TOGGLE below) — sits right
    # above the folder listing once at least one item is selected. Observed to read exactly
    # 'Selected for Physical Machine: 200' after a Select-all in a 200-item folder, confirming the
    # 200-item cap.
    FOOTER_COUNT = ("//div[contains(@class,'textComment1') and "
                    "contains(normalize-space(.),'Selected for')]")

    # --- Selected Items expansion panel — RE-CALIBRATED live 2026-07-18 (corrects an earlier
    # same-day pass that wrongly concluded no such panel exists here, having probed for the FLR
    # wizard's differently-named 'flrSelectedItemsTitle' class instead of this dialog's own
    # markup). The 'Show'/'Hide' toggle (a simple-link sibling of FOOTER_COUNT, text swaps
    # Show<->Hide) expands a real ExtJS grid (div.fileLevelFolderSelectionGridView) with Name/Path
    # columns — one row per currently-selected item, each showing its full breadcrumb path (e.g.
    # 'C: > TestData_ForFLB') and a per-row delete icon (div.flrDelBtn) to deselect directly from
    # the expanded list.
    SELECTED_ITEMS_TOGGLE = (DIALOG + "//a[contains(@class,'simple-link') and "
                              "(normalize-space()='Show' or normalize-space()='Hide')]")
    SELECTED_ITEMS_GRID = DIALOG + "//div[contains(@class,'fileLevelFolderSelectionGridView')]"
    SELECTED_ITEMS_ROWS = SELECTED_ITEMS_GRID + "//tr[contains(@class,'x-grid-row')]"

    @staticmethod
    def selected_items_row_delete(name: str) -> str:
        """The per-row delete icon (div.flrDelBtn) inside the expanded Selected Items grid, for
        the row whose Name-column cell reads `name` — used to deselect directly from the expanded
        list rather than re-navigating to the source row."""
        return (SelectItemsLocators.SELECTED_ITEMS_GRID +
                f"//tr[contains(@class,'x-grid-row')][.//span[@title='{name}']]"
                "//div[contains(@class,'flrDelBtn')]")

    # --- '>200 results' banner — CALIBRATED live 2026-07-18: a folder/volume listing with more
    # than 200 entries shows this message ABOVE the listing (not a dialog on its own); exact text
    # matches the TC spec (NJM-122673/122645) verbatim: 'Showing the first 200 results. Try using
    # Search to narrow your results.' Note the dialog's search box does NOT filter the listing in
    # this build (see picker_search()'s docstring), so the message's own suggestion to 'use
    # Search to narrow your results' cannot itself be exercised — a real, reportable product gap,
    # distinct from the (real, working) banner text/visibility itself.
    OVER_200_MESSAGE = DIALOG + "//div[contains(@class,'hmText') and contains(., 'Showing the first 200 results')]"

    # --- Apply/Cancel button containers (for enabled/disabled state reads) — CALIBRATED live
    # 2026-07-18: the clickable target is the inner x-btn-inner span (APPLY/CANCEL above); the
    # disabled STATE lives on the outer div.x-btn (adds 'x-btn-disabled'). Observed: at open with
    # nothing selected, Apply carried NO 'x-btn-disabled' class (i.e. Apply is enabled from the
    # start in this build — the 'select at least one item' gate is enforced by the Source step, not
    # by disabling the dialog's Apply). ---
    APPLY_BUTTON = DIALOG + "//div[contains(@class,'x-btn') and @title='Apply']"
    CANCEL_BUTTON = DIALOG + "//div[contains(@class,'x-btn') and @title='Cancel']"

    # --- list-header 'Select all' checkbox — CALIBRATED live 2026-07-18 ---
    # The one checkbox in div.listHeader (div.globalCheckbox). Ticking it selects rows from the TOP
    # of the current listing and STOPS at the 200-item cap (verified: a 200-folder dir yielded
    # exactly 200 checked). Same non-native-input caveat as every ExtJS checkbox — force-click.
    SELECT_ALL = "//div[contains(@class,'globalCheckbox')]//input[@role='checkbox']"

    # --- search box + clear control — CALIBRATED live 2026-07-18 ---
    # Input (placeholder 'Search') in div.inventorySearchBar; the clear/X is div.searchTrigger2
    # (display toggles none->block when text is present). IMPORTANT live finding: the search box
    # does NOT filter the folderInfoItem listing in THIS build — a matching term ('Folder1') and a
    # non-matching term ('zzzznomatchzzzz') both leave the full listing unchanged (verified via
    # per-keystroke typing + Enter). So the 'no matching items' empty-result message and the
    # '>200 results' search-limit warning are NOT reachable/observable here (documented gaps — do
    # NOT fabricate locators for them).
    SEARCH_INPUT = DIALOG + "//input[@placeholder='Search']"
    SEARCH_CLEAR = DIALOG + "//div[contains(@class,'searchTrigger2')]"

    # --- breadcrumb / address bar — CALIBRATED live 2026-07-18 ---
    # div.addressBar holds one div.addressBarBox per path segment: the ROOT segment is icon-only
    # (div.addressBarIcon.iconRoot24, no text); each named segment carries a
    # div.addressBarCell.addressBarText whose @title/text is the folder name; a div.addressBarNext
    # chevron separates segments. Clicking a segment navigates to it. Deep-path truncation was NOT
    # observed 3 levels deep (C: / TestData_ForFLB / Subfolder_200Folders all render in full) —
    # reproducing the overflow/ellipsis behaviour would need a far deeper path (documented gap).
    BREADCRUMB_BAR = DIALOG + "//div[contains(@class,'addressBar')]"
    BREADCRUMB_ROOT = BREADCRUMB_BAR + "//div[contains(@class,'iconRoot24')]"

    @staticmethod
    def breadcrumb_segment(name: str) -> str:
        """A named, clickable crumb segment (its addressBarText cell) by folder name."""
        return (SelectItemsLocators.BREADCRUMB_BAR +
                f"//div[contains(@class,'addressBarText') and @title='{name}']")

    # --- Up One Level — CALIBRATED live 2026-07-18 ---
    # There is NO dedicated toolbar 'up' button. Up navigation is a synthetic listing row whose
    # name is '[..]' (a folderInfoItem with a permanently-disabled checkbox) — it is the FIRST row
    # in every NON-root view and is ABSENT at the volume-root view. Click its name link to go up
    # (picker_up_one_level() / picker_drill('[..]') both do this via the existing drill()).
    UP_ONE_LEVEL_ROW = ("//div[contains(@class,'folderInfoItem')]"
                        "[.//div[contains(@class,'folderInfoItemName') and @title='[..]']]")

    # --- loading mask/spinner — CALIBRATED live 2026-07-18 ---
    # Folder contents load behind the standard ExtJS div.x-mask overlay (BasePage.wait_masks_gone()
    # already polls it); named here for tests that want to assert the mask appears while loading.
    LOADING_MASK = "//div[contains(@class,'x-mask')]"

    # --- disabled-row tooltips (system folder / 200-cap) — CALIBRATED live 2026-07-18 ---
    # A row that cannot be ticked renders its checkbox disabled (input[@disabled]; the field
    # div.folderInfoCheckbox gains 'x-item-disabled') AND swaps its name-link @title for the REASON
    # text (a hover tooltip in the same attribute the folder name normally occupies — so once
    # blocked a row can no longer be located by @title=<folder name>; match on the visible anchor
    # text via row_by_text() instead). Two reasons observed live:
    #   - system folders (Program Files, Program Files (x86), Windows): SYSTEM_FOLDER_TOOLTIP.
    #     Note: the truly-protected ones ($Recycle.Bin, System Volume Information) are NOT listed
    #     at all — only these three appeared, each disabled.
    #   - once 200 items are selected, EVERY other still-empty selectable row shows
    #     MAX_SELECTED_TOOLTIP (a folder that already CONTAINS checked descendants keeps class
    #     'has-checked-item' and stays enabled so you can still drill in / uncheck).
    SYSTEM_FOLDER_TOOLTIP = "System folder is not supported."
    MAX_SELECTED_TOOLTIP = "Maximum selected items were reached."

    @staticmethod
    def row(name: str) -> str:
        return (f"//div[contains(@class,'folderInfoItem')][.//div[contains(@class,'folderInfoItemName') "
                f"and @title='{name}']]")

    @staticmethod
    def row_by_text(name: str) -> str:
        """A row located by its VISIBLE name-link text (a.slText) rather than the @title attribute.
        CALIBRATED live 2026-07-18: use this (not row()) for a row that may be DISABLED — a
        disabled row's @title is the reason tooltip, not the folder name, so row()/drill()/
        checkbox() (all keyed on @title) miss it, but the anchor text still shows the folder name."""
        return (f"//div[contains(@class,'folderInfoItem')]"
                f"[.//a[contains(@class,'slText') and normalize-space()='{name}']]")

    @staticmethod
    def name_link_by_text(name: str) -> str:
        """The folderInfoItemName element (which carries the hover-tooltip @title) for a row found
        by its anchor text — read its @title to get the disabled-reason tooltip."""
        return (SelectItemsLocators.row_by_text(name) +
                "//div[contains(@class,'folderInfoItemName') and contains(@class,'slMain')]")

    @staticmethod
    def checkbox_by_text(name: str) -> str:
        return SelectItemsLocators.row_by_text(name) + "//input[@role='checkbox']"

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
    """Options step (step 6 of 6) — 'Job Options' / 'Full Backup Settings' / 'Pre and Post
    Actions' / 'Data Transfer' sections. Only JOB_NAME/ENCRYPTION_COMBO_INPUT had coverage before
    2026-07-19 — the ACL/App-aware/Full-Backup-Settings/concurrent-task-limit locators below were
    added then, CALIBRATED live against nbr-84 (suite D, NJM-182722).
    """
    # Job name text field: the input inside the x-field whose label is 'Job name:'
    JOB_NAME = ("//div[contains(@class,'x-field')][.//label[normalize-space()='Job name:']]"
                "//input[contains(@class,'x-form-text')]")

    # --- Backup encryption combo — CALIBRATED live 2026-07-08. Two options: 'Disabled'
    # (default) / 'Enabled'. Picking 'Enabled' reveals a 'settings' link (password config).
    ENCRYPTION_COMBO_INPUT = ("//label[normalize-space()='Backup encryption:']"
                              "/following-sibling::div[contains(@class,'x-form-item-body')][1]//input")

    # --- Encryption password dialog ('Set a password') — CALIBRATED live 2026-07-22, resolving
    # the NJM-123510 gap noted above. Clicking the 'settings' link (revealed when Backup
    # encryption is Enabled) opens a modal with two radios: 'Select password:' (pick an existing
    # saved password, default-selected) and 'Create password:' (reveals Password/Repeat
    # the password/Description fields). Two real, DOM-verified gotchas (a live outerHTML dump
    # via page.evaluate() was needed to find these — see FlbWizardPage.set_encryption_password()):
    # (1) the 'Create password:' toggle is `<input type="button" role="radio">`, NOT
    # `<input type="radio">` — a literal `input[type='radio']` search finds ZERO elements in this
    # dialog (an earlier attempt concluded from that there was no real radio input at all; there
    # is one, it just isn't a real radio-typed input). It's also rendered off-screen (bounding
    # box x≈-9491 — the visible circle is drawn by CSS on a sibling), so Playwright's
    # coordinate-based click (plain or force=True) always fails with "element is outside of the
    # viewport"; only a real DOM `.click()` via Locator.evaluate("el => el.click()") reliably
    # flips it (confirmed 3/3 live attempts). (2) the dialog's 'Description:' textarea is a
    # REQUIRED field for Create-password submission — leaving it empty puts a red validation
    # border on it and the submit click silently no-ops (dialog stays open); this ISN'T mentioned
    # anywhere in the visible label text. (3) the submit button's own LABEL changes dynamically
    # from 'Apply' to 'Proceed' (styled red) once both password fields are filled — this appliance
    # shows a "Key Management Service is disabled" warning and uses the relabel to flag that the
    # user must explicitly acknowledge it, so a locator hardcoded to only 'Apply' silently never
    # matches once a password is entered. Once (1) and (2) are both handled, the submit button
    # itself takes a normal `.click()` — no force/dispatch_event needed.
    ENCRYPTION_SETTINGS_LINK = "//*[normalize-space(text())='settings']"
    ENCRYPTION_CREATE_PASSWORD_RADIO = (
        "//label[normalize-space()='Create password:']/preceding-sibling::input[@role='radio'][1]"
    )
    ENCRYPTION_PASSWORD_INPUTS = "//input[@type='password']"
    ENCRYPTION_DESCRIPTION_TEXTAREA = "//textarea[@name='description']"
    ENCRYPTION_DIALOG_SUBMIT = ("//span[contains(@class,'x-btn-inner') and "
                                "(normalize-space()='Apply' or normalize-space()='Proceed')]")

    # --- KMS-disabled confirmation dialog on Finish — CALIBRATED live 2026-07-22. A SEPARATE
    # modal from the 'Set a password' dialog above: with a password configured but the Key
    # Management Service disabled, clicking the wizard's own Finish/Finish & Run button pops a
    # second confirmation ("Key Management Service is Disabled" — "If you lose the password you
    # entered, it will be impossible to decrypt your data...") that must be explicitly dismissed
    # via its own Proceed button. Without this, the wizard's page-covering mask never clears and
    # the job is NEVER actually created (confirmed live: 120s of polling never cleared the mask,
    # and the job was absent from the sidebar afterward) — this looks exactly like a backend hang
    # but is really just an un-dismissed confirmation dialog.
    KMS_DISABLED_DIALOG_TITLE = "//*[normalize-space()='Key Management Service is Disabled']"
    KMS_DISABLED_DIALOG_PROCEED = ("//*[normalize-space()='Key Management Service is Disabled']"
                                   "/ancestor::div[contains(@class,'x-window')][1]"
                                   "//span[contains(@class,'x-btn-inner') and normalize-space()='Proceed']")

    @staticmethod
    def encryption_option(label: str) -> str:
        return f"//li[normalize-space()='{label}']"

    @staticmethod
    def combo_option(label: str) -> str:
        """Generic dropdown-option <li> locator — same markup encryption_option() above already
        uses (identical ExtJS x-boundlist-item structure across every simple combo on this step:
        ACL, App-aware mode, Full backup mode, Create full backup frequency, the day-of-week/
        day-of-month secondary combos). Kept as a separate, more generically-named alias rather
        than renaming encryption_option() (an existing, already-used call site)."""
        return f"//li[normalize-space()='{label}']"

    # --- Access Control List combo — CALIBRATED live 2026-07-19. Two options verified via the
    # real dropdown: 'Back up only folder permissions' (default) / 'Back up folder and file
    # permissions'. This input carries NO stable name attribute (ExtJS assigns only an
    # auto-generated 'ext-gen*' id, unlike FULL_BACKUP_MODE_COMBO_INPUT/
    # CREATE_FULL_BACKUP_FREQUENCY_COMBO_INPUT below, which do) — same label+following-sibling
    # pattern as ENCRYPTION_COMBO_INPUT is the only reliable way to target it. Maps to
    # options.accessControlList in the JobDto (flb_job.template.json default:
    # 'FOLDER_PERMISSIONS' — the enum value for 'Back up folder and file permissions' was not
    # independently confirmed via RPC on this appliance, formatVersion 1 has no entities
    # catalogue to cross-check against; a reasonable inferred name is
    # 'FOLDER_AND_FILE_PERMISSIONS' but treat that as unconfirmed).
    ACL_COMBO_INPUT = ("//label[normalize-space()='Access Control List:']"
                       "/following-sibling::div[contains(@class,'x-form-item-body')][1]//input")

    # --- App-aware mode combo — CALIBRATED live 2026-07-19. Three options verified: 'Enabled
    # (proceed on error)' / 'Enabled (fail on error)' / 'Disabled' (default). Same no-stable-name
    # caveat as ACL_COMBO_INPUT above. Maps to options.applicationAwareMode ('NONE' default per
    # the template; the two 'Enabled' UI labels' exact enum spellings are unconfirmed for the
    # same formatVersion-1 reason).
    APP_AWARE_COMBO_INPUT = ("//label[normalize-space()='App-aware mode:']"
                            "/following-sibling::div[contains(@class,'x-form-item-body')][1]//input")

    # Picking EITHER 'Enabled' option pops an 'Application-Aware Mode' credentials dialog
    # (div.agent-mode-popup — VMs/Credentials tabs, one row per source machine needing a
    # credential assigned) — CALIBRATED live 2026-07-19. Configuring a real per-machine
    # credential is out of scope for this pass (no app-aware-capable fixture VM/credential is
    # documented in test-data/environment.md); FlbWizardPage.set_app_aware_mode() dismisses this
    # via its own Cancel button (best-effort — leaves the App-aware mode combo's value set,
    # just without any credential configured, matching 'proceed on error''s tolerant intent).
    APP_AWARE_CREDENTIALS_DIALOG = "//div[contains(@class,'agent-mode-popup')]"
    APP_AWARE_CREDENTIALS_CANCEL = (APP_AWARE_CREDENTIALS_DIALOG +
                                    "//span[contains(@class,'x-btn-inner') and normalize-space()='Cancel']")

    # --- Full Backup Settings section — CALIBRATED live 2026-07-19. Unlike ACL/App-aware above,
    # these DO carry stable `name` attributes matching the JobDto fields verbatim (cross-checked
    # against flb_job.template.json: fullBackupMode, fullBackupRunSettingsType,
    # fullBackupEveryJobRuns, fullBackupDayOfWeek, fullBackupDayOfMonth) — prefer name-based
    # selectors here rather than the label+sibling pattern.
    FULL_BACKUP_MODE_COMBO_INPUT = "//input[@name='fullBackupMode']"   # 'Synthetic full' (default) / 'Active full'

    # 'Create full backup:' frequency combo — 10 options verified via the real dropdown: Always /
    # Every / Every 2nd / First / Second / Third / Fourth / Last / Day # / Job runs # (default,
    # paired with a numeric field defaulting to 5).
    #
    # ⚠ IMPORTANT GATING FINDING (live 2026-07-19): every option EXCEPT 'Always' and 'Job runs #'
    # renders DISABLED (its <li>'s inner div carries an extra 'disabled' class and clicking it is
    # a silent no-op — the combo's displayed value simply never changes, no exception, no visual
    # feedback) whenever the Schedule step is left on 'Do not schedule, run on demand'
    # (FlbWizardPage.set_run_on_demand()). They become selectable the moment the job instead has
    # a real recurring schedule (verified live: leaving the Schedule step's own default recurring
    # config untouched enabled Every/Every 2nd/First/Second/Third/Fourth/Last/Job runs # all at
    # once) — EXCEPT 'Day #', which stayed disabled even then; it most likely additionally
    # requires the Schedule step's own recurrence to be specifically Monthly (not exercised — the
    # Schedule step's Daily/Weekly/Monthly recurrence-type selector has no POM coverage yet, out
    # of scope for this pass). This cost significant live-debugging time before being traced to
    # the disabled-option class rather than a locator/click-timing bug — see
    # FlbWizardPage.set_full_backup_frequency()'s docstring for the caller-facing consequence.
    CREATE_FULL_BACKUP_FREQUENCY_COMBO_INPUT = "//input[@name='runSettingsType']"

    # Secondary fields revealed by specific frequency choices — ALL of these already exist in the
    # DOM at all times (each just carries display:none until its owning frequency is the current
    # selection), which is how their `name` attributes could be read out even while genuinely
    # disabled/hidden during calibration.
    #  - 'Job runs #' reveals this numeric spinner (JobDto fullBackupEveryJobRuns, default 5).
    #    CONFIRMED 'Every'/'Every 2nd' do NOT reveal it — those two are fixed, non-configurable
    #    presets ('every job run' / 'every 2nd job run'), not editable-N variants of it.
    FULL_BACKUP_EVERY_JOB_RUNS_INPUT = "//input[@name='everyJobRuns']"
    #  - 'First'/'Second'/'Third'/'Fourth'/'Last' (Nth-weekday-of-month patterns) reveal this
    #    Monday..Sunday combo (JobDto fullBackupDayOfWeek). Options CONFIRMED live: ['Monday',
    #    'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].
    FULL_BACKUP_DAY_OF_WEEK_COMBO_INPUT = "//input[@name='everyDayOfWeek']"
    #  - 'Day #' (a specific day-of-month) reveals this combo (JobDto fullBackupDayOfMonth),
    #    labelled 'of the month'. Its own option list (1..31 / 'Last day', presumably) was NOT
    #    enumerated — 'Day #' stayed disabled throughout this calibration pass (see the frequency
    #    combo's own docstring above), so its dropdown was never actually opened. Open question.
    FULL_BACKUP_DAY_OF_MONTH_COMBO_INPUT = "//input[@name='everyDayOfMonth']"

    # --- Data Transfer section: concurrent-task-limit field — CALIBRATED live 2026-07-19.
    # Stable name attr, matches JobDto's foldersPerConcurrentTask verbatim (template default: 1).
    # Unlike its sibling 'Limit transporter load to' spinner (gated by its own checkbox, left
    # uncalibrated — out of scope here), this field has NO gating checkbox — always enabled.
    CONCURRENT_TASK_LIMIT_INPUT = "//input[@name='foldersPerConcurrentTask']"


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
    RUN = "//span[contains(@class,'x-btn-inner') and normalize-space()='Run']"
    CANCEL = "//span[contains(@class,'x-btn-inner') and normalize-space()='Cancel']"
    # 'Backup type:' combo (Incremental/Full) — CALIBRATED live 2026-07-16: only rendered when
    # the job already has a prior recovery point (i.e. a RE-run, never on a job's very first
    # run). A real <label> (unlike e.g. DestinationLocators' combo, whose caption is a plain
    # div) — same following-sibling pattern as OptionsLocators.ENCRYPTION_COMBO_INPUT.
    BACKUP_TYPE_COMBO_INPUT = ("//label[normalize-space()='Backup type:']"
                               "/following-sibling::div[contains(@class,'simple-combo-body')][1]//input")


class FileShareBackupLocators(WizardLocators):
    """No FSB-specific overrides currently defined — FileShareBackupPage.LOC points here as a
    semantic tag distinguishing FSB from FLB, inheriting all shared wizard locators as-is."""


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
    # step headers — Backup Copy has its OWN 4-step numbering, distinct from WizardLocators'
    # FLB-shaped STEP_SOURCE..STEP_OPTIONS ("6. Options" etc. would never match here)
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
    # step 2 shows this mask text while the recovery point mounts — wait for it to clear
    PREPARING = ci_contains("Recovery point is being prepared")
    # once mounted, step 2 gates the footer until a file/folder is ticked (prompt shown meanwhile)
    FILES_PROMPT = ci_contains("Please select at least one file or folder")

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
    TEST_CONNECTION_BUTTON = ci_exact("Test Connection")

    # ---- step 1 Backup: job/machine tree (LEFT panel, 'View: Jobs & Groups') — CALIBRATED
    # live 2026-07-16 for NJM-70312 ----
    # The job is a group node; each backed-up machine/share under it is an ordinary grid row
    # (same 'x-grid-row'/'x-grid-row-selected' convention as the Jobs sidebar — see
    # DataProtectionLocators.sidebar_job_row's docstring). Selecting a job via
    # recover_file_level() auto-expands it and auto-selects its (only, for this suite's jobs)
    # machine row — this locator lets a test independently CONFIRM that selection, which is
    # what proves the job/machine tree (LEFT) and the recovery-point picker (RIGHT, below) are
    # two separate, independently-operable widgets (TC NJM-70312 step 2's literal claim).
    @staticmethod
    def backup_step_machine_row(machine_name: str) -> str:
        return (f"//tr[contains(@class,'x-grid-row')]"
                f"[.//*[normalize-space(translate(.,'{_UP}','{_LO}'))='{machine_name.lower()}']]")

    # ---- step 2 Files: which recovery point is actually loaded ----
    # The Files-step LEFT tree's ROOT node label reads 'MACHINE (Day, DD Mon at H:MM pm)' —
    # CALIBRATED live 2026-07-16: this is the one place that confirms the Backup step's
    # recovery-point radio selection actually took effect (vs. a stale/cached tree — see
    # FileLevelRecoveryPage.select_recovery_point()'s docstring for a caveat). Broad
    # ci_contains-style match (ancestors match too, same as PREPARING/FILES_PROMPT elsewhere in
    # this class) — use .last.
    @staticmethod
    def files_step_root_label(machine_name: str) -> str:
        return ci_contains(f"{machine_name} (")

    # ---- step 1 Backup: recovery-point picker (RIGHT panel, Table view) — CALIBRATED live
    # 2026-07-16 against AUTO_FLB_NJM-70312_calib (2 runs of the same job, item SELECTION
    # changed between runs via Edit -> Save & Run rather than any host-side content edit — see
    # FlbWizardPage.save_and_run()/set_run_dialog_backup_type() and this suite's
    # edit_flb_job_and_rerun() helper) ----
    # Each row is a 'recoveryPointLiv' div containing a Date/Type/Status/Description grid PLUS
    # its own radio control — an <input type="button" role="radio" aria-checked="true|false">,
    # NOT a native checkbox/radio input, so read selection via aria-checked, not .checked.
    # DOM/display order is NEWEST FIRST (index 0 = latest, matching the wizard's own default
    # selection on entry).
    RECOVERY_POINT_ROW = "//div[contains(@class,'recoveryPointLiv')]"
    # relative to a row locator — 'xpath=' prefix required so Playwright doesn't try (and fail)
    # to parse a leading '.' as CSS (see select_root()'s '//td[...]' for the same convention).
    RECOVERY_POINT_DATE_TEXT = "xpath=.//span[contains(@class,'date__text')]"
    RECOVERY_POINT_RADIO = "xpath=.//input"
    # Jumps the radio selection straight to the newest recovery point (disabled/no-op when
    # already on it) — an alternative to clicking a specific row's radio, not exercised by
    # NJM-70312's own test (which needs a SPECIFIC, non-latest point) but documented here since
    # it's part of the same picker.
    LATEST_RECOVERY_POINT_BUTTON = ci_contains("Latest Recovery Point")

    # ---- step 2 Files: 'Selected for recovery: N' summary + expandable item list (NJM-70313)
    # CALIBRATED live 2026-07-16 against AUTO_FLB_DEBUG_70313 (built + cleaned up during
    # calibration): a small header reading 'Selected for recovery: N' sits above the file tree,
    # with 'Show'/'Hide' and 'Clear Selection' text links next to it. Clicking 'Show' expands a
    # panel below listing each selected item's Name/Path/Modified/Size (folders were observed
    # NOT to show a Size value — likely computed async/lazily, unlike files which show it
    # immediately — see FileLevelRecoveryPage.selected_items_panel_text()'s docstring). ----
    SELECTED_ITEMS_TITLE = "//*[contains(@class,'flrSelectedItemsTitle')]"
    SELECTED_ITEMS_SHOW_LINK = ci_exact("Show")
    # Nearest ancestor div whose text includes the 'Modified' column header — only true once the
    # item list is actually expanded (Show clicked) and rendered; scopes a readback to just the
    # popup rather than the whole page body.
    SELECTED_ITEMS_PANEL = (
        "//*[contains(@class,'flrSelectedItemsTitle')]/ancestor::div[contains(.,'Modified')][1]"
    )


class RepositoryManagementLocators:
    """Repository management UI — CALIBRATED live 2026-07-18 against nbr-84. No prior POM
    coverage existed for this area at all (per the task brief) — this is the first pass.

    Entry: left nav 'Settings' (gear icon, bottom of the main nav rail) -> Settings' own left
    sub-nav has 'Repositories' (under an 'Inventory' heading, alongside 'Nodes'/'Tape') ->
    a grid of repository rows (Repository Name / Details columns) -> click a row's name to open
    that repository's OWN detail page (URL becomes /c/configuration?...&targetId=<vid>...),
    which shows two info panels (space usage; self-healing/verification/detach settings) and a
    'Backups' grid of every backup stored there. The detail page's top-right toolbar has
    Refresh / Recover / a '...' overflow button (class 'more-horizontal-btn' — NOT text/title
    based, unlike DataProtectionLocators' title-attribute buttons; this button carries no title
    or visible text of its own) opening a popup with TWO sections:
      MANAGEMENT: Detach / Edit / Remove / Delete backups in bulk
      MAINTENANCE: Run repository self-healing / Reclaim unused space / Verify all backups /
                   Repair / Lock / Migrate backups

    IMPORTANT finding: MAINTENANCE's exact membership is REPO-TYPE- and STATE-gated:
      - 'Run repository self-healing' only rendered for LOCAL-type repos (verified live:
        present on Onboard repository/Local-Immutable, ABSENT on Amazon_Repo (S3) and
        Azure_Repo (Azure Blob) — cloud repos have no local filesystem to self-heal).
      - 'Reclaim unused space' is a REAL, separate action (NJM-85733's literal feature) — but
        it is rendered with `style="display:none"` and a disabled class + the tooltip title
        'No space can be reclaimed' whenever the repository currently has nothing reclaimable
        (verified live on both Onboard repository and Local-Immutable in their current state —
        neither has ever had a recovery point deleted, so there is nothing to reclaim yet).
        Because it is hidden (not merely disabled-but-visible), a bare
        `.locator("visible=true")` query on it correctly reports 0 matches when reclaim isn't
        available — RepositoryManagementPage.reclaim_available() relies on exactly this.
      - 'Repair' can ALSO appear a second, hidden/disabled time with title 'The action is not
        enabled.' — same visible-filter pattern handles it.
      - 'Lock' / 'Migrate backups' are present but permanently disabled+hidden on this
        appliance with the tooltip 'This functionality is not available in the current
        license...' (a licensing gate, not a capability gap) — out of scope for NJM-85730/
        NJM-85733, documented here for completeness only.
      - 'Verify all backups' was seen enabled on every repo type tried (Onboard, Local-
        Immutable, Amazon_Repo, Azure_Repo).

    All MANAGEMENT/MAINTENANCE menu items are `<a class="... popupLink ...">` — the SAME
    element renders twice in the DOM for some entries (an enabled, visible copy AND a disabled,
    display:none copy with a reason tooltip) — always scope to `.locator("visible=true")`,
    mirroring the exact lesson already documented on SelectItemsLocators/ScheduleLocators
    elsewhere in this file (don't repeat the unscoped-duplicate mistake).

    'Run repository self-healing' pops a 'Repository self-healing' confirm dialog (native
    <button>Start</button> / <button>Cancel</button> — NOT an ExtJS x-btn-inner span, same
    native-button convention as DataProtectionLocators.STOP_CONFIRM_BUTTON/
    DELETE_CONFIRM_BUTTON) warning the process can be time-consuming and blocks new jobs while
    running. Clicking Start immediately shows a 'Backup repository self-healing: "<repo>"'
    entry in the global Activities panel (left-nav 'Activities', badge-counted) with a live %
    progress, moving to Past Activities as 'Completed' once done — CONFIRMED live: a 1-backup/
    160MB Local-Immutable repo went from 0% to 'Completed' in under 10 seconds. This Activities
    panel (not the repo detail page itself) is the one reliable place to read real
    start/finish state for ANY of these maintenance actions — the repo detail page itself does
    not show a persistent in-page progress indicator.

    'Repair' pops its own dialog ('Repair Repository') with three checkboxes (Overwrite
    repository metadata / Overwrite backup objects / Verify backup objects) plus a warning that
    leaving all three unchecked still overwrites corrupted metadata — native
    <button>Repair</button>/<button>Cancel</button>. NOT triggered destructively during this
    calibration pass (opened then cancelled) — a real run is left to the NJM-85730 test itself.
    """
    SETTINGS_NAV = ci_exact("Settings")
    REPOSITORIES_SUBNAV = "//div[contains(@class,'tabSwitchLink') and normalize-space()='Repositories']"

    # drilldown pages (repo detail, backup detail) replace the Repositories subnav tabs with a
    # breadcrumb + '<' back button (stable 'backBtn' class) -- use this to go up one level
    # instead of re-clicking SETTINGS_NAV/REPOSITORIES_SUBNAV, which do nothing useful once
    # already two levels deep (CALIBRATED live 2026-07-20, NJM-68621).
    BACK_BUTTON = "//div[contains(@class,'backBtn')]"

    @staticmethod
    def repo_row(repo_name: str) -> str:
        """A repository's row in the Repositories grid, scoped to the (title-bearing) grid-cell
        div rather than the ambiguous <td>/<div class='x-grid-cell-inner'> ancestors that also
        carry the same visible text (verified live: 3 raw matches per row, this is the one with
        a clean, unique @title)."""
        return f"//div[contains(@class,'grid-cell') and @title='{repo_name}']"

    # repo detail page toolbar
    OVERFLOW_MENU_BUTTON = "//div[contains(@class,'more-horizontal-btn')]"

    @staticmethod
    def menu_item(label: str) -> str:
        """A Management/Maintenance popup menu item by its exact visible label — scope to
        `.locator("visible=true")` at the call site (see class docstring: some labels render a
        second, hidden/disabled copy)."""
        return f"//a[contains(@class,'popupLink') and normalize-space()='{label}']"

    DETACH = menu_item.__func__("Detach")
    EDIT = menu_item.__func__("Edit")
    REMOVE = menu_item.__func__("Remove")
    DELETE_BACKUPS_IN_BULK = menu_item.__func__("Delete backups in bulk")
    RUN_SELF_HEALING = menu_item.__func__("Run repository self-healing")
    RECLAIM_UNUSED_SPACE = menu_item.__func__("Reclaim unused space")
    VERIFY_ALL_BACKUPS = menu_item.__func__("Verify all backups")
    REPAIR = menu_item.__func__("Repair")

    # confirm dialogs — native <button>, not ExtJS x-btn-inner spans (CALIBRATED live 2026-07-18)
    SELF_HEALING_START_BUTTON = "//button[normalize-space()='Start']"
    SELF_HEALING_CANCEL_BUTTON = "//button[normalize-space()='Cancel']"
    REPAIR_CONFIRM_BUTTON = "//button[normalize-space()='Repair']"
    REPAIR_CANCEL_BUTTON = "//button[normalize-space()='Cancel']"

    # backup row (within a repo's own 'Backups' grid) by machine/share name
    @staticmethod
    def backup_row_link(name: str) -> str:
        return f"//a[normalize-space()='{name}']"

    @staticmethod
    def backup_row_link_by_job(job_name: str) -> str:
        """A backup's own Name-column link, scoped to the grid row whose Job-column value
        equals `job_name` exactly — the safe alternative to backup_row_link(name) when
        multiple backups share the same displayed machine/share name.

        CALIBRATED live 2026-07-20 (NJM-68621): backup_row_link(name) alone is AMBIGUOUS on
        this appliance — Onboard repository has ~7 backup rows all displaying the machine name
        'Window11', one per distinct FLB job that has ever targeted it (see this repo's own
        Backups grid 'Job' column: FLB_WinSource, FLB_Win11, FLB_1item, ...,
        AUTO_FLB_NJM-68621_rerun-after-rp-delete). backup_row_link('Window11') resolves to
        whichever of these happens to be FIRST in DOM order — not necessarily the one the
        caller actually wants — and opened the WRONG backup's recovery points during this
        calibration pass before this fix.

        Each grid row is a `<tr class="x-grid-row">` containing a Name-cell
        `<a class="linkInText">` (own @title = machine/share name) followed later in document
        order by a Job-cell `<a class="linkInText">` (own @title = job name) — filter the row
        by the Job cell's @title (unique per job name — NBR job names must be unique), then
        take the FIRST linkInText anchor in that row (the Name cell, which renders before the
        Job cell)."""
        return (f"//tr[contains(@class,'x-grid-row') and "
                f".//div[contains(@class,'grid-cell') and @title='{job_name}']]"
                f"//a[contains(@class,'linkInText')][1]")

    # ---- a backup's own detail page ('Recovery points' list) ----
    # CALIBRATED live 2026-07-20 (NJM-68621). Layout: an info panel (Name/Type/Points/Last
    # point/Size/Job name) above a 'Recovery points' grid. The grid has its OWN select-all
    # checkbox (stable id, unlike the generic gridCb class used elsewhere) and its own local
    # toolbar overflow — but that local overflow (scoped via RECOVERY_POINTS_LOCAL_OVERFLOW)
    # only ever offered 'Provide password' (grayed out on a non-encrypted backup) during this
    # calibration pass; it is NOT a delete affordance. The grid has no per-row action icon at
    # all (unlike the repo's own Backups grid, which has one per row).
    #
    # The page's own TOP-RIGHT '...' (next to 'Recover' — the SAME OVERFLOW_MENU_BUTTON
    # locator/class used on the repo detail page, confirmed live to resolve correctly here via
    # `.locator("visible=true").first` since the recovery-points-local overflow, though present
    # in the DOM, sits later in document order) opens a DIFFERENT, backup-scoped menu:
    # Verify / Repair / Delete. This 'Delete' operates on the WHOLE backup object, not on
    # whichever recovery points are checked in the grid — selecting 1-of-2 or 2-of-2 recovery
    # points and clicking it produced the IDENTICAL 'Cannot delete the backup' dialog either
    # way. NBR blocks this outright while any job still references the backup:
    #   "Cannot delete the backup. This backup is used by the following item(s): <job name>"
    # (native ExtJS x-window with a single native <button title="OK">, not an x-btn-inner span).
    #
    # A repository-wide 'Delete backups in bulk' action also exists (MANAGEMENT menu on the
    # REPOSITORY's own overflow, DELETE_BACKUPS_IN_BULK above) — CONFIRMED LIVE it has NO
    # per-backup/per-job picker at all. Its 'Bulk Delete Backups' dialog only offers global
    # age/criteria radio options (All backups not belonging to any job [+ older than N days] /
    # All recovery points older than N days / All legacy recovery points not belonging to any
    # job and older than N days / All corrupted recovery points / All missing recovery points)
    # — every option acts across the WHOLE repository's matching backups, with no way to scope
    # to a single job's backup entry. Deliberately NOT used by RepositoryManagementPage for
    # per-job recovery-point deletion — doing so would risk touching every other backup in the
    # repository, well outside the AUTO_FLB_*/AUTO_FSB_* safety fence.
    RECOVERY_POINTS_SELECT_ALL_CHECKBOX = "//input[@id='masterSavepointCheckboxId']"
    RECOVERY_POINTS_LOCAL_OVERFLOW = (
        "//*[starts-with(@id,'recoveryPointsTableView')]//div[contains(@class,'more-horizontal-btn')]"
    )
    VERIFY_THIS_BACKUP = menu_item.__func__("Verify")
    DELETE_THIS_BACKUP = menu_item.__func__("Delete")
    CANNOT_DELETE_BACKUP_OK_BUTTON = "//button[@title='OK']"

    # global Activities panel (left nav) — the reliable place to observe maintenance-action
    # progress/completion (see class docstring)
    ACTIVITIES_NAV = ci_exact("Activities")

    @staticmethod
    def activity_row_text(needle: str) -> str:
        """Loose contains-match on the Activities panel body for a substring (e.g. a repo name
        or 'self-healing') — callers read the surrounding text themselves (no fixed DOM
        structure was calibrated for individual activity rows; the panel is read as flat text,
        same pragmatic approach used elsewhere for coarse activity-log checks)."""
        return ci_contains(needle)


class GlobalSearchLocators:
    """Global Search feature ('/c/globalsearch') — CALIBRATED live 2026-07-21 against nbr-84
    (NJM-70399/70402/70385, suite L of NJM-182729). No prior POM coverage existed for this area.

    Entry: left sidebar 'Search' nav item (NAV_SEARCH), same nav level as Overview/Data
    Protection/Monitoring/Activities/Calendar/Settings — opens '/c/globalsearch'. Layout: a left
    'Display:' panel with an Infrastructure/Files toggle (Infrastructure is the default and the
    only mode calibrated here — Files switches to a content-search-inside-backups mode not
    needed by NJM-70399/70402/70385, left uncalibrated, an open question for a future pass) plus
    12 category checkboxes (Recovery points / Backups / Replicas / Jobs & Groups / Protected
    Items / Unprotected Items / Backup Repositories / Transporters / VM agents / Physical Machine
    Agents / Tape cartridges / Tape devices) that filter the results grid on the right.

    The top-right search field starts COLLAPSED behind a plain icon (div.searchButton, inside
    div.searchControl — see SEARCH_TOGGLE_ICON's own docstring for a real, caught-live locator
    bug: the obvious-looking `div.searchIcon` class is a DIFFERENT, unrelated element) — click it
    once to reveal the real `<input placeholder="Search">` (also inside div.searchControl) before
    typing. CALIBRATED live: clicking the icon a SECOND time TOGGLES the field closed again (a
    show/hide toggle, not "reveal only") — callers must check visibility first rather than
    always clicking (see GlobalSearchPage._ensure_search_field_open()).

    Each result row is a real ExtJS grid row (tr.x-grid-row, 3 cells): a per-row checkbox
    (input.gridCb — used only by the BULK '...' toolbar actions, see below) in cell 1, the
    item's own name as a real anchor (a.linkInText) in cell 2, and a plain-text Category label
    in cell 3 (last cell). Item NAMES are frequently non-unique (e.g. 11 different backups can
    all display as 'Window11', one per job that ever targeted that machine — same ambiguity
    RepositoryManagementLocators.backup_row_link_by_job()'s docstring already documents) —
    result_row() accepts an optional `category` filter to disambiguate, and callers needing a
    SPECIFIC one of several same-named/same-category rows should pass `nth`.

    CLICKING THE NAME LINK (not the checkbox) opens a small popover (div.gsPopupGroupItems)
    grouped into headed sections — CONFIRMED LIVE for two categories:
      - Backups row: 'JOBS' (a link to the owning job) / 'GRANULAR RECOVERY' ('File level
        recovery') / 'ACTIONS' ('Backup copy' / 'Delete backup') / 'BACKUP INFO' (Repository /
        Rec. points / Last point, plain text).
      - Jobs & Groups row: 'ACTIONS' ('Run' / 'Open job dashboard') / 'JOB INFO' (Type /
        Contents / Status / Last run, plain text).
    Every actionable item inside the popover is the SAME real anchor class (a.simple-link) NBR
    uses for its other popup-menu links elsewhere in this app (see
    RepositoryManagementLocators.menu_item()'s identical `popupLink` convention) — this is the
    natural, TC-literal way to trigger a result row's action ("click a 'Run Job'/'Create Backup
    Copy Job'/'Recover' action button in the result row"), used here in preference to the row
    checkbox + bulk '...' toolbar menu (which ALSO exists — CONFIRMED LIVE to offer the SAME
    'Run / Stop'/'Backup copy'/'Delete backups' actions for a multi-selected batch — but that is
    a bulk-operation affordance, not what these TCs describe; not used by GlobalSearchPage).

    CONFIRMED LIVE (read-only exploration; every wizard opened this way was cancelled before
    Finish except where the calling check script explicitly authorizes completing it — see
    GlobalSearchPage's own docstring for the full per-action finding, including the two
    downstream wizards (Backup Copy / File Level Recovery) needing ZERO new locators of their
    own since both land pre-selected on their normal step 1, reusing BackupCopyPage/
    FileLevelRecoveryPage as-is).
    """
    NAV_SEARCH = ci_exact("Search")

    # Display: Infrastructure/Files toggle — only Infrastructure calibrated (see class docstring)
    DISPLAY_INFRASTRUCTURE = ci_exact("Infrastructure")
    DISPLAY_FILES = ci_exact("Files")

    # top-right search field — CALIBRATED live 2026-07-21 (2nd pass, via outerHTML dump, not
    # guessed): the collapsed state's clickable icon is NOT a `div.searchIcon` (that class is
    # the UNRELATED left-sidebar 'Search' nav icon — an earlier pass wrongly assumed they were
    # the same element and it silently clicked the sidebar icon instead, a real locator-scoping
    # bug caught only because the field never actually opened afterward). The genuine toggle is
    # `div.searchButton` INSIDE `div.searchControl` (`display:inline-block` while collapsed,
    # sitting right next to the real `<input>`, which carries `display:none` until expanded).
    SEARCH_TOGGLE_ICON = "//div[contains(@class,'searchControl')]//div[contains(@class,'searchButton')]"
    SEARCH_INPUT = "//div[contains(@class,'searchControl')]//input[@placeholder='Search']"

    # left 'Display:' filter panel — CALIBRATED live: 'Select all'/'Deselect all' is a single
    # toggle-style link whose own text reflects the OPPOSITE of the current all-or-nothing state
    # (reads 'Deselect all' once >=1 filter is checked — the default on a fresh page load, since
    # every filter starts checked — 'Select all' once none are).
    SELECT_ALL_FILTERS = ci_exact("Select all")
    DESELECT_ALL_FILTERS = ci_exact("Deselect all")

    @staticmethod
    def filter_checkbox(label: str) -> str:
        """A category filter's own checkbox (e.g. 'Backups' / 'Jobs & Groups') — CALIBRATED
        live: identical `label[...]/preceding-sibling::input[1]` pattern already used elsewhere
        in this file (ScheduleLocators.IMMUTABLE_FOR_CHECKBOX, InclusionExclusionLocators) —
        force-click, same non-native-checkbox-forwarding caveat as those."""
        return f"//label[normalize-space()='{label}']/preceding-sibling::input[1]"

    NO_MATCHING_ITEMS = ci_contains("No matching items found")

    # the results panel's own static heading — a safe, always-present, never-navigating click
    # target for dismissing an open row popover (see GlobalSearchPage.close_popup()'s docstring:
    # an earlier version clicked a raw top-left (10, 10) screen coordinate, which is unreliable —
    # on this page that corner sits over the collapsible left-nav rail, not empty canvas).
    RESULTS_HEADER = ci_exact("Search results")

    @staticmethod
    def result_row(item_name: str, category: str | None = None) -> str:
        """A result grid row (tr.x-grid-row) whose Item-name cell (a.linkInText) reads exactly
        `item_name`. Pass `category` to additionally scope to a specific Category-column value
        (e.g. 'Backups' / 'Jobs & Groups') — see class docstring for why this is often needed
        (same display name can appear once per category, or once per job on a Backups row)."""
        base = (f"//tr[contains(@class,'x-grid-row')]"
                f"[.//a[contains(@class,'linkInText') and normalize-space()='{item_name}']]")
        if category:
            base += f"[.//td[contains(@class,'x-grid-cell-last')][normalize-space()='{category}']]"
        return base

    @staticmethod
    def result_row_category_cell(item_name: str, category: str | None = None) -> str:
        return GlobalSearchLocators.result_row(item_name, category) + "//td[contains(@class,'x-grid-cell-last')]"

    @staticmethod
    def result_row_item_link(item_name: str, category: str | None = None) -> str:
        return GlobalSearchLocators.result_row(item_name, category) + "//a[contains(@class,'linkInText')]"

    @staticmethod
    def result_row_checkbox(item_name: str, category: str | None = None) -> str:
        return GlobalSearchLocators.result_row(item_name, category) + "//input[contains(@class,'gridCb')]"

    # per-row action popover (opened by clicking a result row's own item-name link). RE-CALIBRATED
    # live 2026-07-21: this XPath matches FOUR separate sibling divs at once — one per section
    # (JOBS / GRANULAR RECOVERY / ACTIONS / BACKUP INFO for a Backups row), NOT one container
    # nesting all four — each independently carries the `gsPopupGroupItems` class.
    POPUP = "//div[contains(@class,'gsPopupGroupItems')]"

    # a Backups-category popover's 'JOBS' section link (the owning job's name) — scoped to
    # SPECIFICALLY the section whose own header reads 'Jobs' (case-insensitive: the header's
    # REAL DOM text is title-case 'Jobs' — CSS `text-transform: uppercase` on its `.header2`
    # class is what renders it as 'JOBS' on screen, the same ExtJS CSS-uppercase gotcha this
    # whole file's ci_exact()/ci_contains() helpers exist for, confirmed live via outerHTML dump
    # (a raw `normalize-space()='JOBS'` predicate, without case-folding, matched ZERO elements)).
    # RE-CALIBRATED live 2026-07-21 (two findings, not guessed): (1) this popover is FOUR
    # separate sibling divs, not one container nesting four sections (see POPUP's own docstring);
    # (2) an earlier version searched `a.linkInText` unscoped across the WHOLE popup — broken for
    # any backup whose owning job had been deleted, where the Jobs section renders as plain text
    # ('There are no jobs for this backup.', no anchor) instead of a link, so an unscoped `.first`
    # fell through to the NEXT matching anchor instead — the Granular Recovery section's own
    # 'File level recovery' link, which (confirmed live via outerHTML) carries BOTH `simple-link`
    # AND `linkInText` classes, not just the former. This is a real, reproducible bug:
    # find_backup_row_by_job()'s iteration silently misread that unrelated link's text as the
    # "owning job name" for every orphaned/no-job backup row. Scoping to the Jobs-titled section
    # specifically makes an absent job link (count()==0) unambiguous and harmless instead.
    POPUP_JOB_LINK = (
        POPUP + f"[.//*[normalize-space(translate(.,'{_UP}','{_LO}'))='jobs']]"
        "//a[contains(@class,'linkInText')]"
    )

    @staticmethod
    def popup_action_link(label: str) -> str:
        """A clickable link inside the currently-open result popover, by its exact visible text
        (e.g. 'Run' / 'Backup copy' / 'File level recovery' / 'Delete backup' /
        'Open job dashboard') — CALIBRATED live: every one of these is an `a.simple-link`."""
        return GlobalSearchLocators.POPUP + f"//a[contains(@class,'simple-link') and normalize-space()='{label}']"

    # exact action labels, VERIFIED live (see class docstring for which category shows which)
    RUN_ACTION = "Run"
    OPEN_JOB_DASHBOARD_ACTION = "Open job dashboard"
    FILE_LEVEL_RECOVERY_ACTION = "File level recovery"
    BACKUP_COPY_ACTION = "Backup copy"
    DELETE_BACKUP_ACTION = "Delete backup"
