# Framework Quality Metrics — flb-automation

Regenerated 2026-07-17. Computed directly from the source tree via a one-off AST-based analysis
script (Python's built-in `ast` module — no new dependency added, matching this project's
established preference for avoiding extra packages where the standard library suffices).

**Scope**: `browser/pom/**/*.py` (Page Objects + Locators), `tests/e2e/conftest.py` (Fixtures),
`tests/e2e/_lib/_shared_helpers.py` + each suite's `_helpers.py` (Helper functions). Test files
(`test_njm_*.py`) and `browser/checks/*.py` (one-off calibration/diagnostic scripts) are excluded
— they're consumers of the framework, not the framework itself. `browser/pom/base/config.py` (new
since the last report) is **also excluded from the Page Objects table** — it's dataclasses/an enum/
plain functions, not a Page Object (no Playwright actions) or a Locators class; it doesn't fit
either existing category cleanly, so rather than force it into one, it's called out here instead.

**Methodology note**: every number below is a real static-analysis measurement, not an estimate.
This regeneration's script is a fresh rewrite of the original one-off script (not preserved from
the prior report), so treat exact reproduction of prior internal counts (e.g. the previous
report's method-length sample size) as approximate — the *methodology* is the same (AST-walk,
`ast.dump()`-based structural diff, McCabe-style complexity), not necessarily byte-identical code.
One real correction made this round: the prior report's technical-debt file scope had accidentally
widened to include every `test_njm_*.py` file despite its own stated exclusion — this regeneration
enforces that exclusion precisely (see §10).

---

## Changes since last report

This is a full regeneration, not an incremental update — a lot happened between reports:

1. **Typed, multi-environment config system** (`browser/pom/base/config.py`, new) replaced the old
   `driver.py:load_config()` — the prior report's #1 cyclomatic-complexity outlier (complexity 12)
   no longer exists in this codebase at all, and its replacement is deliberately excluded from this
   report's Page Objects scope (see above) rather than silently absorbed into the count.
2. **`FileLevelRecoveryPage` now extends `WizardPage`**, not `BasePage` — its local `click_next()`
   (a weaker, fixed-wait reimplementation) was removed in favor of the inherited
   retry-until-step-changes version, live-verified against the real appliance.
3. **`attach_test_data()` added** to `_shared_helpers.py`, called from all 3 suites'
   `build_flb_job()` — Allure test-data/job-name evidence, which is why every suite's
   `build_flb_job()` grew slightly (see §4).
4. **A new `page` fixture override** in `conftest.py` (console/network capture for Allure) — the
   fixture count grew from 5 to 6.
5. **4 duplicated Inventory OS-support tests consolidated** into one parametrized file (outside
   this report's scope — suite tests aren't measured here — but relevant context for §5/§9).
6. **`CALIBRATION_LOG.md` built** (repo root) — a dated index of all `CALIBRATED live` findings
   across the *whole* codebase (94, including `browser/checks/*.py` and test files, deliberately
   broader than this report's 71 — see §10 for why the two numbers legitimately differ).
7. **mypy, pre-commit, CI, folder reorg** (`tests/e2e/_lib/`, `tests/e2e/test_infrastructure/`) —
   none of these change the numbers below directly, but they're why the codebase looks different
   enough that a from-scratch regeneration (rather than a diff) was the right call.

---

## 1. Page Objects

| Class | File | Methods | Lines |
|---|---|---:|---:|
| `FileLevelRecoveryPage` | file_level_recovery_page.py | 33 | 562 |
| `FlbWizardPage` | flb_wizard_page.py | 29 | 289 |
| `DataProtectionPage` | data_protection_page.py | 12 | 182 |
| `BasePage` | base_page.py | 19 | 156 |
| `BackupCopyPage` | backup_copy_page.py | 10 | 127 |
| `JobManagementPage` | job_management_page.py | 3 | 57 |
| `WizardPage` | wizard_page.py | 4 | 55 |
| `FileShareBackupPage` | file_share_page.py | 3 | 27 |
| `LoginPage` | login_page.py | 2 | 12 |
| `FileShareRecoveryPage` | file_share_recovery_page.py | 1 | 12 |
| `BackupCopyRecoveryPage` | backup_copy_recovery_page.py | 0 | 12 |
| **Total** | **11 classes** | **116** *(was 117)* | **1,491** *(was 1,481)* |

`FileLevelRecoveryPage` is still the clear size outlier (94% larger than the next-biggest class,
28% of all POM methods) — its method count dropped by one (`click_next()` removed, now inherited
from `WizardPage` — see "Changes since last report"), but its overall line count grew slightly (a
new explanatory comment replacing the removed method). `WizardPage` grew from 51→55 lines for the
same reason (the comment explaining the inheritance).

## 2. Locators

| Class | Constants | Static methods (parameterized locators) |
|---|---:|---:|
| `FileLevelRecoveryLocators` | 29 | 3 |
| `DataProtectionLocators` | 16 | 1 |
| `WizardLocators` | 10 | 0 |
| `ScheduleLocators` | 6 | 0 |
| `InclusionExclusionLocators` | 4 | 0 |
| `BackupCopyLocators` | 4 | 0 |
| `LoginLocators` | 3 | 0 |
| `SelectItemsLocators` | 3 | 4 |
| `RunDialogLocators` | 3 | 0 |
| `FlbWizardLocators` | 2 | 2 |
| `DestinationLocators` | 2 | 1 |
| `OptionsLocators` | 2 | 1 |
| `FileShareBackupLocators` | 0 | 0 |
| **Total** | **13 classes** | **84 constants**, **12 static methods** |

Unchanged from the last report — no locator additions/removals since then.
`FileShareBackupLocators` having zero constants is still expected, not a gap — File Share Backup
has no test suite yet (see §9), and its locator class exists purely as a semantic `LOC` tag
inheriting everything from `WizardLocators`.

## 3. Fixtures (`conftest.py`)

| Fixture | Lines | Cyclomatic complexity |
|---|---:|---:|
| `flb_job_cleanup` | 24 | 6 |
| `page` | 18 *(new)* | 1 |
| `nbr_config` | 8 | 1 |
| `nbr_config_fsb` | 5 | 1 |
| `logged_in_page` | 5 | 1 |
| `browser_context_args` | 8 | 1 |

**6 fixtures total** *(was 5)* — the new `page` fixture override wraps pytest-playwright's own
`page` to auto-collect console/network activity for Allure evidence (see
`docs/allure-reporting.md`), following the same "redeclare and wrap" pattern already used by
`browser_context_args`. `flb_job_cleanup` remains the only fixture with real branching
(complexity 6, unchanged) — expected, since it's the one doing conditional teardown logic.
`nbr_config` grew 3→8 lines (now calls `.validate()` before returning, per the config system
rewrite).

## 4. Helper Functions

| File | Functions | Notes |
|---|---:|---|
| `tests/e2e/_lib/_shared_helpers.py` | 5 *(was 4)* | `attach_test_data` (15 ln, **new**), `run_and_wait_flb_job` (18 ln), `flr_browse` (29 ln), `extract_item_names` (6 ln), `verify_checksum` (45 ln) |
| `test_flbv2v3_IncludeExclude/_helpers.py` | 3 | `build_flb_job` (42 ln, was 38), `open_to_inclusion` (12 ln), `has_visible_invalid_feedback` (13 ln) |
| `test_flbv2v3_Inventory/_helpers.py` | 1 | `build_flb_job` (37 ln, was 33) |
| `test_flbv2v3_FLRFunctional/_helpers.py` | 3 | `build_flb_job` (52 ln, was 48), `edit_flb_job_and_rerun` (43 ln), `recover_to_share` (34 ln) |
| **Total** | **12** *(was 11)* | |

Every suite's `build_flb_job()` grew by exactly 4 lines — the new `attach_test_data(...)` call
added to each (see "Changes since last report"). Each suite's own `build_flb_job()` remains
intentionally separate (genuinely different signatures/behavior per suite); the 5 functions in
`_shared_helpers.py` are the ones verified byte-identical (or a strict superset) across suites.

## 5. Duplicate Code

Measured via AST-structural comparison (`ast.dump()` per function body, `difflib.SequenceMatcher`
similarity ratio) — ignores variable-name/whitespace noise, compares actual code shape. Threshold
≥5 lines, to exclude the long tail of trivially-short wrapper methods that share this POM's own
common idiom (`self.click(LOCATOR); self.wait(N); return self`) by design.

| | Pairs at ≥0.60 similarity, ≥5 lines |
|---|---:|
| **Last report** | 96 |
| **Now** | **90** |

The genuinely actionable duplicates (≥0.90 similarity) — essentially unchanged from the last
report:

| Similarity | Pair | Status |
|---:|---|---|
| 1.00 | `FlbWizardPage.select_machine` ↔ `BackupCopyPage.select_backup` | Known, accepted cross-wizard-type tradeoff (see §10 of the framework-guidelines doc / this report's own history) |
| 1.00 | `FlbWizardPage.select_repository` ↔ `BackupCopyPage.select_repository` | Same |
| 1.00 | `FlbWizardPage.set_retention` ↔ `BackupCopyPage.set_retention` | Same |
| 0.99 | `FileLevelRecoveryPage.recover_file_level` ↔ `FileShareRecoveryPage.recover_file_share` | **Not duplication** — inheritance override reusing the shared `_select_job_and_open_recover_menu()` base |
| 0.99 | `FlbWizardPage.enable_inclusion` ↔ `enable_exclusion` | Both thin wrappers delegating to `_enable_pattern_field()` — expected shape, not copy-paste |
| 0.97 | `FlbWizardPage.set_immutable` ↔ `BackupCopyPage.set_immutable` | Cross-wizard-type tradeoff |
| 0.97 | `BackupCopyPage`'s 3 `set_retention_mode_*` methods (pairwise) | Genuinely 3 near-identical radio-click methods; low-risk, low-value to merge |
| 0.96 | `FlbWizardPage.set_run_on_demand` ↔ `BackupCopyPage.set_run_on_demand` | Same cross-wizard-type tradeoff |

One pair just below the 0.90 cut, carried over from the last report:

| Similarity | Pair | Status |
|---:|---|---|
| 0.84 *(was 0.86)* | `DataProtectionPage.edit_job` ↔ `JobManagementPage._open_manage_menu` | Both share the "select_job_row + click one button + wait" shape as a side effect of an earlier consolidation — not worth chasing further |

A handful of additional 0.80–0.88 pairs appear this round (`DataProtectionPage.run_job` ↔
`stop_job`, `edit_job` ↔ `FileLevelRecoveryPage.recover_file_level`/`_select_job_and_open_recover_menu`,
`BackupCopyPage.set_run_on_demand` ↔ two of its own `set_retention_mode_*` siblings) — all the same
generic "select a row, click one button, wait" shape every simple wizard-navigation method shares;
not new duplication, just more pairs crossing a lower threshold.

## 6 & 7. Average Method Length / Average Class Size

- **Average method/function length**: 12.8 lines *(was 12.7)* (median 10, n=128)
- **Longest method**: `test_flbv2v3_FLRFunctional/_helpers.py`'s `build_flb_job()` at 52 lines
  (grew from 48 — the new `attach_test_data()` call; still a genuine suite-specific sequence with
  real branching, not a decomposition candidate)
- **Average class size**: 135.5 lines *(was 134.6)* (median 57, n=11)
- **Largest class**: `FileLevelRecoveryPage` at 562 lines (see §1)

## 8. Cyclomatic Complexity

- **Average**: 1.76 *(was 1.84 — improved)* (n=128)
- **Distribution**: 117 simple (1-3), 10 moderate (4-6), 1 complex (7-10), **0 very complex (11+)**
  *(was 1)*

| Complexity | Function |
|---:|---|
| 7 | `DataProtectionPage.get_job_status` |
| 6 | `_shared_helpers.verify_checksum` |
| 6 | `test_flbv2v3_FLRFunctional/_helpers.recover_to_share` |
| 5 | `JobManagementPage.delete_job` |
| 4 | `FileLevelRecoveryPage.list_folder_contents` |
| 4 | `FlbWizardPage._tick_checkbox_robust` |
| 4 | `DataProtectionPage._click_menu_item_robust` |
| 4 | `BasePage.wait_masks_gone` |
| 4 | `BackupCopyPage.expand_all_backup_groups` |
| 4 | `WizardPage.click_next` |

**The prior #1 outlier (`driver.py:load_config`, complexity 12) is gone — not simplified, removed
entirely.** It was replaced by `config.py`'s `load_app_config()`, which is excluded from this
report's scope (see the top-of-file note) rather than silently folded in; a fair like-for-like
complexity comparison would need `config.py` measured separately; on a quick read it doesn't
appear to reintroduce a single 12-branch function (the logic is split across several small
functions — `current_environment()`, `_load_dotenv_layers()`, `_appliance_from_env()` — each simple
on its own). Every other entry in the top 10 remains a **polling loop** (retry/wait-until-condition)
or a genuine multi-source verification (`verify_checksum`, `recover_to_share`) — complexity
concentrated in the kind of logic that's supposed to be complex, not accidental. 91% of all
functions remain simple.

## 9. Unused Code

Zero real call sites found anywhere in the repo (own `def` line excluded):

- `BackupCopyPage.expand_all_backup_groups`, `select_backup` *(new)*, `set_retention_mode_exact_copy`, `set_retention_mode_keep_last`, `set_retention_mode_sync_custom`
- `FileLevelRecoveryPage.set_overwrite_behavior`, `has_overwrite_behavior`
- `FlbWizardPage.set_encryption`
- `DataProtectionPage.start_backup_copy`, `start_file_share_backup`
- `FileShareBackupPage.expand_shares` *(new)*, `select_share` *(new)*

**12 flagged, up from 9** — all 3 new entries (`BackupCopyPage.select_backup`,
`FileShareBackupPage.expand_shares`/`select_share`) are further evidence for the same finding this
project's architecture review already identified as its single biggest current gap: File Share
Backup and Backup Copy have real, calibrated Page Objects with **zero pytest suite coverage**, so
none of their methods have a caller yet. This isn't scope creep in the unused-code metric — it's
the same root cause showing up in a second, independent measurement. All 12 remain deliberately
kept as working, safety-fence-compliant scaffolding for planned-but-not-yet-tested areas, not
forgotten dead code — they'll stop being "unused" the moment either suite gets built.

## 10. Technical Debt Indicators

| Indicator | Count |
|---|---:|
| `CALIBRATED live` / `VERIFIED live` markers (this report's exact scope) | 71 |
| ⚠ / TODO / FIXME / XXX markers | 13 |
| Code lines (POM + locators + helpers) | 2,274 |
| Comment/docstring lines | 403 |
| Comment-to-code ratio | 0.18 |

**On the 71 vs. `CALIBRATION_LOG.md`'s 94**: these are two different, both-correct numbers for two
different scopes. This report's 71 is scoped exactly as stated at the top of this file (POM +
locators + conftest.py + helper files only). `CALIBRATION_LOG.md`'s 94 deliberately covers the
*whole* codebase, including `browser/checks/*.py` (12 standalone scripts) and every
`test_njm_*.py` file — both excluded here because they're consumers of the framework, not the
framework itself. The prior version of this report stated 96 for what it called the same scope as
this one; that number appears to have been measured with an unintentionally wider file set (this
regeneration's script found and fixed the same class of scope-creep bug in its own technical-debt
counter — see the methodology note at the top). 71 is the number that actually matches the stated
scope.

96 calibration markers (now 71, precisely scoped) remain a real but *managed* debt surface — each
documents a specific, live-verified finding rather than a vague admission. **This is no longer an
open recommendation**: `CALIBRATION_LOG.md` (repo root) now indexes all of them.

---

### Summary

| Category | Headline number |
|---|---|
| Page Objects | 11 classes, 116 methods *(↓1)*, 1,491 lines *(↑10)* |
| Locators | 13 classes, 84 constants (unchanged) |
| Fixtures | 6 *(↑1: new `page` Allure-evidence override)* |
| Helper functions | 12 *(↑1: new `attach_test_data`)* |
| Duplicate code (real, ≥0.90 similarity) | ~8 actionable pairs (of 90 raw matches at ≥5 lines, ↓6) |
| Avg. method length | 12.8 lines |
| Avg. class size | 135.5 lines |
| Avg. cyclomatic complexity | 1.76 *(↓ from 1.84 — the old 12-complexity outlier is gone)*, 91% simple |
| Unused code | 12 flagged *(↑3, all tied to the FSB/Backup Copy zero-coverage gap)*, all reviewed-and-kept scaffolding |
| Technical debt | 71 documented calibration findings *(this report's scope)* / 94 codebase-wide (see `CALIBRATION_LOG.md`), comment ratio 0.18 |
