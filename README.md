# flb-automation

Playwright + pytest test automation for NAKIVO B&R — **File-Level Backup** (physical machine)
coverage, driven entirely through the real Director web UI. Every job build, run, and File-Level
Recovery verification goes through the browser POM in `browser/pom/`; **no backend RPC** in the
test path (that was the previous architecture — see "History" below).

Repo: https://github.com/triton-ops/flb-automation (private)

## The flow

```
You: "run NJM-1234"
        │
        ▼
1. Claude locates tests/e2e/test_flbv2v3_<Suite>/test_njm_1234.py (one file per Jira TC).
   If it doesn't exist yet, checks cases/<Suite>/NJM-1234.md for a prior runbook/verdict
   (fixture paths, machine names) to inform a new test, following the existing suite pattern.
2. Claude runs the single test file — `pytest tests/e2e/test_flbv2v3_<Suite>/test_njm_1234.py -v`
   — never the whole suite unless a batch run is explicitly requested. Every step (open the
   FLB wizard, build the job, run it, browse the recovery point via File Level Recovery) drives
   the actual Director UI through browser/pom/'s Page Object Model.
3. Claude reads the real pytest pass/fail output and reports honestly — a documented product
   finding (even an unexpected one) is reported as such, never silently worked around to force
   a green checkmark.
4. Cleanup is automatic: the flb_job_cleanup fixture removes the AUTO_FLB_* job it created,
   pass or fail, unless --keep-failed-jobs is passed.
```

See the **`execute-tc`** skill (`.claude/skills/execute-tc/SKILL.md`) for the full step-by-step
workflow Claude follows, and **`review-refactor-test`**
(`.claude/skills/review-refactor-test/SKILL.md`) for the checklist used when reviewing/refactoring
existing tests.

## Layout

| Path | What |
|---|---|
| `CLAUDE.md` | Binding execution rules — read before running anything |
| `docs/framework-guide.md` | **Start here for contributing**: architecture, folder structure, how to add a Page Object/fixture/test, how to debug/execute, best practices, common mistakes |
| `CALIBRATION_LOG.md` | Dated index of every `CALIBRATED live` finding across the codebase (file:line + one-liner, not a copy) — "what's flaky/surprising and why, and where" without grepping the whole tree |
| `docs/` (other files) | `configuration.md`, `allure-reporting.md`, `framework-guidelines.md` (full naming/style standards), `parametrize-pattern.md`, `xdist-parallelization.md`, `visual-regression-pattern.md`, `ci-secrets.md`, `enterprise-gap-analysis.md` |
| `.claude/skills/execute-tc/` | How Claude locates, writes, and runs a TC's pytest test |
| `.claude/skills/review-refactor-test/` | Checklist for reviewing/refactoring existing tests |
| `.env` (gitignored, from `.env.example`) | `NBR_FLB_URL/USER/PASS`, `NBR_FSB_URL/USER/PASS` — loaded by `browser/pom/base/config.py`'s typed, multi-environment `load_app_config()` (`NBR_ENV` switches environments — see `docs/configuration.md`) |
| `.venv/` (gitignored) | Project virtualenv — see Setup below |
| `test-data/environment.md` | Connection fixtures (appliances, source machines, repos) |
| `test-data/test-data.md` | Seeded filesets + checksum manifests (the FLR verification oracle) |
| `test-data/manifests/` | Per-host SHA-256 + MD5 checksum manifests |
| `browser/pom/` | Playwright Page Object Model — `common/` (login, job list, wizard base, FLR, `checksum.py`'s manifest parsing + hashing for content-integrity checks), `backup_types/` (FLB wizard, FLR flow incl. Download recovery + file selection), `base/` (BasePage action wrappers, `browser_page()` driver factory) |
| `browser/checks/` | Standalone calibration/regression scripts exercising the POM directly (not pytest) — useful for live debugging a specific UI area |
| `browser/config/` | Legacy JSON config fallback (`ui_config*.json`, gitignored) — `.env` takes priority when both are present |
| `tests/e2e/conftest.py` | Shared fixtures: `logged_in_page`, `flb_job_cleanup` (auto job teardown), `nbr_config`/`nbr_config_fsb`, `--keep-failed-jobs`/`--visual-update-snapshots` CLI flags; `pytest_runtest_makereport` hook attaches a failure screenshot and every test's recorded video to its Allure entry |
| `tests/e2e/_lib/` | Framework-support Python modules shared across suites (not tests themselves): `_shared_helpers.py` (cross-suite build/run/verify helpers), `_visual_regression.py` (Pillow-based snapshot-diff helper) |
| `tests/e2e/test_infrastructure/` | Non-Jira-TC infrastructure tests: `test_smoke.py` (fixture-chain smoke test), `test_visual_regression_example.py` (visual-regression pattern demo — see `docs/visual-regression-pattern.md`) |
| `tests/e2e/test_flbv2v3_IncludeExclude/` | 21 TCs (NJM-182720) — Inclusion/Exclusion filter rules, one `test_njm_<id>.py` per TC, shared `_helpers.py` |
| `tests/e2e/test_flbv2v3_Inventory/` | 17 TCs (NJM-182726) — OS/filesystem support end-to-end workflow; one `test_njm_<id>.py` per TC except the 4 Linux-OS-matrix TCs (67806/67807/67808/67809), consolidated into one parametrized file — see `docs/parametrize-pattern.md` |
| `tests/e2e/test_flbv2v3_FLRFunctional/` | 5 TCs (NJM-182725) — FLR wizard functional coverage (E2E recovery, Backup/Files step selection, large subfolder count, Download recovery type), one `test_njm_<id>.py` per TC, shared `_helpers.py` |
| `cases/<Suite>/NJM-*.md` | Historical runbooks — some predate the pytest port (raw-RPC era) and are kept as fixture/pattern reference, not executable |
| `results/allure-results/` | Raw Allure result JSON + attachments (screenshots, per-test `.webm` videos), written by every pytest run (`--alluredir`, gitignored) |
| `results/allure-report/` | Static HTML report generated from `results/allure-results/` (`allure generate`, gitignored) — see Usage below for how it's kept live on a local port |
| `results/test-results/` | pytest-playwright's raw per-test artifact staging dir (`--output`) — videos/traces/screenshots before they're copied into `results/allure-results/`; gitignored, safe to delete between runs |
| `results/screenshots/` | Ad-hoc calibration screenshots (failure screenshots now go straight to Allure instead) |
| `requirements.txt`, `requirements-dev.txt` | Pinned runtime (Playwright) / dev (`pytest`, `pytest-playwright`, `pytest-rerunfailures`, `allure-pytest`, `python-dotenv`, `ruff`, `mypy`, `pre-commit`, `Pillow`, `axe-playwright-python`) dependencies |
| `requirements-lock.txt` | Full transitive-dependency snapshot (`pip freeze`) for byte-for-byte environment reproduction — regenerate after changing the files above |
| `pyproject.toml` | pytest config (`--alluredir`, `--video=on`, `--output=results/test-results`, markers) + ruff/mypy config |
| `allurerc.json` | Allure v3 CLI config (auto-discovered) — report output dir, `historyPath` for trend graphs (see Usage below) |
| `Dockerfile`, `.dockerignore` | Best-effort container image — **unverified**, no Docker daemon was available to build-test it (see the Dockerfile's own header comment) |
| `.pre-commit-config.yaml` | Local ruff enforcement on commit (`pre-commit install`) — matches `pyproject.toml`'s `[tool.ruff]` config exactly |
| `.github/workflows/ci.yml` | Two-tier CI: `lint-and-collect` runs on every push/PR (GitHub-hosted, no secrets); `e2e-appliance` is manual/opt-in and **unverified** — see `docs/ci-secrets.md` |
| `recipes/file-backup-recipes.md` | **Historical reference only** — documents the old raw-RPC (`mcp__nbr__call`) workflow this project used before the Playwright pivot. No test code calls into it. |

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate        # Windows Git Bash; use .venv\Scripts\activate.ps1 for PowerShell
pip install -r requirements-dev.txt
python -m playwright install chromium

cp .env.example .env                 # fill in NBR_FLB_URL/USER/PASS (+ NBR_FSB_* if using FSB)
```

## Environment (summary — details in `test-data/environment.md`)

- **Two appliances (NBR 11.2.1):** `nbr-84` (10.10.16.84) = **FLB** (all current suites target
  this one), `nbr-5` (10.10.15.5) = **File Share Backup** (config wired, no suite ported yet).
- FLB sources on `nbr-84` span many discovered physical machines (Windows 10/11/Server
  2016/2019/2022/2025, and a wide Linux fleet — Rocky/Debian/Ubuntu/RHEL/SLES/AlmaLinux) — see
  `test-data/environment.md` for the current machine → UI-display-name → VID mapping.
- Seeded fixture convention: `C:\TestData_ForFLB\` (Windows) / `/TestData_ForFLB/` (Linux), with
  an `IncludeExclude\` subtree (one folder per filter-rule TC) and a `MixedTypes\` subtree
  (7-file mixed-type set, same shape across every OS) — see `test-data/test-data.md`.
- Jobs named `AUTO_FLB_<JIRA-ID>` (safety fence — the POM refuses to delete anything else).

## Coverage

| Suite | TCs | Jira Test Execution | Status |
|---|---|---|---|
| `test_flbv2v3_IncludeExclude/` | 21 | NJM-182720 | **All 21 live-verified**: 20 PASS (182424–182431, 185011–185014, 185017–185023) + 1 with documented spec deviations (185015: 2 unenforced parameter-limit gaps; 185016b: a documented, deliberate FAIL) |
| `test_flbv2v3_Inventory/` | 17 | NJM-182726 | **All 17 live-verified PASS** (real SHA-256 content verification via `verify_checksum()`, not just filename-listing, on every TC where a manifest exists) |
| `test_flbv2v3_FLRFunctional/` | 5 | NJM-182725 | **All 5 live-verified PASS** — FLR wizard E2E recovery to CIFS, Backup/RP step selection, Files step browse/select, large-subfolder-count recovery, Download-to-browser recovery type |
| File Share Backup / Backup Copy | — | — | Not yet ported to this framework |

**A historical `cases/*/NJM-*.md` runbook's recorded PASS/FAIL verdict is workflow/fixture
reference only, never ground truth for the new UI-driven test** — it came from the retired raw-RPC
execution path, which had its own tooling defects independent of the product. Let each new test's
own result stand on its own; don't assume an old verdict still holds.

Known product findings surfaced by this suite (not automation bugs — see the relevant test's
docstring for detail):
- `NJM-182426` — the historical raw-RPC investigation attributed an empty FLR listing to a product
  defect (FLR directory listing returning empty for nested-subfolder content under an active
  Inclusion filter). The UI-driven re-run passes cleanly: the real root cause was a POM bug
  (`RIGHT_PANEL_ROW` locator only matched folder rows, silently missing every file row — fixed in
  `browser/pom/common/locators.py`), not a product defect.
- Several PENDING-status TCs (never executed under the old workflow) found spec-vs-actual gaps
  in this build: no visible red-highlight/"Invalid parameters" message for a rejected entry (only
  a behavioral Next-block), no enforced 5000-character textarea cap or Linux 4095-char per-path
  cap (Windows' 255-char per-path cap IS enforced — an asymmetry), and more permissive
  intermediate-path-segment wildcard handling than spec describes — see
  `test_flbv2v3_IncludeExclude/test_njm_185014.py`, `test_njm_185015.py`, `test_njm_185016.py`.

Automation bugs found and fixed while live-verifying `test_flbv2v3_Inventory/` for the first time
(none were product defects):
- Every Linux-source FLR browse across both suites needed a `"root"` top-level tree segment that
  none of the original path constants included (the FLR left tree's top node is a generic `root`
  container, not literally the `/root` home directory — confirmed even for a non-`/root` source
  like a mounted `/mnt/xfs_testdata` volume). Fixed in `IE_LINUX_FLR_PREFIX` and per-test paths.
- `NJM-68916`'s non-`C:` wizard volume picker labels (`"FAT16 (E:)"`, `"New Volume - REFS (E:)"`,
  etc.) were undiscovered until this run; the FLR tree still uses the bare drive letter.
- `NJM-67816`/`NJM-67817` found unrelated leftover debris (`Folder_test2`/`Folder_test1`, dated
  weeks before the `MixedTypes` fixture was seeded) sitting inside two Ubuntu Desktop sources'
  fixture directories — removed via SSH with explicit per-action authorization (CLAUDE.md's
  read-only-machines rule otherwise blocks this).
- **Every** `verify_checksum()`-calling test silently leaked its `AUTO_FLB_*` job despite
  reporting PASS: executing a Download recovery advances the FLR wizard to step 4 (Finish),
  which has a `Close` button, not `Cancel` — the old code only called `click_cancel()`
  afterward, which silently timed out and left the wizard open, which in turn broke every
  subsequent `flb_job_cleanup` teardown (the Jobs sidebar wasn't reachable, and the exception
  was swallowed). Fixed via `FileLevelRecoveryPage._close_finish_step()`, called automatically
  at the end of `download_selected()`. 14 already-leaked jobs were manually cleaned up after
  the fix; confirmed live that new runs now clean up correctly.

## Usage

Give Claude a Jira TC id (e.g. *"run NJM-182425"*). Claude follows the `execute-tc` skill: locate
or write `tests/e2e/test_flbv2v3_<Suite>/test_njm_<id>.py`, run it, report the real result.

Run a single TC directly:
```bash
pytest tests/e2e/test_flbv2v3_IncludeExclude/test_njm_182425.py -v
pytest tests/e2e/test_flbv2v3_IncludeExclude/test_njm_182425.py -v --headed   # to watch it live
```

Run a whole suite (only when explicitly requested — case-by-case is the default working mode):
```bash
pytest tests/e2e/test_flbv2v3_IncludeExclude/ -v
```

View the Allure report — results (including a per-test recorded video, see below) accumulate in
`results/allure-results/` across runs:
```bash
allure serve results/allure-results          # quick look, ephemeral random port, ctrl-C tears it down
```
For a stable local URL that stays up across a whole case-by-case session, generate the static
report once and serve that folder on a fixed port instead:
```bash
rm -rf results/allure-report && allure generate results/allure-results  # output dir comes from allurerc.json
allure open results/allure-report --port 5252                          # persistent server, survives the launching shell exiting
```
Re-run the `generate` line (after `rm -rf results/allure-report`) whenever new results should
appear — a browser refresh at the same URL picks them up immediately, no server restart needed.

**Trend history**: `allurerc.json` (repo root, auto-discovered by the `allure` v3 CLI) sets
`historyPath: ./results/allure-history.jsonl` — a JSONL file *outside* `results/allure-report/`,
so it survives the `rm -rf results/allure-report` step above and accumulates one entry per
`generate` run (verified: two generations in a row produced a 2-line file, and the report's own
`data/history` folder picked it up). It's gitignored (see `.gitignore`'s comment) since it's local,
per-machine run history — not something to commit.

**Video recordings**: every test run gets Playwright video (`--video=on` in `pyproject.toml`,
works in headless mode too), auto-attached to that test's Allure entry named
`NJM-<id>_<test function name>-video` by the `pytest_runtest_makereport` hook in
`tests/e2e/conftest.py`, once the browser context (and so the video file) has finished writing.

**Content-integrity verification**: `test_flbv2v3_Inventory/_helpers.py`'s `verify_checksum()`
downloads a specific recovered file via the FLR wizard's real **Download** recovery type
(captured through Playwright's download API), extracts it from the `Recovered-items-*.zip`
NBR always wraps even a single file in, and asserts its SHA-256 matches the host's manifest
under `test-data/manifests/` — actual byte-level content verification, not just a filename-
listing match. Built on `browser/pom/common/checksum.py` (manifest parsing + hashing) and two
new `FileLevelRecoveryPage` methods (`select_file_in_current_folder()`, `download_selected()`).
Every Inventory TC with a matching manifest calls it; TCs without one (no seeded/checksummed
fixture, or a TC whose own scope is filesystem-coverage rather than content-matching) document
why in their own docstring instead.

## Conventions

- **One test file per Jira TC** — `tests/e2e/test_flbv2v3_<Suite>/test_njm_<id>.py`, named
  `test_njm_<id>.py` regardless of how many test functions it contains (a TC needing several
  sub-assertions gets several functions in the same file, not several files).
- **Reuse the suite's `_helpers.py`** (`build_flb_job()`, `run_and_wait_flb_job()`,
  `flr_browse()`, `extract_item_names()`) — never duplicate wizard-build or FLR-browse logic
  inline in a test.
- **No XPath or locators in a test file** — they belong in `browser/pom/common/locators.py` or a
  `backup_types/*` locators class. If a test needs a UI interaction the POM doesn't have yet,
  extend the POM, don't reach around it.
- **No RPC in the test path** — `browser_page()`/`mcp__nbr__call` raw scripts under
  `browser/checks/` are fine for live calibration/debugging, but the actual pytest tests only
  ever go through the UI.
- **Cleanup is automatic** via the `flb_job_cleanup` fixture — don't hand-roll job deletion in a
  test. Safety fence: only `AUTO_FLB_*`/`AUTO_FSB_*` names are ever touched.
- **Honest reporting** — a test failing because it found a real product limitation is a
  successful test run, not a bug to hide. Never loosen an assertion just to get green.

## History

This repo previously ran TCs via raw NBR Director RPC (`mcp__nbr__call`) with a separate Allure
reporting layer (`reporting/`) built on an execution-event journal. That approach is retired and
its dead code removed (2026-07-16): the `reporting/` package, its unit tests
(`tests/test_runbook_parser.py`, `tests/test_reporting_pipeline.py`, `tests/conftest.py`), the
old job-template validator (`tests/test_job_templates.py`), the RPC-era screenshot helper
(`browser/nbr_ui.py`), and the superseded master prompt (`docs/EXECUTION_PROMPT.md`, replaced in
full by the `execute-tc` skill). `recipes/file-backup-recipes.md`, all `cases/*.md` runbooks, and
`test-data/job-templates/*.json` were deliberately kept — genuine product-behavior/API-shape
reference value with zero current code depending on them. The pivot to pure-UI Playwright +
pytest was a deliberate architecture decision: every assertion now reflects exactly what the
Director UI itself shows a real user, with Allure wired directly through `pytest`'s own
`--alluredir` (no custom mapping layer needed).
