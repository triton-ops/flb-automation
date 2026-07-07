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
    locators.py       # ALL selectors (XPath, ci_exact/ci_contains) — single place to maintain
    base_page.py      # ALL Playwright actions (click/fill/wait/query/screenshot) — single place
    driver.py         # config/values loaders + browser_page() factory (ignore self-signed cert)
    login_page.py
    data_protection_page.py   # nav + open_create_menu (create-btn) + start_* wizards + Recover
    wizard_page.py            # shared job-wizard base: next_enabled/needs_selection_hint/click_next/cancel
    flb_wizard_page.py        # File-Level Backup
    file_share_page.py        # Backup for file share
    backup_copy_page.py       # Backup copy
    file_level_recovery_page.py  # FLR via Recover (needs a backup job present)
  checks/
    check_njm_122652.py # one runnable check per TC; navigates via POM, screenshots, prints signals
  ../results/screenshots/<TC>/   # PNG evidence per check
```

## Maintenance points
- **Selector changed?** → `locators.py` only.
- **Interaction changed?** → `base_page.py` only.
- **New screen/flow?** → add a page object + a locator group.

## Run a check
```
cd browser
python checks/check_njm_122652.py            # UI-state assertion (headless)
python checks/check_flb_wizard_smoke.py      # full FLB wizard drive, cancels (creates nothing)
# add --headed to watch either run
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
| File Level Recovery (nbr-84) | select job → Recover → File level recovery | ✅ **calibrated headed 2026-07-07** — entry, 4-step nav (Backup/Files/Options/Finish), RP mount, file select, and step-3 **Recovery type** options: `Recovery to original location` (default; ⚠ overwrites source → reveals **Overwrite behavior** = *Rename* / *Skip* / *Overwrite the original item if such item exists*), `Recover to custom location (CIFS/NFS)`, `Download`, `Forward via email`. Final action is **Recover** — POM deliberately never auto-executes original-location (safety-gated). |
| Backup Copy wizard | Create → Backup copy | ⏳ n/a — no BC on current appliances |
```
