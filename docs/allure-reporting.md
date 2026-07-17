# Allure reporting — what's automatically attached, and why

Every mechanism below is wired into `tests/e2e/conftest.py` (or `pyproject.toml`'s `addopts`) —
nothing needs to be called per-test unless noted. See `docs/configuration.md` for the config
system referenced throughout, `docs/xdist-parallelization.md`/`docs/visual-regression-pattern.md`
for unrelated conftest.py features.

| Requirement | Mechanism | Scope |
|---|---|---|
| Screenshots | `pytest_runtest_makereport`, full-page PNG | on failure only — a passing test's video already covers its whole run |
| Videos | `--video=on` (pytest-playwright) + `pytest_runtest_makereport` attaches `video.webm` | every test, pass or fail |
| Trace.zip | `--tracing=retain-on-failure` (pytest-playwright) + `pytest_runtest_makereport` attaches it | on failure only (that's what `retain-on-failure` means — see pyproject.toml's comment) |
| Console log | `page` fixture override registers a `console` listener | every test that uses `page` (directly or via `logged_in_page`) |
| Network log | same `page` fixture override, `request`/`response` listeners | same as console log |
| Execution time | native Allure feature (every test result carries start/stop timestamps) | automatic, no code needed |
| Environment | `pytest_sessionstart` writes `results/allure-results/environment.properties` | once per session |
| Browser | same `environment.properties` (`Browser=Chromium <playwright version>`) | once per session |
| Machine | same `environment.properties` (`Machine=<hostname> (<OS> <release>)`) | once per session |
| Test data | `_shared_helpers.py`'s `attach_test_data()`, called from each suite's `build_flb_job()` | every test that builds an FLB job (all 3 ported suites) |
| Job name | same `attach_test_data()` call — also sets an Allure `job_name` label (filterable/searchable) | same as test data |
| Failure reason | native Allure feature (assertion message + traceback in the test body) **plus** an explicit `failure-reason` text attachment (`rep.longreprtext`) for visibility even in a collapsed/summary view | on failure only |

## Console log / network log — how it's captured

Python Playwright has no built-in "attach this to my test runner" hook for console/network
activity, so `conftest.py` overrides pytest-playwright's own `page` fixture (the same "wrap and
extend" pattern already used for `browser_context_args`):

```python
@pytest.fixture
def page(page, request):
    console_log, network_log = [], []
    page.on("console", lambda msg: console_log.append(f"[{msg.type}] {msg.text}"))
    page.on("request", lambda req: network_log.append(f"--> {req.method} {req.url}"))
    page.on("response", lambda res: network_log.append(f"<-- {res.status} {res.url}"))
    request.node.stash[_CONSOLE_LOG_KEY] = console_log
    request.node.stash[_NETWORK_LOG_KEY] = network_log
    return page
```

Every test that requests `page` (directly, like `test_smoke.py`, or indirectly via
`logged_in_page`) gets this automatically — no per-test wiring. A pure-logic test that never
requests `page` at all (e.g. `test_infrastructure/test_config.py`) never triggers browser
creation just for this — the fixture is lazy, same as pytest-playwright's own `page`.

The collected lists are stashed on the test item (`pytest.StashKey`, not a global) and attached in
`pytest_runtest_makereport`'s teardown phase, alongside the video.

## Environment / Browser / Machine — `environment.properties`

Allure v3's Awesome report reads the classic Allure 2-era `environment.properties` file (plain
`KEY=VALUE` lines) dropped directly in `results/allure-results/` — verified against the installed
`allure` v3 CLI's own Allure2-compat reader
(`@allurereport/reader/dist/allure2/index.js`'s `processEnvironment`). `pytest_sessionstart`
writes this file fresh at the start of every session using `browser/pom/base/config.py`'s
`load_app_config()` (so `NBR_ENV`/the resolved appliance URL is always the real, current value —
never hardcoded) plus `platform`/`importlib.metadata` for the browser/machine/Python info.

This file is written once per session (these values don't vary test-to-test), not per test.

## Test data / job name

`tests/e2e/_lib/_shared_helpers.py`'s `attach_test_data(job_name=None, **fields)` attaches a JSON
blob of whatever parameters the test actually used (machine, drill path, checks, inclusion/
exclusion, repository, etc. — whatever the suite's own `build_flb_job()` was called with) and, if
a `job_name` is given, also sets it as a searchable Allure **label** (`job_name`) — so the Allure
report can filter/group by the exact `AUTO_FLB_*`/`AUTO_FSB_*` job a test created, useful when
cross-referencing against the Jobs sidebar or a `cleanup_auto_flb_jobs.py` dry-run.

Each of the 3 ported suites' `build_flb_job()` calls this once, right after receiving its
parameters — this is suite-specific glue code (same reason `build_flb_job()` itself isn't in
`_shared_helpers.py` — see that module's own docstring), calling the one shared, generic
attachment utility.

## Failure categorization

Allure v3's Awesome report ships built-in "Product errors" (status: failed — an assertion didn't
hold) vs "Test errors" (status: broken — an exception was raised outside the assertion itself,
e.g. a POM method threw) categories automatically, with no config needed — verified live (see
Verification below).

This is a coarse, mechanical split, not a replacement for `CLAUDE.md`'s own root-cause
classification (Product / Automation / Environment / Test-data) — that judgment (is this actually
a NBR product defect, or a POM locator bug, or the appliance being unreachable, or bad seeded test
data?) still requires a human or agent reading the actual failure, per the project's existing
"Honest reporting" rule. The `failure-reason` attachment above exists specifically to make that
judgment call easy to make from the report alone, without needing to re-run the test.

## Verification

- `ruff check .` / `mypy browser tests` — clean.
- A deliberate throwaway failing test confirmed: `failure-screenshot`, `failure-reason`,
  `console-log`, `network-log`, `<test>-video`, and `<test>-trace` all appear as real Allure
  attachments (not just written to disk unattached) — a genuine `Invalid NBR_FLB_URL` style
  `ConfigError` message was clearly readable from the `failure-reason` attachment alone.
- A real passing suite test confirmed: video + console log + network log + test-data attachment +
  `job_name` label all appear, and `results/allure-results/environment.properties` was written
  with the real current `NBR_ENV`, appliance URL, browser, and machine values.
- The generated report's Categories tab showed "Product errors" for the deliberate assertion
  failure, confirming Allure's built-in categorization needs no extra config.
