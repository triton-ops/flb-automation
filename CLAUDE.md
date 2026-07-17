# Execution rules — FLB automation (read before running any case)

These are binding rules for Claude when generating or executing a file-level backup test case.

Architecture: every job build, run, and File-Level Recovery verification goes through the real
Director web UI via the Playwright Page Object Model in `browser/pom/`, driven by pytest tests
under `tests/e2e/`. **No backend RPC in the test path.** See `README.md` and the `execute-tc`
skill (`.claude/skills/execute-tc/SKILL.md`) for the full workflow.

## Golden rules

1. **Single source of truth.** All fixtures (appliance URLs, machine display names, repo names,
   seeded paths, credentials) come from `test-data/environment.md`, `test-data/test-data.md`, and
   `.env` (`NBR_FLB_URL/USER/PASS`, `NBR_FSB_URL/USER/PASS`). Never hardcode addresses, paths, or
   credentials in a test.
2. **Reuse before you extend.** Before adding a new POM locator/action or duplicating build/run/
   verify logic in a test, check whether `browser/pom/` or the suite's `_helpers.py`
   (`build_flb_job()`, `run_and_wait_flb_job()`, `flr_browse()`, `extract_item_names()`,
   `verify_checksum()` for real SHA-256 content verification — see `browser/pom/common/checksum.py`)
   already covers it. The ExtJS UI can drift across builds — if a locator/action stops working,
   recalibrate it live (inspect the real DOM/screenshot) and fix it in the POM layer
   (`browser/pom/common/locators.py`, `backup_types/*`), never by hardcoding XPath in a test or
   loosening an assertion to route around it.
3. **Safety fence.** Only ever create/modify/delete entities whose name starts with
   `AUTO_FLB_` (FLB and Backup Copy, both on `nbr-84`) or `AUTO_FSB_` (File Share Backup, on
   `nbr-5`) — see `test-data/environment.md` for the naming convention. The discovered
   machines, repositories, and transporters are **read-only references** — never delete or
   edit them. Never touch a job you didn't create.
4. **Evidence always.** Every test run's pass/fail is backed by its pytest assertion output, plus
   an Allure record (`results/allure-results/`, `--alluredir`) carrying: a failure screenshot
   (auto-attached on FAIL), and a full-session video recording (`--video=on`, attached to every
   run — pass or fail — named `NJM-<id>_<test function name>-video`). See `tests/e2e/conftest.py`'s
   `pytest_runtest_makereport` hook.
5. **Honest reporting.** If a step fails, report FAIL with the real pytest assertion message —
   never paper over it or loosen the assertion to force green. If a step is skipped, say so and
   why. Don't claim PASS without the test's actual verification assertion (FLR-browse content
   match, dashboard status) succeeding.
6. **A historical runbook's verdict is not ground truth.** `cases/<Suite>/NJM-<id>.md` runbooks
   predate this architecture (raw-RPC execution) and may hold useful fixture/pattern context
   (machine names, drill paths), but their recorded PASS/FAIL came from a different execution path
   with its own independent tooling defects. Never assume an old verdict still holds — let the new
   UI-driven test's own result stand on its own (e.g. `NJM-182426` was originally recorded FAIL due
   to an RPC-era FLR-browse tooling bug, not a product defect; the UI-driven re-run passes).
7. **Stop on hard failure.** If a step's precondition fails (e.g. source machine unreachable, repo
   inaccessible), stop and report BLOCKED rather than pushing ahead.
8. **A test reporting PASS does not mean its job actually got cleaned up — verify it.** Any FLR
   flow that *executes* a recovery (not just browses one — e.g. `download_selected()`'s Download
   recovery type) leaves the wizard on step 4 (Finish), which has a `Close` button, not `Cancel`.
   Calling `click_cancel()` there silently times out and does nothing, leaving the wizard open —
   which then breaks the `flb_job_cleanup` teardown's own `jm.delete_job()` call (the Jobs
   sidebar isn't reachable from an open wizard), and that failure is itself silently swallowed
   (`except Exception: pass`). This exact chain leaked 14 `AUTO_FLB_*` jobs across the Inventory
   suite before being found — every checksum-verifying test reported PASS while leaking its job.
   `download_selected()` now calls `_close_finish_step()` to close via 'Close', but the lesson
   generalizes: any new POM flow that executes (not just browses) must confirm it returns to a
   state where the Jobs sidebar is reachable, and don't just trust a green pytest result as proof
   cleanup happened — spot-check the Jobs sidebar for `AUTO_FLB_*`/`AUTO_FSB_*` leftovers
   periodically, especially after adding a new execute-a-recovery-type flow.

## Standard lifecycle of a case

1. **Locate** — search `tests/e2e/test_flbv2v3_*/test_njm_<id>.py`. If it exists, run it as-is.
2. **If missing** — check `cases/<Suite>/NJM-<id>.md` for prior fixture/pattern context (see Golden
   Rule 6), then Jira (`mcp__jira__get_issue`) if needed, and write the test following the existing
   suite pattern (build via wizard POM → run → verify via FLR browse/dashboard status → rely on
   `flb_job_cleanup` for teardown).
3. **Execute** — `pytest tests/e2e/test_flbv2v3_<Suite>/test_njm_<id>.py -v` (one file at a time by
   default; add `--headed` to watch live). Backup runs are async — `run_and_wait_flb_job()` polls
   the job dashboard on a sane interval (10–30s); don't busy-loop, and size the timeout to the
   seeded fileset (small — a few minutes is enough).
4. **Verify** — read the real pytest PASSED/FAILED line and assertion message; cross-check the
   Allure result JSON if needed. "The wizard advanced" / "job reached a non-error state" is not
   verification by itself — the FLR-browse content assertion (or documented UI-state check) is
   what determines the verdict.
5. **Report** — per the `execute-tc` skill's Output Format: TC summary, test location, execution
   command + result, verification detail, root-cause on FAIL (Product / Automation / Environment /
   Test-data), cleanup confirmation.
6. **Cleanup** — automatic via the `flb_job_cleanup` fixture (always runs, pass or fail, unless
   `--keep-failed-jobs` is passed to leave a failed job in place for inspection). This can fail
   silently (see Golden Rule 8) — don't assume a PASSED test means its job is gone; check the
   Jobs sidebar if in doubt, especially for a test that executes (not just browses) a recovery.

## Verdict definitions

- **PASS** — the job reached `Successful` on its dashboard, and the test's own verification
  assertion (FLR-browse listing match, or a documented UI-state check) actually passed.
- **FAIL** — any expected step did not meet its expectation; the real assertion message and (for a
  UI issue) the auto-attached failure screenshot/video are the evidence — never a silently
  loosened assertion to force a PASS.
- **BLOCKED** — a precondition was not met (source machine unreachable, repo inaccessible) — an
  environment issue, not a product defect.

## Reporting

- Allure is the reporting system (`results/allure-results/`, wired via `pyproject.toml`'s
  `--alluredir`) — no bespoke reporting layer. View with `allure serve results/allure-results` (quick,
  ephemeral) or generate+serve a persistent local copy — see `README.md`'s Usage section for the
  exact commands (`allure generate` + `allure open --port <N>`).
- Every test's video is attached automatically; no extra flag needed per run.

## Secrets

Never print credentials. `.env` (gitignored; see `.env.example`) holds `NBR_FLB_URL/USER/PASS` and
`NBR_FSB_URL/USER/PASS`, loaded via `browser/pom/base/config.py`'s `load_app_config()` — a typed,
validated, multi-environment config system (`NBR_ENV` switches environments; see
`docs/configuration.md`). Never hardcode a credential in a test or POM method.
