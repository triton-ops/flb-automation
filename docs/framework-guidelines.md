# Framework Engineering Guidelines — flb-automation

Prepared 2026-07-17. These are binding engineering standards for this Playwright + pytest
framework, written by codifying what this codebase has already proven to work — every rule below
is grounded in an existing, working pattern (cited by file) or a real, documented incident this
project hit and fixed. Where a current file doesn't yet fully match a rule, that's noted as a
gap, not silently glossed over — **this document does not modify any source code**; gaps are
follow-up candidates, not something fixed here.

These guidelines sit *alongside* `CLAUDE.md` (the binding safety-fence/execution rules) and the
`execute-tc` skill (the TC-execution workflow) — they don't replace either. Where this document
and `CLAUDE.md` overlap (safety fence, honest reporting, evidence), `CLAUDE.md` is authoritative.

---

## 1. Naming Convention

- **Classes**: `PascalCase`, suffixed by role — `XxxPage` for a Page Object (`FlbWizardPage`,
  `DataProtectionPage`), `XxxLocators` for a locator class (`WizardLocators`,
  `FileLevelRecoveryLocators`). Never mix the two roles in one class.
- **Methods/functions**: `snake_case`. Action methods are verb-first (`click_visible`,
  `select_machine`, `open_item_picker`); query/predicate methods read as a question or state
  (`is_visible`, `files_ready`, `has_overwrite_behavior`).
- **Private/internal helpers**: single leading underscore (`_tick_checkbox_robust`,
  `_select_job_and_open_recover_menu`, `_enable_pattern_field`). A method is private if it exists
  only to be composed by a public method in the *same* class — the moment another class needs to
  call it, drop the underscore and document why it's now part of the public surface (see
  `DataProtectionPage.select_job_row()`'s docstring for a worked example).
- **Booleans**: `is_`/`has_`/`needs_` prefix, or a clear adjective/participle
  (`files_ready`, `files_awaiting_selection`). Avoid naming a method for a *side effect* it
  produces rather than the question it answers (e.g. a method that both checks AND advances a
  step) unless a docstring explicitly flags it — `FlbWizardPage.inclusion_advances_wizard()` is
  the one existing example of this, and its docstring explains why no side-effect-free
  alternative exists in this build. Don't add a second one without the same justification.
- **The locator-class-alias convention**: every module importing one primary locator class aliases
  it to `L` (`from .locators import FileLevelRecoveryLocators as L`). Keep this — it's used
  consistently across every Page Object file and any reviewer expects `L.SOMETHING` to mean "the
  locator class this file is about."

## 2. Folder Organization

```
browser/pom/base/        BasePage, driver.py (config/browser factory), retry.py — foundational,
                          zero locator imports, zero business logic
browser/pom/common/      Shared cross-wizard pages (DataProtectionPage, JobManagementPage,
                          LoginPage, WizardPage) + the single locators.py + checksum.py
browser/pom/backup_types/ One file per job-type wizard/recovery flow (flb_wizard_page.py,
                          backup_copy_page.py, file_level_recovery_page.py, ...)
browser/checks/          One-off calibration/diagnostic scripts (health_check.py,
                          framework_doctor.py, cleanup_auto_flb_jobs.py, check_*.py) — run
                          standalone, NOT part of the pytest suite, NOT imported by tests/
tests/e2e/conftest.py    Shared fixtures only
tests/e2e/_lib/_shared_helpers.py  Cross-suite helpers verified byte-identical across every suite
                          that had a copy (see §15)
tests/e2e/test_flbv2v3_<Suite>/  One folder per Jira Test Execution: _helpers.py (suite-specific
                          build/run/verify) + one test_njm_<id>.py per TC
test-data/               environment.md, test-data.md, manifests/ — the single source of truth
                          for fixture names/paths/checksums (never hardcode these elsewhere)
cases/<Suite>/           Historical pre-Playwright runbooks — reference only, not executed
docs/                    Standing engineering docs (this file, metrics.md at repo root today —
                          consider moving metrics.md here too for consistency)
```

**Rule**: a new job type gets a new file under `backup_types/`, never a new method bag bolted
onto an existing unrelated class. A new suite gets a new `tests/e2e/test_flbv2v3_<Suite>/`
folder with its own `_helpers.py`, never test files dropped into an existing suite's folder.

## 3. Test Naming

- **File**: `test_njm_<id>.py` — the bare Jira issue number, lowercase `test_njm_` prefix, one
  file per TC. Never bundle multiple unrelated TCs into one file.
- **Function**: `test_<snake_case_description>` — describe *what's being verified*, not the TC
  id (the id is already in the filename and the Allure title). Examples already in this codebase:
  `test_windows_server_2025_e2e`, `test_backup_step_recovery_point_selection`,
  `test_download_to_browser_mixed_selection`, `test_files_step_browse_and_select`.
- **Allure title**: `@allure.title("NJM-<id> — <short description>")` on every test function —
  100% of existing tests follow this; keep it universal so Allure reports are scannable without
  opening each test's source.
- **Markers**: `pytestmark = [pytest.mark.flb, pytest.mark.<suite_marker>, pytest.mark.jira("NJM-<id>")]`
  (or `.fsb` for File Share Backup). Every suite now has its own registered marker in
  `pyproject.toml`'s `markers` list (`include_exclude`, `inventory`, `flrfunctional`,
  `sourceselection`, `objectstorage`, `backupexecution`, `flrtosource`, `alarms`, `uireporting`,
  …) — `pytest -m <suite>` works for all of them. Register a new suite's marker there before its
  first test file, or `--strict-markers` will fail collection.
- **One test function per business flow/assertion group** — don't chain unrelated verifications
  into one giant test function; a TC with genuinely distinct sub-flows gets multiple test
  functions in the same file, not one function doing everything.

## 4. Fixture Naming

- `snake_case`, named for **what they provide**, not how they're implemented:
  `logged_in_page` (an authenticated `Page`), `nbr_config`/`nbr_config_fsb` (resolved config
  dicts), `flb_job_cleanup` (a cleanup-registering factory), `browser_context_args` (Playwright's
  own context-args override point).
- **Factory fixtures return a callable**, not a raw value, when the test needs to parameterize
  what gets set up per-call — `flb_job_cleanup(job_name)` registers a name and returns it,
  letting the test both name its job *and* guarantee teardown in one line
  (`job_name = flb_job_cleanup("AUTO_FLB_NJM-70307")`). Prefer this shape over a fixture that
  hardcodes one job name.
- Every fixture that touches the live appliance (creates state, logs in, deletes a job) documents
  **when** its teardown runs (every test / pass-only / fail-only) directly in its docstring —
  `flb_job_cleanup`'s own docstring is the reference example (always runs, pass or fail, unless
  `--keep-failed-jobs`).
- Fixture scope: default to function-scope unless there's a measured, stated reason for a wider
  scope (session-scoped auth was considered and explicitly rejected earlier in this project's
  history in favor of a fresh `logged_in_page` per test, trading a login round-trip for isolation
  — don't silently "optimize" this without re-confirming the isolation tradeoff still holds).

## 5. Variable Naming

- **The same concept uses the same name and parameter position everywhere.** Every method that
  takes a job name takes it as `job_name: str` in the first positional slot after `self`(and
  `page` for helper functions); every method needing a duplicate-name disambiguator takes
  `nth: int = 0` as a keyword-defaultable parameter, always spelled `nth`, never `index`/`i`/
  `which`. This consistency (already near-100% across the codebase) is what lets a reader predict
  a new method's signature without opening it — preserve it.
- `path_segments: list[str]` for FLR-tree navigation paths, `drill_path: list[str]` for the
  Select-Items-dialog wizard picker path — these are **not interchangeable** even though both are
  "a list of folder names": one is tree-node names (`"C:"`), the other is picker display names
  (`"Local Disk (C:)"`). Never rename one to match the other; a bug this session was caused by
  exactly this confusion (see `test_njm_70313.py`'s fix history) — keep the names distinct so the
  mistake is harder to make again.
- Local variables: `snake_case`, short-lived and short-named is fine inside a small scope
  (`loc`, `row`, `waited`), but a variable crossing more than ~10 lines of scope should have a
  full descriptive name.
- Locator instances fetched via `self.page.locator(...)` are named for **what they resolve to**
  (`textarea`, `combo_input`, `path_lbl`), never generic (`el`, `elem`, `x`).

## 6. Constants

- **Locator constants**: `ALL_CAPS`, defined **only** in `locators.py`, grouped inside the
  `XxxLocators` class matching the page/widget they belong to. Never a bare XPath string literal
  inside a Page Object method or a test file — if a value needs runtime parameterization, it's a
  `@staticmethod` on the locator class (e.g. `DataProtectionLocators.sidebar_job_row(name)`),
  never an f-string built inline in the calling method.
- **Safety-fence prefixes**: module-level `_SAFE_PREFIXES = ("AUTO_FLB_", "AUTO_FSB_")`
  (`job_management_page.py`) — any new destructive-action method needs the same guard, defined
  once per module, never duplicated as a magic string in multiple places.
- **Suite fixture constants** (fileset names, share paths, manifest filenames): defined once at
  the top of that suite's `_helpers.py`, `ALL_CAPS` (`MIXED_TYPES_FILES`, `WINFS3_SHARE_CIFS`).
  Never inline a literal fileset/path string directly in a test file — if two suites need the
  identical constant, that's a signal it may belong in `_shared_helpers.py` instead (see §15).
- **No magic timeouts inline in test files.** A timeout value belongs in the POM layer, either as
  a `BasePage`/method default or an explicit override with a `CALIBRATED live YYYY-MM-DD`
  comment explaining why that specific number was chosen (see `DataProtectionPage.run_job()`'s
  `timeout=60_000` for the reference pattern).

## 7. Configuration

- **Resolution order** (from `config.py`'s `load_app_config()`, the canonical implementation —
  see `docs/configuration.md` for the full writeup): real process env var, then a per-environment
  `.env.<environment>` overlay (only for a non-`local` `NBR_ENV`), then the base `.env`, then the
  gitignored JSON config file (`browser/config/ui_config.json` / `ui_config_fsb.json`) as final
  fallback. Each layer only overrides the *specific keys* it sets — a partially-set layer plus a
  lower one for the rest still resolves correctly. Any new config source must follow this same
  override-not-replace precedence.
- **Never hardcode** an appliance URL, machine name, repo name, or credential in a test or POM
  method — always via `load_app_config()` (`.flb`/`.fsb`/`.share(host)`) or a `test-data/*.md`-sourced
  constant. This is also a `CLAUDE.md` Golden Rule; repeating it here because it's the single
  most load-bearing configuration rule in the project.
- **One typed object per appliance/host domain**, not one generic dict with a growing key list —
  `AppConfig.flb`/`.fsb` (`ApplianceCredentials`) for the two NBR appliances, `AppConfig.share(host)`
  (`ShareCredentials`) for arbitrary third-party fixture hosts (win-fs3, etc.), kept as genuinely
  separate types because they resolve genuinely different env-var namespaces and validate
  differently.
- **Validate explicitly where a credential is actually required** — `.validate(label)` raises
  `ConfigError` listing every missing/malformed field at once; call it in any fixture/script that
  needs a guaranteed-working login (see `conftest.py`'s `nbr_config` fixture), not in code paths
  that merely pass a possibly-unconfigured value through (see `nbr_config_fsb`, unused today).

## 8. Environment Variables

- **Naming**: `NBR_<APPLIANCE>_<FIELD>` for the two Director appliances (`NBR_FLB_URL/USER/PASS`,
  `NBR_FSB_URL/USER/PASS`); `<HOST>_<FIELD>` for any other fixture host used as a recovery/export
  target (`WINFS3_USER/PASS`). A legacy alias (`NBR_UI_URL/USER/PASS`, FLB-only) exists for
  scripts predating the FLB/FSB split — don't extend it to new code, only `NBR_FLB_*` for FLB.
  `NBR_ENV` selects the environment (`local`/`dev`/`qa`/`staging`/`production`) — see
  `docs/configuration.md`.
- **`.env` is gitignored; `.env.example` documents every key with an empty/placeholder value.**
  Adding a new required env var means adding it to `.env.example` in the same change — an
  undocumented required var is a real onboarding failure mode, not a hypothetical one.
- **Credentials never appear in**: source code, git history, chat/agent output, log files, or any
  script written to disk (including throwaway calibration scripts) — load via the appropriate
  `load_*()` function and pass the returned value straight into a Playwright action, never
  through a shell command, environment-variable-export command, or `print()`.
- **When a human must enter a credential live** (e.g. into a UI form during first-time
  calibration of a new field, before an automated `.env`-based path exists) — it is typed by the
  human directly in their own browser session, never scripted or echoed by an agent on their
  behalf. This was a hard rule established during this project's own CIFS-credential calibration
  work and is treated as non-negotiable, not a style preference.

## 9. Logging

**This framework deliberately does not use Python's `logging` module anywhere in `browser/pom/`.**
This is a measured, confirmed characteristic (verified via repo-wide search), not an oversight —
Allure's per-test video recording + auto-attached failure screenshot, combined with pytest's own
assertion output, **are** this project's evidence/logging layer (see `CLAUDE.md` Golden Rule 4,
"Evidence always"). Do not add `logging`/`print()` calls to Page Object methods; if a method needs
to communicate WHY it did something, that belongs in its docstring (calibration comment), and if
it needs to communicate WHAT it observed at runtime, that belongs in its return value for the
test to assert on and report.

**Narrow exception**: standalone scripts under `browser/checks/` (calibration, health checks, the
Framework Doctor) are not part of the pytest evidence trail and may use `print()` freely for
human-readable console output — that's a genuinely different context from a Page Object method.

## 10. Exception Handling

- `try/except: pass` is reserved for **optional, best-effort UI interactions where failure is
  expected and harmless** — always with a comment stating *why* swallowing is safe here.
  Reference examples: `FileLevelRecoveryPage._close_finish_step()` (closing a confirmation step
  that may not be present), `WizardPage.click_cancel()`'s second-confirm-popup handling,
  `BasePage.reveal_and_click()`'s force-click-then-dispatch fallback.
- **Never** wrap a test-level `assert` in a `try/except` that could suppress it — a swallowed
  assertion is a false PASS, and this project's Golden Rule 5 ("Honest reporting") treats that as
  a serious violation, not a convenience.
- **Guard conditions that protect against unsafe actions raise, they don't silently no-op.**
  `JobManagementPage.delete_job()`'s safety-fence check (`raise ValueError(...)` for a non-`AUTO_*`
  name) is the reference pattern — a silent return would let a caller believe the guard ran when
  it actually skipped the dangerous action for the wrong reason.
- **Retry loops catch broad `Exception` intentionally** (DOM/network timing is inherently flaky
  in this ExtJS app) but every one has a bounded attempt count or timeout — never an unbounded
  retry. `DataProtectionPage.open_create_menu()`'s `attempts: int = 3` and
  `FlbWizardPage._tick_checkbox_robust()`'s `timeout_ms` parameter are the reference shapes.

## 11. Assertions

- **Every test verdict comes from a real `assert` with a descriptive f-string message showing
  expected vs. actual** — e.g. `assert status == "Successful", f"job did not succeed: {status}"`.
  A bare `assert x` with no message is not acceptable in a new test.
- **Page Object methods never contain `assert`.** A POM method returns state (`bool`, `str`,
  `list[dict]`) for the *test* to assert on — this keeps the "what happened" (POM) and "was that
  correct" (test) concerns separated, and is already followed with zero exceptions across the
  current codebase's ~120 POM methods.
- **"The wizard advanced" is not verification.** The real, content-level assertion (an FLR-browse
  listing match, a checksum match, a dashboard status check, an explicit wizard confirmation
  message) is what determines PASS — never treat "no exception was raised" as proof a recovery
  actually started (see `FileLevelRecoveryPage.execute_custom_location_recovery()`'s own
  docstring, which explicitly returns a boolean for exactly this reason rather than trusting the
  absence of an exception).
- **Never loosen an assertion to force a green result.** A genuine, unexpected finding — even one
  that looks like flakiness at first — is more valuable than a false PASS. This is `CLAUDE.md`
  Golden Rule 5 restated because it's the single most important standard in this document.

## 12. Waiting Strategy

- **Prefer polling a real DOM/state condition over a fixed sleep**, especially wherever appliance
  timing can vary (job status, wizard-step transitions, mount/loading spinners, button-enabled
  state). Reference implementations to reuse rather than reinvent:
  - `WizardPage.click_next()` — polls `current_step_title()` until it changes, retries the click
  - `FileLevelRecoveryPage.wait_files_ready()` / `_wait_right_panel_loading_gone()` — polls a
    loading indicator's visibility
  - `DataProtectionPage.wait_for_job_status()` — polls dashboard status to a terminal state
  - `FileLevelRecoveryPage._wait_recover_enabled()` — polls a button's enabled state
- **A short fixed wait (roughly 300–2000ms) is acceptable only** for known, already-calibrated UI
  settle time after an action with no independently observable completion signal. It must be the
  *smallest* value empirically found to work, with a `CALIBRATED live YYYY-MM-DD` comment stating
  what was tried and what broke at a shorter value.
- **Extended timeouts** (e.g. 60s instead of the 10s default) require a documented, live-observed
  reason — dashboard-state lag, video-recording overhead compounding with appliance load, etc.
  Never bump a timeout "just in case" without a specific failure it's addressing; an unexplained
  timeout bump is itself technical debt.
- **Never busy-loop without a wait step inside the loop body** — every polling `while` loop in
  this codebase sleeps a fixed step (`self.wait(step)` or `self.page.wait_for_timeout(step)`)
  between condition checks.
- `visible=true` scoping is itself a targeting strategy specific to this ExtJS app (which keeps
  hidden duplicate step/dialog panels in the DOM) — scope to `.locator("visible=true")` before
  `.first`/`.last` by default; only skip it with a stated reason (e.g. checking a value that's
  identical whether visible or not).

## 13. Locator Strategy

- **All locators live in `browser/pom/common/locators.py`** — including wizard-type-specific
  ones (`FlbWizardLocators`, `BackupCopyLocators`, `FileShareBackupLocators`,
  `FileLevelRecoveryLocators` all live in this one file today, not scattered per Page Object
  file). Never write an inline XPath string literal in a test file or Page Object method body.
- **XPath only, never CSS.** This ExtJS app's class names carry unstable per-load numeric
  suffixes, CSS has no case-insensitive text match, and this project's `ci_exact()`/
  `ci_contains()` helpers rely on XPath's `translate()` to work around ExtJS's CSS
  `text-transform` breaking naive case-sensitive matches.
- **Use `ci_exact()`/`ci_contains()`** for text matching rather than a hand-rolled
  `contains(text(), ...)` — they already encode the case-insensitivity fix; don't reinvent it
  per-locator.
- **Prefer stable attributes** (`@title`, `@name`, `@role`) over positional or raw-class
  selectors where the UI actually exposes one — `RUN_BUTTON = "//*[@title='Run']"` is the
  reference pattern. **But** a documented positional selector (`//td[3]`) is the *correct*,
  deliberate choice where ExtJS's own class names are the unstable part
  (`x-grid-cell-gridcolumn-<N>`-style suffixes) — don't "clean up" a positional selector without
  reading the comment explaining why it's shaped that way first.
- **Parameterize with a `@staticmethod`** when a locator needs a runtime value
  (`sidebar_job_row(name)`, `tree_expander(label)`) — never string-format a raw XPath inline
  inside a Page Object method body.
- **Scope to `visible=true`** whenever the target page is known to render hidden duplicate panels
  (see §12) — this is a locator-construction concern as much as a waiting concern.
- **Every non-obvious locator carries a `CALIBRATED live YYYY-MM-DD against nbr-XX` comment**
  explaining the specific ExtJS quirk it works around. This project's locator file has 3+
  recorded recalibration dates for the *same* Files-step grid as the underlying build changed —
  the comment trail is what lets a future contributor tell "this looks weird but is deliberate"
  from "this is just stale."

## 14. Page Object Rules

- **One Page Object per logical page/wizard/flow** — not per DOM widget, not per individual UI
  element. `FlbWizardPage` covers the whole 6-step FLB wizard as one class because tests drive it
  as one continuous fluent chain; this is a deliberate design choice, not an SRP violation, given
  the domain (see the earlier page-object review's reasoning).
- **Every action method returns `self`** for fluent chaining; only query/predicate methods return
  a value (`bool`, `str`, `list[dict]`). This is followed with zero exceptions today — keep it
  that way.
- **No `assert`, business-logic verdicts, or `time.sleep()`/raw `page.wait_for_timeout()` calls
  inline in test files.** Waiting belongs in the POM (via `BasePage.wait()` or a calibrated
  polling method); verdicts belong in the test's own `assert`.
- **Extend the closest matching shared base** (`WizardPage`, `FileLevelRecoveryPage`) when a new
  class is structurally the same kind of thing — don't reimplement `click_next()`/`click_cancel()`
  independently. **Known existing gap**: `FileLevelRecoveryPage` does not currently extend
  `WizardPage` despite being a 4-step wizard, and reimplements a weaker local `click_next()` as a
  result — flagged in the earlier architecture review as a fix candidate, not corrected here
  (this document doesn't modify source code). New wizard-shaped classes should not repeat this
  gap.
- **Check `BasePage` and sibling classes for an existing capability before writing a new
  Playwright call.** The project's own duplication metrics (see `metrics.md`) show the cost of
  skipping this step — e.g. `BackupCopyPage`/`FlbWizardPage` ended up with several
  byte-identical methods because each wizard class was built independently.
- **Safety-fence checks live in the POM method that performs the destructive action**
  (`JobManagementPage.delete_job()`), never left for the caller to remember to check themselves.
- **Class-size guidance** (grounded in `metrics.md`'s measured averages: 134.6 lines/class,
  12.7 lines/method): a class approaching 300–400 lines, or containing a clearly-separable
  sub-concern (a wizard step's own summary panel, a distinct picker widget), should decompose its
  *methods* into smaller private steps composed by a public entry point — the
  `fill_custom_location()` decomposition this session (one ~70-line method split into 4 named
  private steps) is the reference pattern. Splitting the *class itself* is a separate, higher-bar
  decision — only justified when the sub-concern is independently reusable outside that one flow.

## 15. Helper Function Rules

- **Every suite's `_helpers.py` holds only build/run/verify orchestration specific to that
  suite's TCs** — it calls into Page Object methods, never raw Playwright (`page.locator(...)`)
  directly, and never contains a bare `assert` (assertions belong in the test file that calls the
  helper).
- **A helper is promoted to `tests/e2e/_lib/_shared_helpers.py` only when verified — via an actual
  diff, not an assumption — to be byte-identical or a strict backward-compatible superset across
  every suite that has a copy.** Document the verification in the moved function's own docstring
  (see `_shared_helpers.py`'s `run_and_wait_flb_job()`/`flr_browse()`/`verify_checksum()`
  docstrings for the reference pattern — each states exactly what was diffed and what, if
  anything, differed).
- **`build_flb_job()`-style functions stay suite-local even when similar across suites.** Real
  per-suite divergence (different job-type parameters, different optional behavior like
  inclusion/exclusion or `run_on_demand`) is expected — forcing one shared signature trades a
  small amount of duplication for a larger amount of parameter-juggling complexity. This was
  explicitly evaluated and rejected during this project's helper-architecture review; don't
  re-attempt it without new evidence the tradeoff has changed.
- **Every helper function takes `page` as its first parameter** — never a stored or global page
  reference. This keeps helpers composable and testable in isolation, and is followed with zero
  exceptions across the current 11 helper functions.
- **Suite-specific fixture constants live at the top of that suite's `_helpers.py`**, `ALL_CAPS`,
  never duplicated silently into a second suite — if two suites independently need the identical
  constant, that's itself the signal to consider promoting it (see §6, §15's promotion rule
  above).

---

## Appendix: how to use this document

- Adding a new Page Object, locator, fixture, or helper function → check the matching section
  above *before* writing it, not after.
- Reviewing a PR/change against this framework → each section above doubles as a review
  checklist; a change that violates a rule here needs either a fix or an explicit, documented
  reason it's an exception (matching this project's own established style of explaining
  deviations rather than silently allowing them).
- This document should be updated whenever a new *pattern* is deliberately established (not for
  every individual bugfix) — the goal is to keep it describing the framework's actual, current
  conventions, not an aspirational or stale ideal.
