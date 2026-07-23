# Framework guide

The practical "how do I..." reference for working in this repo. For binding execution rules
(safety fence, verdict definitions, honest-reporting requirement) see `CLAUDE.md` — this doc
doesn't repeat those, it explains the mechanics around them. For the full 15-section naming/style
standards, see `docs/framework-guidelines.md`; this doc's Best Practices section is a condensed
top-10, not a replacement.

## Architecture

Every TC's assertion is made by driving the **real NAKIVO Director web UI** with Playwright — there
is no backend RPC in the test path. The layers, thin to thick:

```
tests/e2e/test_flbv2v3_<Suite>/test_njm_<id>.py   (pytest test — build/act/assert only)
        │  uses
        ▼
tests/e2e/test_flbv2v3_<Suite>/_helpers.py         (suite-specific build/run/verify glue)
        │  uses (some suite helpers) + tests/e2e/_lib/_shared_helpers.py (generic cross-suite ones)
        ▼
browser/pom/backup_types/*.py, browser/pom/common/*.py   (Page Objects — actions, no assertions)
        │  uses
        ▼
browser/pom/base/base_page.py                      (BasePage — every raw Playwright action)
        │  uses
        ▼
Playwright (Chromium)  ──────────────────────────▶  Real Director UI (nbr-84 / nbr-5)
```

Cross-cutting concerns, not part of the vertical stack above:

- **Config**: `browser/pom/base/config.py` — typed, validated, multi-environment (`NBR_ENV`)
  credential resolution. Every layer that needs an appliance URL/credential goes through
  `load_app_config()`. See `docs/configuration.md`.
- **Fixtures**: `tests/e2e/conftest.py` — `logged_in_page` (a signed-in `page`), `flb_job_cleanup`
  (safety-fenced teardown), `nbr_config`/`nbr_config_fsb`, plus the Allure-evidence machinery
  (console/network capture, environment.properties, trace/video/screenshot attachment — see
  `docs/allure-reporting.md`).
- **Reporting**: plain `pytest` + `allure-pytest`, rendered by the Allure v3 CLI
  (`allurerc.json`). No bespoke reporting layer.
- **Diagnostics** (`browser/checks/`): standalone, non-pytest scripts — `health_check.py`
  (pre-suite gate), `framework_doctor.py` (root-cause diagnosis), `accessibility_scan.py`,
  `cleanup_auto_flb_jobs.py` (raw-RPC job sweep), and calibration scripts for a specific UI area.
  These are debugging tools, not part of the TC-verdict path.

### Page Object hierarchy

```
BasePage                              (browser/pom/base/base_page.py — every click/fill/wait/query)
├── WizardPage                        (common/wizard_page.py — shared job-wizard base)
│   ├── FlbWizardPage                 (backup_types/flb_wizard_page.py — File-Level Backup)
│   │   └── FileShareBackupPage       (backup_types/file_share_page.py — reuses FLB's wizard steps)
│   └── BackupCopyPage                (backup_types/backup_copy_page.py)
├── FileLevelRecoveryPage             (backup_types/file_level_recovery_page.py — FLR wizard, FLB source)
│   ├── FileShareRecoveryPage         (backup_types/file_share_recovery_page.py — FSB source)
│   │   └── BackupCopyRecoveryPage    (backup_types/backup_copy_recovery_page.py — provides BOTH
│   │                                  recover_file_level() and recover_file_share())
├── DataProtectionPage                (common/data_protection_page.py — Jobs list, Create menu, Recover menu)
├── JobManagementPage                 (common/job_management_page.py — Manage → Delete, safety-fenced)
└── LoginPage                         (common/login_page.py)
```

All locators live in `browser/pom/common/locators.py` as per-page-object classes (e.g.
`FlbWizardLocators(WizardLocators)`) — XPath only, using the `ci_exact()`/`ci_contains()` helpers
for case-insensitive text matching (ExtJS CSS-uppercases a lot of text, so raw-cased `text()=`
matches are unreliable).

## Folder structure

```
browser/
  config/            SECRETS fallback JSON (gitignored) — .env takes priority, see config.py
  pom/
    base/             base_page.py (actions), config.py (typed config), driver.py (browser factory), retry.py
    common/           locators.py, login_page.py, data_protection_page.py, job_management_page.py, wizard_page.py
    backup_types/     one page object per job-wizard/recovery-flow type (see hierarchy above)
  checks/             standalone diagnostic/calibration scripts (not pytest) — see Architecture above
tests/
  e2e/
    conftest.py       shared fixtures + Allure-evidence hooks (session-wide, applies to every suite)
    _lib/             framework-support Python modules that are NOT tests: _shared_helpers.py, _visual_regression.py
    test_infrastructure/   non-Jira-TC tests: test_smoke.py, test_config.py, test_visual_regression_example.py
    test_flbv2v3_<Suite>/  one folder per Jira Test Execution — __init__.py, _helpers.py, test_njm_<id>.py per TC
    __snapshots__/    visual-regression baselines (committed, not gitignored — see docs/visual-regression-pattern.md)
cases/<Suite>/        historical runbooks (pre-pytest, raw-RPC era) — fixture/pattern reference only, not executable
test-data/            environment.md (fixture source of truth), test-data.md (seeded filesets), manifests/ (checksums)
docs/                 this file + configuration.md, allure-reporting.md, framework-guidelines.md,
                       parametrize-pattern.md, xdist-parallelization.md, visual-regression-pattern.md,
                       ci-secrets.md, enterprise-gap-analysis.md
results/               allure-results/, allure-report/, test-results/ (all gitignored, regenerate freely),
                       screenshots/ (ad-hoc calibration evidence, tracked)
CLAUDE.md             binding execution rules — read before running/writing anything
allurerc.json, pyproject.toml, requirements*.txt, .pre-commit-config.yaml, Dockerfile, .env(.example)
```

## How to add a Page Object

1. **Check it doesn't already exist.** Grep `browser/pom/` for the UI area first — reuse before
   extend is Golden Rule 2 in `CLAUDE.md`.
2. **Locators go in `browser/pom/common/locators.py`**, as a new class or additions to an existing
   one. XPath only, relative (never absolute), scoped to `visible=true` when ExtJS keeps hidden
   duplicate panels in the DOM (a real, repeatedly-hit gotcha — see Common Mistakes below). Use
   `ci_exact()`/`ci_contains()` for text matching, never `get_by_text`/CSS selectors.
3. **Pick the right base class.** A new job-wizard type extends `WizardPage` (or `FlbWizardPage`
   if it's structurally identical to FLB's, like `FileShareBackupPage` is); a new recovery flow
   extends `FileLevelRecoveryPage` if it shares FLR's 4-step shape.
4. **Actions go in the page-object class**, one file under `backup_types/` or `common/`. Every
   method performs a UI action and returns page state (or `self`, for chaining) — **no
   `assert`, no business logic, no `time.sleep()`** inside a POM method (that belongs in the test).
   Prefer Playwright's own waiting; a calibrated fixed `self.wait(ms)` needs a
   `# CALIBRATED live YYYY-MM-DD` comment explaining why (see existing examples).
5. **Calibrate live** against the real appliance (nbr-84 for FLB, nbr-5 for FSB) — inspect the
   actual DOM/screenshot before writing a locator; don't guess selector text from the Jira TC
   description alone.
6. **Verify** by running the standalone script or test that exercises it, `--headed` if you're
   watching live.

## How to add a fixture

Fixtures live in `tests/e2e/conftest.py` (session-wide) or a suite's own `_helpers.py` if
genuinely suite-local (rare — most suite logic is a plain function, not a fixture).

- **Session-scoped, expensive-to-create, read-only data** (config, credentials): `scope="session"`,
  see `nbr_config`.
- **Function-scoped, per-test state** (a signed-in page, a job registered for cleanup): default
  scope, see `logged_in_page`/`flb_job_cleanup`.
- **Wrapping/extending a fixture pytest-playwright already provides** (not inventing a new name):
  redeclare the *same* fixture name and request the original as a parameter — see
  `browser_context_args` and `page` in `conftest.py` for the exact pattern. This is how the
  Allure console/network capture was added without touching every test.
- **A factory fixture** (the test calls it with arguments, e.g. `flb_job_cleanup("AUTO_FLB_...")`):
  `yield` an inner function, do teardown after the `yield` — see `flb_job_cleanup`.
- **New CLI flags** go in `pytest_addoption` (top of `conftest.py`), not scattered elsewhere.

## How to add a new test

This is the `execute-tc` skill's job when done through Claude — see
`.claude/skills/execute-tc/SKILL.md` for the full workflow. The short version:

1. Locate `tests/e2e/test_flbv2v3_<Suite>/test_njm_<id>.py`. If it exists, you're done — run it.
2. If missing, check `cases/<Suite>/NJM-<id>.md` for prior fixture/pattern context (machine names,
   drill paths) — but never trust its recorded PASS/FAIL verdict (`CLAUDE.md` Golden Rule 6).
3. Write the test in the matching suite folder, following that suite's existing pattern:
   `build_flb_job()` → `run_and_wait_flb_job()` → verify (FLR browse / checksum / dashboard state)
   → rely on `flb_job_cleanup` for teardown, never hand-rolled.
4. `pytestmark = [pytest.mark.flb, pytest.mark.<suite_marker>, pytest.mark.jira("NJM-<id>")]` —
   register any new marker in `pyproject.toml`'s `markers` list (`--strict-markers` will otherwise
   fail collection).
5. Reuse `_helpers.py`/`_shared_helpers.py` before writing new interaction code; only add a new
   POM method if the UI area is genuinely new (see "How to add a Page Object" above).
6. Name the file `test_njm_<id>.py`, the function `test_<snake_case_description>`.

If the TC doesn't fit any existing suite folder, stop and ask which suite it belongs to (or
whether a new one is warranted) rather than guessing.

## How to debug

- **`--headed`** on any `pytest` or `browser/checks/*.py` invocation — watch the browser live.
- **`python browser/checks/health_check.py`** first, whenever something seems off — an 8-check,
  <1-minute gate that tells you if it's the appliance/build/environment before you spend 3+
  minutes on a real TC only to hit the same wall.
- **`python browser/checks/framework_doctor.py`** for root-cause triage (broken locator / wrong
  selector / timeout / environment / auth / test-data / browser / Playwright-version issue).
- **Allure evidence** — every test's Allure entry carries a failure screenshot, full video,
  `trace.zip` (failures only — `playwright show-trace <file>`), console log, and network log
  automatically; see `docs/allure-reporting.md`. Check `failure-reason` first, it's the exact
  pytest assertion/traceback.
- **`--keep-failed-jobs`** — leaves a failed test's `AUTO_FLB_*`/`AUTO_FSB_*` job in place on the
  appliance for manual inspection instead of the default auto-cleanup.
- **A locator that used to work stops matching** — the ExtJS UI drifts across builds. Recalibrate
  live (open the real page, inspect the DOM/take a screenshot) and fix it in `locators.py`; never
  loosen the test's assertion to route around it, and never hardcode a workaround in the test file.
- **Job leaked on the appliance despite a PASSED test** — check the Jobs sidebar for stray
  `AUTO_FLB_*`/`AUTO_FSB_*` entries. `flb_job_cleanup` swallows its own delete exceptions
  (`except Exception: pass`) so a broken teardown fails silently — see Common Mistakes below
  (Golden Rule 8's leak chain) before assuming "PASSED" means "cleaned up."

## How to execute

```bash
# One TC (the default working mode — case-by-case, not whole-suite):
pytest tests/e2e/test_flbv2v3_IncludeExclude/test_njm_182425.py -v
pytest tests/e2e/test_flbv2v3_IncludeExclude/test_njm_182425.py -v --headed   # watch it live

# A whole suite (only when explicitly requested):
pytest tests/e2e/test_flbv2v3_IncludeExclude/ -v

# Filter by marker:
pytest tests/e2e -m inventory -v
pytest tests/e2e -m "flb and not fsb" -v

# A different environment (see docs/configuration.md — requires .env.<environment> to exist):
NBR_ENV=qa pytest tests/e2e -v

# View the report:
allure serve results/allure-results                                    # quick, ephemeral
rm -rf results/allure-report && allure generate results/allure-results  # persistent
allure open results/allure-report --port 5252
```

Lint/type-check before committing (also enforced by `.pre-commit-config.yaml` on `git commit`):

```bash
ruff check .
mypy browser tests
```

## Best practices

The condensed top-10 — full standards in `docs/framework-guidelines.md`:

1. **Reuse before you extend.** Check `browser/pom/`/`_helpers.py`/`_shared_helpers.py` before
   adding a locator, action, or helper function.
2. **Never hardcode** an appliance URL, machine name, repo name, or credential — always
   `load_app_config()` or a `test-data/*.md`-sourced constant.
3. **POM methods act; tests assert.** No `assert`, no business logic, no `time.sleep()` inside a
   page-object method.
4. **Safety fence absolute.** Only ever create/modify/delete `AUTO_FLB_*`/`AUTO_FSB_*` — discovered
   machines/repos/transporters are read-only references.
5. **One suite, one `_helpers.py`.** Cross-suite sharing only for functions verified byte-identical
   (or a strict superset) across every suite that had a copy — see `_shared_helpers.py`'s own
   docstring for the bar.
6. **Calibrate live, don't guess.** A locator/timing value is only trustworthy after being
   confirmed against the real running appliance.
7. **Fail loud, not quiet.** Never loosen an assertion to force green; a genuine product finding
   is more valuable than a passing test that proves nothing.
8. **Let `flb_job_cleanup` handle teardown** — don't hand-roll cleanup in a test body.
9. **One test file per TC, one TC per test file — no exceptions**, even for byte-identical bodies
   differing only in fixture data (a real prior attempt at consolidating those was reversed — see
   `docs/parametrize-pattern.md`). `@pytest.mark.parametrize` is still fine *within* a single TC's
   own file (e.g. testing the same TC at two values), just never to span multiple Jira TCs.
10. **Case-by-case execution is the default.** Run one TC at a time unless a batch run is
    explicitly requested — easier to debug, avoids long unwatched runs.

## Common mistakes

Real issues this project has actually hit — not generic advice. This is the curated, prose
version of the handful of costliest findings; `CALIBRATION_LOG.md` (repo root) is the complete,
dated, one-line-per-entry index of every `CALIBRATED live` comment in the codebase — check it
before assuming something's unexplained UI behavior is new.

- **ExtJS keeps hidden duplicate panels in the DOM.** A locator that matches >1 element (one
  visible, others hidden leftovers from a prior step/dialog) silently interacts with the wrong
  one. Scope to `.locator("visible=true")`, and don't assume `.count() == 1` without checking.
- **`.fill()` doesn't always update an ExtJS component's internal state.** Some ExtJS-backed
  fields need a real keystroke event (or a deliberate blur/change trigger) before the component
  registers the new value — a `.fill()` that "looks" like it worked (the DOM shows the text) can
  still leave the underlying form invalid. This caused a genuinely long CIFS-credential debugging
  session earlier in this project's history; if a field's value doesn't seem to "stick" from the
  wizard's perspective, suspect this before anything else.
- **Positional locators (e.g. `/td[3]`) are sometimes the *correct*, calibrated choice** — ExtJS
  generates class names with unstable per-load numeric suffixes
  (`x-grid-cell-gridcolumn-<N>`-style). Don't "clean up" a positional selector without reading the
  comment explaining why it's there; it may be the only stable option.
- **Case-sensitive text matching breaks on ExtJS's CSS-uppercased labels.** `text()='Log In'` fails
  against a button whose rendered text is uppercased by `text-transform` — use `ci_exact()`.
- **Never run 2+ jobs against the same source VID concurrently** — they lock/stall rather than
  queue. Suites with a shared source (see `_helpers.py` module docstrings, e.g. two Inventory TCs
  both on `Linux_16.84`) must run sequentially; this is also why `pytest-xdist` isn't enabled by
  default (see `docs/xdist-parallelization.md`).
- **A "PASSED" test doesn't guarantee its job was actually cleaned up.** Any FLR flow that
  *executes* a recovery (not just browses one) can leave the wizard on a step whose Cancel button
  doesn't exist (e.g. step 4's Finish/Close instead of Cancel) — calling `click_cancel()` there
  silently times out, leaving the wizard open, which then breaks `flb_job_cleanup`'s own
  `delete_job()` call — and *that* failure is swallowed too (`except Exception: pass`). This
  leaked 14 jobs across a suite before being caught. Any new execute-a-recovery-type flow must
  confirm it returns to a state where the Jobs sidebar is reachable — don't just trust green.
- **A historical `cases/*.md` runbook's verdict is not ground truth.** It came from a retired
  raw-RPC execution path with its own independent tooling defects — let the new UI-driven test's
  own result stand alone.
- **Moving a Python file to a new folder depth breaks any `Path(__file__).resolve().parent...`
  chain that wasn't updated to match** — this project hit this for real: a file moved one level
  deeper during a folder reorg kept its old `.parent` count, silently pointing `MANIFESTS_DIR` at
  a nonexistent directory. Any file move needs every relative-path computation in that file
  checked, not just its imports.
- **A hook-local variable isn't automatically in `pytest`'s `item.funcargs`.** Only fixtures
  actually named as a parameter somewhere in the test's requested fixture chain appear there —
  `pytest-playwright`'s own `output_path` fixture (needed to locate `video.webm`/`trace.zip` for
  Allure attachment) silently returned `None` via `item.funcargs.get("output_path")` until a
  fixture explicitly requested it. If a hook-based lookup of "some fixture's value" is quietly
  returning `None`/empty, check whether anything in the actual dependency chain named it directly.
- **`override=False` in `python-dotenv`'s `load_dotenv()` means "skip a key already in
  `os.environ`" — load order determines precedence, not file priority intuition.** To make an
  overlay file win over a base file (while still losing to a real shell/CI var), load the overlay
  *first*, not last — see `config.py`'s `.env.<environment>`-then-`.env` order and comment.
- **Deleting/regenerating `results/allure-report` while a persistent `allure open --port <N>`
  server is already running against it leaves that server serving stale/broken state** (a `404`
  with no visible error) — kill and restart the server after any manual `rm -rf
  results/allure-report && allure generate ...`, don't assume the running viewer picks up changes.
