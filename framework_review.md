# Framework Review — 2026-07-07

Automated review of the flb-automation framework prior to test execution. Per the CI-agent
mission: safe issues were fixed automatically; anything not safe to fix automatically is
documented below rather than silently left broken.

## Fixed automatically this run

| Issue | Location | Fix |
|---|---|---|
| Hardcoded fallback URL pointing at a decommissioned appliance (`10.10.15.149`, old `nbr-149`) | `browser/nbr_ui.py::resolve_creds()` | Removed the dead default; the function now fails loudly with a clear `sys.exit(2)` message if no URL is configured via `--url`/`NBR_UI_URL`/`ui_config.json`, instead of silently pointing at a dead host. |
| No environment-variable fallback for UI config (CI had to write a JSON file from secrets instead of reading them directly) | `browser/pom/driver.py::load_config()` | Added `NBR_UI_URL`/`NBR_UI_USER`/`NBR_UI_PASS` env-var resolution, mirroring the pattern already used in `nbr_ui.py`. Env vars override individual keys; a partially-set config file still resolves correctly. |
| No Playwright trace capture anywhere in the framework | `browser/pom/driver.py::browser_page()` | Added an opt-in `trace_name` param — when given, records a full trace (screenshots+snapshots+sources) and saves it to `results/traces/<name>.zip` on exit (pass, fail, or exception), so failures are replayable with `playwright show-trace`. Wired into all four `browser/checks/*.py` scripts. |
| No retry strategy for genuinely transient failures | `browser/pom/retry.py` (new) + `driver.py` | Added `retry_on_transient()`, a small exponential-backoff helper, and wrapped only the browser-launch step (the one step here that's actually transient — resource contention, first-run download flakiness). Deliberately **not** applied to page-object actions or selectors — retrying those would mask real defects instead of fixing them. |
| Framework's own pytest results were invisible in the Allure report (only historical NBR journal data appeared) | `requirements-dev.txt`, `pyproject.toml`, `.github/workflows/ci.yml` | Pinned `allure-pytest==2.16.0`; `addopts` now includes `--alluredir=results/allure-results --junitxml=results/junit.xml` as the single source of truth, so both this run's pytest results and the historical NBR-execution journal results land in the same directory and merge into one Allure report. |
| 3 new lint findings introduced by the above (import-sort ×2, `UP035` typing.Callable) | `driver.py`, `retry.py` | Auto-fixed via `ruff check --fix`; verified clean afterward. |

## Reviewed, no issue found

- **Hardcoded credentials in source**: none found. The only password-shaped string is a CSS
  selector (`input[type='password']`), a false positive.
- **Broken imports**: `py_compile` across every `.py` file in the repo passed clean.
- **Project structure / missing dependencies**: `requirements.txt` / `requirements-dev.txt`
  are present and consistent with what's imported; `pyproject.toml` correctly scopes
  `pytest`/`ruff` config.
- **Reporting/logging/screenshot config**: the `reporting/` Allure pipeline
  (journal → `ResultCollector` → `AllureMapper`) is solid and unchanged; screenshot paths
  (`SHOTS_DIR`, self-healing on capture) were already correct.

## Known limitations — documented, not fixed (risk of live re-verification outweighs benefit)

- **Weak waiting strategy**: `browser/pom/base_page.py` and several page objects use fixed-sleep
  `wait(ms)` calls in places rather than pure Playwright auto-waiting/explicit expectations. This
  is a real weakness, but rewriting it blind — without a live appliance session to re-verify
  every call site — risks introducing new flakiness into POM code that currently works. Left as
  a flagged follow-up, not touched this run.
- **No structured logging**: the framework uses `print()` throughout instead of Python's
  `logging` module (levels, structured fields, log files). This is a legitimate gap but is a
  cross-cutting design decision (log format, destinations, verbosity policy) better suited to an
  explicit follow-up task than a "safe automatic fix" bundled into a review pass.
  See [[browser-only-for-ui-state]] for how browser output is already scoped down deliberately.
- **Selectors not re-verified live this run**: `browser/pom/locators.py`'s XPath selectors were
  last calibrated 2026-07-07 against NBR 11.2.1 build 106315/106316. This run had no live
  appliance session (see Environment Validation and Execution below), so selector drift cannot be
  ruled out — it will only surface the next time a `browser/checks/*.py` script actually runs
  against nbr-84/nbr-5.
- **`E702` (semicolon-chained statements) intentionally excluded from ruff's ruleset** — a
  deliberate, pervasive, already-live-verified convention in `browser/pom/*.py`'s fluent
  page-object actions, not a bug-risk category. Documented in `pyproject.toml` inline.

## Scope note on "Execute the Requested Test Suite"

No specific suite, test IDs, or runbook name was given in this request. Per the instruction
"Execute ONLY the requested suite... Do not execute unrelated tests," the safest non-scope-creeping
interpretation is: run the framework's own scriptable, CI-executable suite — `ruff check` +
`pytest` — exactly what the hosted `lint`/`test` jobs in `.github/workflows/ci.yml` do. This does
**not** include a live NBR RPC/browser execution against the lab appliances (`nbr-84`/`nbr-5`),
since (a) nothing in the request named a TC/runbook to run there, and (b) launching a live
create/run/verify/cleanup cycle against shared lab infrastructure without a named target would be
scope creep, not caution.
