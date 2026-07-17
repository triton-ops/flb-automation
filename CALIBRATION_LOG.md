# Calibration log

An **index**, not a duplicate — every row below points at a real `CALIBRATED live`/`VERIFIED
live` comment already in the code, which remains the source of truth for the full explanation.
This file exists to answer "what's flaky/surprising and why, and where" without grepping the
whole tree — see `docs/framework-guide.md`'s Common Mistakes section for the handful of these
that were costly enough to also get a prose write-up there.

**Keeping this current**: when you add a new `CALIBRATED live YYYY-MM-DD` comment, add one row
here too (date, area, one line, file:line). Don't copy the explanation — link to it. If a
calibration is later superseded (the UI changed again), update or remove its row rather than
stacking a new one on top of a stale one.

## 2026-07-06

| Area | Finding | Ref |
|---|---|---|
| FLR wizard | Full 4-step File-Level Recovery flow calibrated (Backup/Files/Options/Finish) | `file_level_recovery_page.py:1` |
| FLB wizard | Full 6-step build flow calibrated | `flb_wizard_page.py:3` |
| FSB wizard | Structurally identical to FLB, calibrated against nbr-5 | `file_share_page.py:3` |
| FLR locators | Locator set for the FLR flow on nbr-84 | `locators.py:332` |

## 2026-07-07

| Area | Finding | Ref |
|---|---|---|
| FLR Options step | Exact 'Recovery type' combo option label text verified | `locators.py:388,396` |

## 2026-07-08

| Area | Finding | Ref |
|---|---|---|
| Schedule step | 'Do not schedule, run on demand' label renders TWICE (real checkbox + disabled mirror); the old `DO_NOT_SCHEDULE_ROW` locator ambiguously resolves to the disabled one — use `DO_NOT_SCHEDULE_CHECKBOX` instead, kept as a documented warning | `locators.py:188` |
| Backup Copy wizard | 4-step flow (not FLB's 6) calibrated | `backup_copy_page.py:3` |
| Backup Copy | 'Immutable for &lt;days&gt;' control behavior | `backup_copy_page.py:136` |
| Inclusion/Exclusion steps | Locator set calibrated | `locators.py:235` |
| Backup encryption combo | Two options ('Disabled'/...) | `locators.py:223` |
| Wizard cancel | 'Close the wizard? All changes will be lost.' confirm appears once anything was touched (Backup Copy) | `locators.py:122`, `wizard_page.py:57` |
| FSB recovery | 'File Share Recovery Wizard' entry point calibrated on nbr-5 | `file_share_recovery_page.py:1` |
| FLR cancel | `click_cancel()` must handle BOTH the FLB flow (closes on 1 click) and FSB's 'Close the wizard?' confirm whose OWN button is also labeled 'Cancel' | `file_level_recovery_page.py:393` |
| FLR mount wait | `L.PREPARING`'s `ci_contains()` match tests every ancestor node — check `.last`, not `.first` | `file_level_recovery_page.py:160` |
| Wizard step title | Active step tab carries `tabSwitchLinkActive`; other visited steps only carry the weaker `slActive` | `wizard_page.py:26` |
| FSB FLR check | FSB's distinctly-worded FLR equivalent | `check_flr_file_share.py:6` |
| Job selection | A bare `ci_exact(name)` text search matches ~3 DOM nodes — scope to the sidebar | `locators.py:88` |

## 2026-07-15

| Area | Finding | Ref |
|---|---|---|
| Wizard open/cancel cycling | Running many open/cancel cycles back-to-back has a side effect | `data_protection_page.py:23` |
| `run_job()` | Baseline calibration against nbr-84 | `data_protection_page.py:87` |
| Job dashboard status | Line 1 (`JOB_INFO_LINE1`) is AMBIGUOUS — read line 2 instead | `data_protection_page.py:151` |
| `get_job_status()` idempotency | Check current status before acting | `data_protection_page.py:134` |
| `delete_job()` | A job stopped mid-transfer showed 'Running' in the grid well past when it should have | `job_management_page.py:45` |
| Job management locators | `MANAGE_BUTTON`, Job Info dashboard portlet's two status lines, a genuine `&lt;button&gt;` element, Manage→Delete section | `locators.py:45,48,54,67,70` |
| Inclusion/Exclusion validation | The ONLY reliable validation signal for these steps | `flb_wizard_page.py:174` |
| Files-step listing | RE-CALIBRATED browse-only folder listing | `locators.py:361` |
| IncludeExclude spec gaps | No enforced 5000-char textarea cap; no visible red-highlight/message for a rejected entry | `test_njm_185014.py`, `test_njm_185015.py`, `test_njm_185016.py` |

## 2026-07-16 (the big day — FLR wizard + CIFS credential debugging)

| Area | Finding | Ref |
|---|---|---|
| **CIFS credentials (the costly one)** | **`.fill()` sets the raw DOM value but never updates some ExtJS widgets' internal component state — a 'Test Connection' call read an empty password despite the DOM showing the typed value. Fixed via real per-character keystroke simulation (`fill_reliable()`).** | `file_level_recovery_page.py:483`, promoted to `base_page.py:65` — see `docs/framework-guide.md`'s Common Mistakes |
| Recovery-point order | DOM/display order is newest-first (index 0 = latest) | `file_level_recovery_page.py:69` |
| RP picker + machine tree | Two separate findings for NJM-70312 (independence of job-tree vs. RP-picker selection) | `file_level_recovery_page.py:89` |
| Files-step tree refresh | Confirmed switching RP updates the Files-step header/tree | `file_level_recovery_page.py:116` |
| RP picker Table view | A row renders partially outside the visible viewport | `file_level_recovery_page.py:127` |
| RP label | Timestamp text confirms which recovery point is actually loaded | `file_level_recovery_page.py:147` |
| Files-step gate | `FILES_ROOT_CHECKBOX` is stale, no longer applies to the current listing view | `file_level_recovery_page.py:179` |
| Tree drill | Clicking a tree row refreshes the right-hand listing | `file_level_recovery_page.py:211` |
| Selected-items panel | Opening the panel doesn't tick any checkbox / doesn't affect selection | `file_level_recovery_page.py:264` |
| RP freshness | A savepoint that just finished is the common case needing special handling | `file_level_recovery_page.py:270` |
| Item selection matching | Use membership-test (`name in text`), not exact match | `file_level_recovery_page.py:326` |
| Finish step close | Step 4 (Finish) has a 'Close' button, not 'Cancel' — executing a recovery leaves the wizard here | `file_level_recovery_page.py:367` — see Golden Rule 8 / Common Mistakes (the 14-job leak) |
| Files-step selection gate | Gates progression until ≥1 file/folder ticked | `file_level_recovery_page.py:417` |
| CIFS share type field | 'Share type:' doesn't render as a `&lt;label&gt;` element | `file_level_recovery_page.py:455` |
| CIFS path field | 'Path to the share:' also isn't a `&lt;label&gt;` | `file_level_recovery_page.py:477` |
| Recover button gate | Stays DISABLED until 'Test Connection' succeeds | `file_level_recovery_page.py:515` |
| Test Connection click | Clicking via `.first` needed a second calibration pass | `file_level_recovery_page.py:522` |
| Locator scoping | Both selection steps scoped to VISIBLE matches only (NJM-70312) | `base_page.py:125` |
| Backup/Incremental combo | Only rendered under a specific prior condition | `flb_wizard_page.py:302` |
| Same-job re-run | Re-running the SAME job immediately after a prior run completed can leave the Run control un-re-enabled well past the 10s default | `data_protection_page.py:89` |
| 'Run this job?' confirm | Its own Run button also timed out at the 10s default — 3 consecutive real pytest runs failed here, an isolated diagnostic didn't (recording overhead + appliance load) | `data_protection_page.py:97` |
| Finish/Finish & Run | Maps to `WizardLocators.SAVE`/`SAVE_RUN` | `data_protection_page.py:117` |
| Job re-edit | EDIT-mode equivalents when reopening an existing job | `locators.py:113` |
| Backup type combo | Only rendered under a specific condition | `locators.py:254` |
| Backup step confirmation | The ONE place that confirms the Backup step's job/RP state | `locators.py:424` |
| RP picker Table view | Locator set calibrated | `locators.py:433` |
| Folder row rendering | RE-CALIBRATED — a bare folder row in the right-hand listing carries a specific attribute | `locators.py:380` |
| NJM-182426 (historical) | UI-driven re-run PASSES — the old "empty FLR listing" product-defect finding was actually a POM locator bug (`RIGHT_PANEL_ROW` only matched folder rows) | `test_njm_182426.py:7` |
| Inclusion filter browsing | Browsing INTO a folder matched by an active Inclusion filter has specific behavior | `test_njm_182424.py:7` |
| Linux FLR tree path | The FLR Files-step left tree does NOT mirror the wizard's drill path | `test_flbv2v3_IncludeExclude/_helpers.py:42` |
| **Linux FLR tree root node** | **A Linux source's FLR left tree top-level node is `"root"`, not the wizard drill path — hit independently 7 times across the Inventory suite** | `test_njm_67702.py`, `test_njm_67806_67809_linux_os_matrix.py`, `test_njm_67813.py`, `test_njm_67816.py`, `test_njm_67817.py`, `test_njm_68933.py`, `test_njm_68934.py` |
| Select Items dialog | Display labels for a specific item confirmed | `test_njm_68916.py:18` |
| Download recovery type | Always wraps its output in a zip, even for a single file | `_lib/_shared_helpers.py:139` |
| FLRFunctional RP building | Calibration jobs built and fully cleaned up during calibration | `test_njm_70312.py:18`, `test_njm_70313.py:11` |
| `run_on_demand=False` | An on-demand job's Schedule step has NO retention field at all | `test_flbv2v3_FLRFunctional/_helpers.py:70` |
| Second genuinely-different RP | How this suite gets a second real recovery point for one job (NJM-70312) | `test_flbv2v3_FLRFunctional/_helpers.py:125` |
| Backup type for 2nd RP | `backup_type='Incremental'`, NOT `'Full'`, is required | `test_flbv2v3_FLRFunctional/_helpers.py:131` |

## 2026-07-17

| Area | Finding | Ref |
|---|---|---|
| `framework_doctor.py` canary | Must capture results BEFORE dismissing the popup being checked, not after | `framework_doctor.py:287` |
| `health_check.py` nav icons | Left nav's own icon containers, specific matching pattern | `health_check.py:177` |
| `health_check.py` menu labels | Use real `DataProtectionLocators` constants, not guessed text | `health_check.py:202` |
| `health_check.py` popup dismiss | Escape does NOT close this ExtJS popup menu | `health_check.py:213` |
| `FileLevelRecoveryPage` inheritance | Confirmed live the wizard's step-header DOM carries the same `tabSwitchLinkActive` pattern `WizardPage.current_step_title()` depends on — fixed to extend `WizardPage`, removed the weaker local `click_next()` | `file_level_recovery_page.py` (see this project's own architecture review, §0/§3) |
