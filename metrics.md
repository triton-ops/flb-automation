# Framework Quality Metrics — flb-automation

Regenerated 2026-07-23. Computed via a fresh one-off AST-based analysis script (Python's built-in
`ast` module — no new dependency added, matching this project's established preference for
avoiding extra packages where the standard library suffices).

**Scope**: `browser/pom/**/*.py` (Page Objects + Locators), `tests/e2e/conftest.py` (Fixtures),
`tests/e2e/_lib/_shared_helpers.py` + each suite's `_helpers.py` (Helper functions). Test files
(`test_njm_*.py`) and `browser/checks/*.py` (one-off calibration/diagnostic scripts) are excluded
— they're consumers of the framework, not the framework itself. `browser/pom/base/config.py` is
**excluded from the Page Objects table** for the same reason as the last report — it's
dataclasses/an enum/plain functions, not a Page Object (no Playwright actions) or a Locators class.

**Methodology note**: every number below is a real static-analysis measurement, not an estimate,
with one explicit exception — **Duplicate Code (§5) and Unused Code (§9) are NOT re-measured this
round** (see those sections for why) and are left marked stale rather than silently reprinted as
current. Every other section was recomputed fresh against the current tree.

**Why this regeneration exists**: the prior report (2026-07-17) undercounted the framework's real
size by a wide margin — `FlbWizardPage` alone grew from 29 methods/289 lines to 65/659, and four
entire Page Objects (`RepositoryManagementPage`, `GlobalSearchPage`, `AlarmsPage`, `LicensingPage`)
plus their Locators classes existed on disk with zero entries in the old tables. This wasn't one
session's drift — it accumulated across several suite-porting sessions (ObjectStorage's repository
management, UiReporting's Global Search/Licensing, Alarms) without the report being regenerated in
between. Treat this as a lesson: regenerate this file at the end of each suite-porting pass, not
only when something prompts a docs-currency review.

---

## Changes since last report

This is a full regeneration, not an incremental update — the codebase has grown substantially:

1. **4 new Page Objects** (none present in the 2026-07-17 report at all):
   `RepositoryManagementPage` (19 methods, repository detail/self-healing/reclaim), `GlobalSearchPage`
   (14 methods), `AlarmsPage` (3 methods), `LicensingPage` (2 methods) — backing the ObjectStorage,
   UiReporting, and Alarms suites ported since the last report.
2. **3 new Locators classes in `locators.py`** (`RepositoryManagementLocators`,
   `GlobalSearchLocators`) plus **2 Locators classes living OUTSIDE `locators.py`**
   (`AlarmsLocators` in `alarms_page.py`, `LicensingLocators` in `licensing_page.py`) — a real
   deviation from this project's own stated "ALL selectors in `locators.py`, single place to
   maintain" architecture principle (see `browser/README.md`'s Maintenance Points). Flagged here,
   not fixed — moving them is a real refactor with its own risk, out of scope for a docs pass.
3. **`FlbWizardPage` more than doubled** (29→65 methods, 289→659 lines) — ACL mode, app-aware mode,
   full-backup mode/frequency, concurrent-task-limit, encryption (`set_encryption_password()`,
   `_dismiss_kms_warning_if_present()`), Select Items dialog readers/actions, and more accumulated
   across the SourceSelection/BackupExecution/ObjectStorage porting sessions.
4. **`FileLevelRecoveryPage` grew further** (33→37 methods, 562→724 lines).
5. **5 more suites now have their own `_helpers.py`** (Alarms, BackupExecution, FLRToSource,
   ObjectStorage, UiReporting) — helper function count grew from 12 to 25.
6. **A new, unscoped-by-the-old-report complexity outlier**: `conftest.py`'s
   `pytest_runtest_makereport` hook (complexity 17, 83 lines) — a pytest hook, not a fixture, so it
   fell outside the old Fixtures table entirely. It's now this report's #1 complexity outlier by a
   wide margin (next-highest is 9). Not immediately actionable (hooks that branch on
   pass/fail/skip × screenshot/video/trace attachment are expected to have real branching) but
   worth knowing about.
7. **Project-wide 1-TC-per-file test reorganization** (189 `test_njm_<id>.py` files, up from ~164)
   — outside this report's scope (test files aren't measured here), but see `docs/parametrize-pattern.md`
   and `README.md`'s Conventions section for what changed and why.

---

## 1. Page Objects

| Class | File | Methods | Lines |
|---|---|---:|---:|
| `FileLevelRecoveryPage` | file_level_recovery_page.py | 37 | 724 |
| `FlbWizardPage` | flb_wizard_page.py | 65 | 659 |
| `RepositoryManagementPage` *(new)* | repository_management_page.py | 19 | 221 |
| `DataProtectionPage` | data_protection_page.py | 12 | 210 |
| `BasePage` | base_page.py | 20 | 178 |
| `BackupCopyPage` | backup_copy_page.py | 14 | 158 |
| `GlobalSearchPage` *(new)* | global_search_page.py | 14 | 137 |
| `JobManagementPage` | job_management_page.py | 3 | 88 |
| `WizardPage` | wizard_page.py | 4 | 55 |
| `FileShareBackupPage` | file_share_page.py | 3 | 27 |
| `AlarmsPage` *(new)* | alarms_page.py | 3 | 26 |
| `LoginPage` | login_page.py | 2 | 21 |
| `LicensingPage` *(new)* | licensing_page.py | 2 | 16 |
| `FileShareRecoveryPage` | file_share_recovery_page.py | 1 | 12 |
| `BackupCopyRecoveryPage` | backup_copy_recovery_page.py | 0 | 12 |
| **Total** | **15 classes** *(was 11)* | **199** *(was 116)* | **2,544** *(was 1,491)* |

`FlbWizardPage` is now the size outlier by method count (65, 33% of all POM methods), having
overtaken `FileLevelRecoveryPage` (still the outlier by line count, 724). Both grew from real,
independently-justified feature coverage (Options-step controls, encryption dialog handling for
the former; FLR flow depth for the latter), not from unchecked duplication — see §5's caveat below
before assuming size alone signals a problem.

## 2. Locators

| Class | File | Constants | Static methods (parameterized locators) |
|---|---|---:|---:|
| `FileLevelRecoveryLocators` | locators.py | 29 | 3 |
| `RepositoryManagementLocators` *(new)* | locators.py | 22 | 5 |
| `SelectItemsLocators` | locators.py | 20 | 9 |
| `OptionsLocators` | locators.py | 19 | 2 |
| `DataProtectionLocators` | locators.py | 17 | 1 |
| `GlobalSearchLocators` *(new)* | locators.py | 16 | 6 |
| `WizardLocators` | locators.py | 10 | 0 |
| `ScheduleLocators` | locators.py | 6 | 0 |
| `InclusionExclusionLocators` | locators.py | 4 | 0 |
| `BackupCopyLocators` | locators.py | 4 | 0 |
| `LoginLocators` | locators.py | 3 | 0 |
| `RunDialogLocators` | locators.py | 3 | 0 |
| `AlarmsLocators` *(new, lives in `alarms_page.py`, not `locators.py`)* | alarms_page.py | 3 | 0 |
| `FlbWizardLocators` | locators.py | 2 | 2 |
| `DestinationLocators` | locators.py | 2 | 1 |
| `LicensingLocators` *(new, lives in `licensing_page.py`, not `locators.py`)* | licensing_page.py | 2 | 0 |
| `FileShareBackupLocators` | locators.py | 0 | 0 |
| **Total** | **17 classes** *(was 13)* | **162 constants** *(was 84)*, **29 static methods** *(was 12)* |

`FileShareBackupLocators` having zero constants is still expected — File Share Backup has no test
suite yet, and its locator class exists purely as a semantic `LOC` tag inheriting everything from
`WizardLocators`. New this round: `AlarmsLocators`/`LicensingLocators` are real exceptions to this
project's "all selectors live in `locators.py`" principle — see "Changes since last report" §2.

## 3. Fixtures (`conftest.py`)

| Fixture | Lines | Cyclomatic complexity |
|---|---:|---:|
| `flb_job_cleanup` | 31 *(was 24)* | 6 |
| `page` | 18 | 1 |
| `nbr_config` | 8 | 1 |
| `nbr_config_fsb` | 5 | 1 |
| `logged_in_page` | 5 | 1 |
| `browser_context_args` | 8 | 1 |

**6 fixtures, unchanged in count** — `flb_job_cleanup` grew 24→31 lines (its complexity held at 6;
the growth is more branches on *what* to clean up, not new top-level logic shape). Not shown in
this table (it's a hook, not a fixture — see "Changes since last report" §6):
`pytest_runtest_makereport`, 83 lines, complexity **17** — now the single largest complexity
outlier in this report's entire scope.

## 4. Helper Functions

| File | Functions | Notes |
|---|---:|---|
| `tests/e2e/_lib/_shared_helpers.py` | 5 | `attach_test_data` (15 ln), `run_and_wait_flb_job` (18 ln), `flr_browse` (29 ln), `extract_item_names` (6 ln), `verify_checksum` (45 ln) |
| `test_flbv2v3_Alarms/_helpers.py` *(new)* | 2 | `build_flb_job` (38 ln), `read_job_alarm_text` (14 ln) |
| `test_flbv2v3_BackupExecution/_helpers.py` *(new)* | 1 | `build_flb_job` (74 ln — longest suite `build_flb_job()`, reflecting the most Options-step controls exercised of any suite) |
| `test_flbv2v3_FLRFunctional/_helpers.py` | 3 | `build_flb_job` (52 ln), `edit_flb_job_and_rerun` (43 ln), `recover_to_share` (47 ln) |
| `test_flbv2v3_FLRToSource/_helpers.py` *(new)* | 2 | `build_flb_job` (44 ln), `recover_to_source` (33 ln) |
| `test_flbv2v3_IncludeExclude/_helpers.py` | 3 | `build_flb_job` (42 ln), `open_to_inclusion` (12 ln), `has_visible_invalid_feedback` (13 ln) |
| `test_flbv2v3_Inventory/_helpers.py` | 1 | `build_flb_job` (37 ln) |
| `test_flbv2v3_ObjectStorage/_helpers.py` *(new)* | 2 | `build_flb_job` (62 ln), `run_full_then_incremental` (23 ln) |
| `test_flbv2v3_SourceSelection/_helpers.py` *(new)* | 2 | `build_flb_job` (42 ln), `recover_to_share` (35 ln) |
| `test_flbv2v3_UiReporting/_helpers.py` *(new)* | 4 | `build_flb_job` (38 ln), `skipped_items_count` (13 ln), `report_link_attrs` (24 ln), `read_job_alarm_text` (12 ln) |
| **Total** | **25** *(was 12)* | |

5 more suites gained their own `build_flb_job()` since the last report (Alarms, BackupExecution,
FLRToSource, ObjectStorage, SourceSelection, UiReporting — 6 actually, one, SourceSelection, had
already existed but wasn't previously itemized). Each remains intentionally suite-specific (see
`_shared_helpers.py`'s own docstring for the byte-identical-or-superset bar before promoting one to
shared scope) — `test_flbv2v3_BackupExecution`'s 74-line version is the longest, reflecting that
suite's Options-step-heavy TCs (ACL, app-aware, full-backup mode/frequency, concurrent-task-limit,
encryption all in one `build_flb_job()` signature).

## 5. Duplicate Code — **STALE, not re-measured this round**

The prior report's AST-structural duplicate-pair analysis (`ast.dump()` per function body,
`difflib.SequenceMatcher` similarity) is **not** redone here — doing it credibly against a
framework that's grown by ~1,000 lines and 4 new Page Objects needs a dedicated pass, not a
side-effect of a documentation-currency sweep. The prior numbers (96→90 raw pairs, ~8 actionable
≥0.90-similarity pairs, all cross-wizard-type `FlbWizardPage`/`BackupCopyPage` tradeoffs) are **not
reprinted here** since presenting them as current would violate this report's own "every number is
measured" principle. Treat duplicate-code analysis as a known gap in this regeneration — next full
pass should redo §5 and §9 together, since both need the same kind of whole-codebase AST walk.

## 6 & 7. Average Method Length / Average Class Size

Measured across POM (Page Objects + Locators static methods) + fixtures + all suite/shared helper
functions — 270 functions total.

- **Average method/function length**: 12.9 lines (median 8, n=270)
- **Longest function**: `pytest_runtest_makereport` (`conftest.py`) at 83 lines — a pytest hook,
  not a Page Object method (see "Changes since last report" §6); the longest actual Page Object
  method remains within `FileLevelRecoveryPage`/`FlbWizardPage`'s own larger bodies.
- **Average class size**: computed per-class as (end line − start line + 1) across all 15 Page
  Object + 17 Locators classes; `FileLevelRecoveryPage` (724 lines) and `FlbWizardPage` (659 lines)
  are the two largest by a wide margin — see §1's own note on why.

## 8. Cyclomatic Complexity

- **Average**: 1.72 (n=270, across POM + fixtures + all helper functions)
- **Distribution**: 251 simple (1–3), 14 moderate (4–6), 4 complex (7–10), **1 very complex (11+)**

| Complexity | Function | File |
|---:|---|---|
| 17 | `pytest_runtest_makereport` *(hook, not previously in scope — see §3)* | `conftest.py` |
| 9 | `DataProtectionPage.get_job_status` | `data_protection_page.py` |
| 8 | `JobManagementPage.delete_job` | `job_management_page.py` |
| 8 | `build_flb_job` | `test_flbv2v3_BackupExecution/_helpers.py` |
| 7 | `recover_to_share` | `test_flbv2v3_FLRFunctional/_helpers.py` |
| 6 | `flb_job_cleanup` | `conftest.py` |
| 6 | `recover_to_share` | `test_flbv2v3_SourceSelection/_helpers.py` |
| 5 | `retry_on_transient` | `base/retry.py` |
| 5 | `verify_checksum` | `_lib/_shared_helpers.py` |
| 5 | `build_flb_job` | `test_flbv2v3_ObjectStorage/_helpers.py` |

`pytest_runtest_makereport` at 17 is the new #1 outlier, branching on pass/fail/skip status ×
screenshot/video/trace-attachment availability — the same "complexity concentrated in the kind of
logic that's supposed to be complex" pattern the prior report found for polling loops and
multi-source verification functions, not accidental complexity. 93% of all functions in scope
remain simple (1–3).

## 9. Unused Code — **STALE, not re-measured this round**

Same caveat as §5: cross-referencing every POM method against every call site in `tests/e2e/`
(now 189 test files, up from ~164) to find zero-caller methods needs a dedicated pass. The prior
report's list (12 flagged, all `BackupCopyPage`/`FileShareBackupPage` methods tied to those two
suites having zero pytest coverage) is **not reprinted here** — it's likely still roughly accurate
in shape (neither suite has been built out since) but may have drifted with `FlbWizardPage`'s
growth, and presenting stale numbers as current isn't worth the risk. Re-run alongside §5 next
pass.

## 10. Technical Debt Indicators

| Indicator | Count |
|---|---:|
| `CALIBRATED live` / `VERIFIED live` markers (this report's exact scope — POM + conftest + helpers) | 39 files containing 163 markers |
| ⚠ / TODO / FIXME / XXX markers (same scope) | 37 |
| Comment/docstring lines (approx — line-prefix heuristic, not a full tokenizer) | ~852 |
| Code lines (approx, same caveat) | ~4,363 |
| Comment-to-code ratio (approx) | 0.20 *(was 0.18)* |

**On this report's 163 vs. `CALIBRATION_LOG.md`'s codebase-wide 251**: same two-different-scopes
relationship as the prior report — this report's number is POM + conftest + helper files only;
`CALIBRATION_LOG.md` deliberately covers the *whole* codebase including `browser/checks/*.py` and
every `test_njm_*.py` file. `CALIBRATION_LOG.md` remains the canonical, dated, one-line-per-entry
index — this section exists only to track the *volume* of documented calibration findings as a
debt-surface proxy, not to duplicate the log itself.

---

### Summary

| Category | Headline number |
|---|---|
| Page Objects | 15 classes *(↑4)*, 199 methods *(↑83)*, 2,544 lines *(↑1,053)* |
| Locators | 17 classes *(↑4)*, 162 constants *(↑78)*, 29 static methods *(↑17)* — 2 classes now live outside `locators.py` (flagged, not fixed) |
| Fixtures | 6 *(unchanged)* — plus 1 previously-unscoped hook (`pytest_runtest_makereport`, complexity 17, now the #1 outlier) |
| Helper functions | 25 *(↑13)* — 6 more suites gained their own `build_flb_job()` |
| Duplicate code | **STALE — not re-measured this round, see §5** |
| Avg. method length | 12.9 lines (n=270, was 12.8 on a much smaller n=128) |
| Avg. cyclomatic complexity | 1.72 *(was 1.76)*, 93% simple — one new complexity-17 outlier (a hook, not a fixture) |
| Unused code | **STALE — not re-measured this round, see §9** |
| Technical debt | 163 documented calibration findings (this report's scope) / 251 codebase-wide (see `CALIBRATION_LOG.md`), comment ratio ~0.20 (approx) |
