# browser/ — UI-validation checks (Playwright POM + vision)

For TCs whose assertions are **UI state** (button enable/disable, selection counts/labels, step
transitions) that the RPC layer can't see. Drives the Director web UI with Playwright, screenshots
the decision point, and the **vision step (Claude reads the PNG)** renders the verdict.

## The NBR UI is ExtJS — use XPath, not get_by_text
- Text is rendered in **nested wrappers** and often **CSS-uppercased** (`text-transform`), so
  Playwright `get_by_text` and raw-cased `text()='LOG IN'` are unreliable.
- Locators are **XPath, case-insensitive, on the element's full string value** — see
  `locators.py` helpers `ci_exact()` / `ci_contains()`:
  `//*[normalize-space(translate(.,'A..Z','a..z'))='label']`.
  `ci_exact('Backup copy')` matches the menu item but NOT the `BACKUP COPY JOB` header (exact).
- Icon-only controls (no text) → target a **stable class**, e.g. the Create `+` is
  `//*[contains(@class,'create-btn')]`. **Avoid pixel coordinates** — a license-expiry banner
  shifts the layout ~50px and breaks them.

## Layout
```
browser/
  config/
    ui_config.json    # SECRETS: url, user, password — gitignored; copy from ui_config.example.json
    ui_config_fsb.json # SECRETS for nbr-5 (FSB) — gitignored; copy from ui_config_fsb.example.json
    ui_values.json    # reusable UI-check DATA: machine names, folders, labels, per-TC expectations
  nbr_ui.py           # standalone helper: --calibrate / screenshot a view
  pom/
    base/             # foundational primitives — no locators of their own
      base_page.py    # ALL Playwright actions (click/fill/wait/query/screenshot) — single place
      driver.py       # config/values loaders + browser_page() factory (ignore self-signed cert)
      retry.py        # retry_on_transient() — wraps only genuinely transient steps (browser launch)
    common/           # shared across every backup job type
      locators.py     # ALL selectors (XPath, ci_exact/ci_contains) — single place to maintain
      login_page.py
      data_protection_page.py   # nav + open_create_menu (create-btn) + start_* wizards + Recover
      wizard_page.py            # shared job-wizard base: next_enabled/needs_selection_hint/click_next/cancel
    backup_types/     # one page object per specific backup job type/flow
      flb_wizard_page.py        # File-Level Backup
      file_share_page.py        # Backup for file share (extends FlbWizardPage)
      backup_copy_page.py       # Backup copy
      file_level_recovery_page.py  # FLR via Recover (needs a backup job present)
  checks/             # one runnable check per TC/flow; navigates via POM, screenshots, prints signals
                      # (currently empty — see git history for prior check scripts if reviving one)
  ../results/screenshots/<TC>/   # PNG evidence per check
```

## Maintenance points
- **Selector changed?** → `pom/common/locators.py` only.
- **Interaction changed?** → `pom/base/base_page.py` only.
- **New screen/flow?** → add a page object under `pom/backup_types/` (or `pom/common/` if shared) + a locator group.

## Run a check
```
cd browser
python checks/<script>.py            # any check script under checks/
# add --headed to watch
```
Then read the screenshots under `../results/screenshots/<TC>/` for the verdict.

## Coverage status (RE-CALIBRATED 2026-07-06 on nbr-84 / NBR 11.2.1)
The 11.2.1 FLB wizard changed to **6 steps** (Source / Inclusion / Exclusion / Destination /
Schedule / Options); item selection is on the **Source** step via a per-machine **Select Items**
dialog (tick folders and/or individual files). ExtJS keeps every step in the DOM at once → use
`base_page.click_visible()` for step controls; tree checkboxes + the hover-revealed edit pencil
need `click_force` / `reveal_and_click`.

| Area | Entry | Status |
|---|---|---|
| Login | — | ✅ verified (11.2.1) |
| FLB job wizard — full drive | Create → File level backup… | ✅ **calibrated end-to-end** (`check_flb_wizard_smoke.py` ALL PASS: machine → Select Items folder+file → Inclusion/Exclusion → Destination → Schedule → Options → Cancel) |
| FLB UI-state assertion | Source step | ✅ **NJM-122652 PASS** (cannot proceed without an item selected) |
| Select Items dialog | Source step | ✅ drill + folder/file tick + Apply (`SelectItemsLocators`) |
| File Share backup wizard (nbr-5) | Create → Backup for file share | ✅ **calibrated** (`check_fsb_wizard_smoke.py` ALL PASS: share → whole-share select → Inclusion/Exclusion → Destination → Schedule → Options → Cancel). Uses `config/ui_config_fsb.json`. Granular per-file pick inside a share is drivable but flaky behind an ExtJS load mask → prefer whole-share. |
| File Level Recovery (nbr-84) | select job → Recover → File level recovery | ✅ **calibrated headed 2026-07-07, re-verified + fixed headless 2026-07-08** — entry, 4-step nav (Backup/Files/Options/Finish), RP mount, file select, and step-3 **Recovery type** options: `Recovery to original location` (default; ⚠ overwrites source → reveals **Overwrite behavior** = *Rename* / *Skip* / *Overwrite the original item if such item exists*), `Recover to custom location (CIFS/NFS)`, `Download`, `Forward via email`. Final action is **Recover** — POM deliberately never auto-executes original-location (safety-gated). `check_flr_flow.py` ALL PASS after 3 fixes: (1) its job target `FLB_NFS_REPO` no longer exists — jobs are now selected via `DataProtectionLocators.sidebar_job_row()` (scoped to the left Jobs list) + an `nth` index, since NBR's generic default job name collides across multiple never-custom-named jobs; (2) the mount-detection locator `FileLevelRecoveryLocators.PREPARING` is a `ci_contains()` match that resolves ~11 ancestor duplicates whose count never reaches 0 — `wait_files_ready()`/`files_ready()` now check the LAST (most specific) match instead of count/`.first`; (3) the Files-step selection gate ('Please select at least one file or folder') is no longer shown proactively on mount — it's now REACTIVE, only appearing after an attempted Next click with nothing selected (`files_awaiting_selection()` performs that harmless attempt itself). |
| Backup Copy wizard | Create → Backup copy | ✅ **calibrated end-to-end 2026-07-08** (`check_backup_copy_wizard_smoke.py` ALL PASS: existing-backup tree (job-type groups expanded by row state, not by glyph class — see `BackupCopyPage.expand_all_backup_groups`) → Destination repo pick → Schedule retention-mode radio + the repo-capability-gated **'Immutable for'** checkbox (disabled on non-Object-Lock repos, enabled + settable on `*_Immutable`/`*-immutable` ones, verified against `Cloudian-immutable`) → Options job name → Cancel + the wizard's 'Close the wizard?' confirm). Repo list now also includes `Amazon_Immutable`/`Azure_Immutable`/`BlackBlaze_Immutable`/`Wasabi-immutable`/`Local-Immutable` (Object-Lock capable) alongside the plain repos in `environment.md`. |
```
