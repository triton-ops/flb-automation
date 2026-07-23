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
| `tests/e2e/test_flbv2v3_SourceSelection/` | 48 TCs (NJM-182719, execution A) — Select Items dialog UI-state (34) + special-file backup/recovery content matrix (14) |
| `tests/e2e/test_flbv2v3_IncludeExclude/` | 21 TCs (NJM-182720, execution B) — Inclusion/Exclusion filter rules, one `test_njm_<id>.py` per TC, shared `_helpers.py` |
| `tests/e2e/test_flbv2v3_ObjectStorage/` | 26 TCs (NJM-182721, execution C) — repository/encryption/immutability across every backend (S3, Azure, Wasabi, Backblaze, Local/Synology-immutable, Onboard), one `test_njm_<id>.py` per TC, incl. (skip-stubbed) repository-maintenance TCs |
| `tests/e2e/test_flbv2v3_BackupExecution/` | 50 TCs (NJM-182722, execution D) — backup exec/schedule/retention; 24 Ready, 24 genuinely Blocked (mostly NAS hardware this project doesn't have), 2 No-run |
| `tests/e2e/test_flbv2v3_BackupCopy/` | 43 TCs (NJM-182723, execution E) — Backup Copy Job (incl. tape); newly ported, all skip-marked pending live calibration (no test coverage existed for `BackupCopyPage` before, and no tape support exists at all) |
| `tests/e2e/test_flbv2v3_FLRToSource/` | 11 TCs (NJM-182724, execution F) — FLR "recover to original location" + overwrite behavior; every real execution TC only runs against a dedicated disposable fixture tree, never a shared path |
| `tests/e2e/test_flbv2v3_FLRFunctional/` | 55 TCs (NJM-182725, execution G) — FLR wizard functional coverage (E2E recovery, Backup/Files step selection, large subfolder count, Download recovery type, per-OS support coverage, per-repository recovery), one `test_njm_<id>.py` per TC, shared `_helpers.py`, IN PROGRESS |
| `tests/e2e/test_flbv2v3_Inventory/` | 17 TCs (NJM-182726, execution H) — OS/filesystem support end-to-end workflow; one `test_njm_<id>.py` per TC (the 4 Linux-OS TCs — 67806/67807/67808/67809 — were briefly consolidated into one parametrized file, then split back per this project's strict one-TC-per-file convention; see `docs/parametrize-pattern.md`) |
| `tests/e2e/test_flbv2v3_Dashboard/` | 1 TC (NJM-182727, execution I) — the 'Job Contents' widget; newly ported, skip-marked, needs a new Dashboard-widget Page Object from scratch |
| `tests/e2e/test_flbv2v3_Alarms/` | 5 TCs (NJM-182728, execution J) — job-failure alarm messages (ict45/ict1), two-phase WinRM-mutation pattern |
| `tests/e2e/test_flbv2v3_UiReporting/` | 20 TCs (NJM-182729, execution L) — skipped-items reporting, reliability (error346/ict45), licensing, Multi-Tenancy, Global Search |
| `tests/e2e/test_flbv2v3_Reliability/` | 9 TCs (NJM-182805, execution M) — mid-job fault injection + a soak test; newly ported, all skip-marked (needs a WinRM/SSH-coordinated fault-injection architecture this project doesn't have yet) |
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

Test plan **NJM-182718** has 12 Xray test executions (A–M), all targeting `nbr-84` (FLB). Status
below is Xray-verified TC counts, not estimates (every suite's TC list comes from Jira's own
`testExecutionTests("NJM-<exec-id>")` JQL, not a guess from summaries) — **Ready** means a pytest
test exists AND has actually been run with a live, honest result (a pass, or a genuine documented
negative finding the test itself produced by exercising the scenario); **Blocked** means a pytest
test exists but is `@pytest.mark.skip`-marked because a real, confirmed-live product/environment/
safety constraint prevents even attempting it (missing fixture/repo, a safety-gated action needing
per-run authorization, an unreproducible precondition) — not a work-in-progress marker; **No run**
means either no file exists yet, or one does but hasn't been executed (not yet calibrated/
implemented, or deliberately deferred, e.g. a real-external-cloud-cost TC). A test's own
`reason=`/`SKIP_REASON` explains which of the latter two applies — check it before assuming a
`@pytest.mark.skip` means Blocked; the newly-ported suites (E/I/M) use skip markers purely for
No-run, not Blocked.

| Exec | Suite | TCs | Ready | Blocked | No run | Status |
|---|---|---|---|---|---|---|
| A · NJM-182719 | `test_flbv2v3_SourceSelection/` | 48 | 30 | 10 | 8 | **DONE** (corrected 2026-07-23 — 10 TCs were miscounted as 0 Blocked; all 10 are genuine confirmed-live findings: search-doesn't-filter, EFS/millions-scale fixtures unprovisionable, breadcrumb truncation not reproducible, root-system-file skip needs a whole-volume selection outside this project's small-fileset convention); 8 content-matrix TCs written, not yet run |
| B · NJM-182720 | `test_flbv2v3_IncludeExclude/` | 21 | 21 | 0 | 0 | **DONE** |
| C · NJM-182721 | `test_flbv2v3_ObjectStorage/` | 26 | 20 | 6 | 0 | **DONE** — Synology C2 (NJM-123129/123130) UNBLOCKED and now PASS (repo exists live, real name `SynologyC2` — the earlier `Synology_C2`/`Synology_C2_Immutable` two-repo finding was wrong on both counts); blocked: EC2 fixture gap (4) + repository-maintenance safety-gate, needs per-run authorization (2) — corrected 2026-07-23, the safety-gated pair was wrongly left out of Blocked earlier the same day |
| D · NJM-182722 | `test_flbv2v3_BackupExecution/` | 50 | 24 | 24 | 2 | **DONE** (fully accounted for 2026-07-23 via `testExecutionTests()` JQL — all 50 real TCs now have a file). Blocked (24): 16 NAS-platform end-to-end TCs (no hardware — TrueNAS/WD My Cloud/Netgear/Asustor/Synology/QNAP), 4 mid-job service-disruption reliability TCs (same fault-injection gap as suite M), 2 legacy-scheduler-migration TCs (irreversible appliance upgrade), 1 fresh-install TC, 1 real-scheduled-fire TC (this project always uses run-on-demand). No-run (2): NJM-87527 (needs a real Backup Copy job — suite E has zero calibrated tests yet), NJM-70015 (out of scope, owned by suite F) |
| E · NJM-182723 | `test_flbv2v3_BackupCopy/` | 43 | 0 | 0 | 43 | PORTED, no-run — all 43 TCs written (real Jira summary + jira marker each, fetched via `testExecutionTests()` JQL, one `test_njm_<id>.py` per TC) but skip-marked pending live calibration: ~24 need `BackupCopyPage` (exists, zero test coverage) calibrated per destination/scenario, 12 need tape hardware/POM support this project doesn't have at all, 6 mirror the FLB retention TCs for a Backup Copy Job, 1 needs a two-phase delete-source-RP design |
| F · NJM-182724 | `test_flbv2v3_FLRToSource/` | 11 | 9 | 2 | 0 | **DONE** — recover-to-original-location, only run under explicit per-session authorization |
| G · NJM-182725 | `test_flbv2v3_FLRFunctional/` | 55 | 23 | 13 | 19 | IN PROGRESS (fully accounted for 2026-07-23 via `testExecutionTests()` JQL — found 26 TCs with NO file at all, a much bigger gap than previously tracked, incl. the immutable-per-repository recovery set NJM-123176..123192 and NJM-123510 "recover from an encrypted backup"). Blocked (13): NJM-83372 (`NFS_REPO` removed, environment drift), NJM-123278 (no non-NTFS destination + no concurrent-job orchestration), no Data Domain/HYDRAstor/Seagate Lyve Cloud repo fixture (3), no RHEL8/Debian11/non-Desktop-Ubuntu22.04 source (3), CIFS_REPO inaccessible, no EC2 repo, no SMTP server. No-run (19): NJM-83356/83357/83358/83359 (S3/Azure/Backblaze/Wasabi repo recovery — written, real cloud cost, deferred), NJM-123510 (buildable now — the exact encryption-dialog gap it names was fixed 2026-07-22/23), 8 more immutable-recovery TCs buildable today reusing existing immutable repos (S3/Azure/Wasabi/Backblaze/Cloudian/SynologyC2/Local-Immutable), 4 immutable-recovery-from-Backup-Copy TCs blocked on suite E's own zero calibration, 1 needing HPE_Repo's immutability confirmed live, 1 generic-immutable precursor TC |
| H · NJM-182726 | `test_flbv2v3_Inventory/` | 17 | 17 | 0 | 0 | **DONE** |
| I · NJM-182727 | `test_flbv2v3_Dashboard/` | 1 | 0 | 0 | 1 | PORTED, no-run — the one TC (NJM-69179, 'Job Contents' widget) is written but skip-marked; needs a new Dashboard-widget Page Object from scratch, none exists yet |
| J · NJM-182728 | `test_flbv2v3_Alarms/` | 5 | 2 | 3 | 0 | **DONE** — blocked: repo-out-of-space, license-state alarms |
| L · NJM-182729 | `test_flbv2v3_UiReporting/` | 20 | 9 | 11 | 0 | **DONE** — blocked: Multi-Tenancy not deployed, appliance-wide licensing, no Usage Data feature |
| M · NJM-182805 | `test_flbv2v3_Reliability/` | 9 | 0 | 0 | 9 | PORTED, no-run — all 9 TCs written but skip-marked: 6 need mid-job fault injection (killed transporter, renamed folder, full repository — requires WinRM/SSH coordinated against a live job run, a different test architecture from every other suite), 2 need their own POM/fixture calibration, 1 is a 48-96h soak test incompatible with per-TC pytest execution |
| **Total** | | **306** | **155** | **69** | **82** | |

A live-updated visual version of this table (with the full per-TC blocked-reason breakdown) is
kept as a published Claude artifact — ask for the link if you need it.

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

Notable findings from later suites (F/G/J/L):
- **Genuine, reproducible product defect** (suite L): the skipped-items report's own "View
  details" link is present with correct `data-action`/`data-event-code` attributes, but clicking
  it — tried 6 independent ways, including launching Chromium with `--disable-popup-blocking` —
  never opens a real report; `window.open()` fires but with no report URL. See
  `test_flbv2v3_UiReporting/test_njm_182573.py`.
- **Project-wide race condition, fixed** (suite J): `DataProtectionPage.get_job_status()` could
  return a stale `"Successful"` from one part of the job dashboard while another part still read
  `"Running"`, for a job being rerun. Fixed by checking for a literal `"Running"` first. This
  method backs `run_and_wait_flb_job()`, used by nearly every suite.
- **A dangling symlink is the only reliable "skipped item" fixture** (suite L) — an NTFS deny-ACL
  and a `FILE_SHARE_NONE`-locked file are both silently tolerated by the backup agent; deleting an
  already-backed-up item doesn't trigger a skip either (it's just never re-enumerated).
- **Global Search POM** (suite L): a Backup Copy job run against a backup permanently
  reattributes that backup's "Jobs" popover to the Backup Copy job instead of its original
  creator — a real UX finding, not a locator bug.
- **Environment issues resolve, don't assume permanently blocked**: NJM-83231 (Win2016) and
  NJM-83235 (Win10) were originally BLOCKED (a picker enumeration timeout; a host refusing WinRM)
  — re-verified live after an environment fix and both now pass. Win10 remains reachable through
  the NBR Director's own agent connection while still refusing this project's own WinRM tooling —
  the two use different network paths.
- **Project-wide login fix**: `LoginPage.login()`'s post-submit wait used
  `page.wait_for_load_state("networkidle")`, which reliably timed out (20s) as this appliance's own
  Activities/Issues load grew — the post-login dashboard has enough ongoing background polling
  that it may never go fully network-idle. Replaced with a deterministic wait for the URL to
  actually leave the login page. This affects the shared `logged_in_page` fixture used by
  virtually every test in the project.
- **Encryption-password gap resolved (NJM-123510)**: `FlbWizardPage.set_encryption(True)` alone
  left a job unsubmittable (Finish silently failed validation, with no visible error). Root-caused
  to two dialog gaps — the 'Create password:' toggle is `<input type="button" role="radio">`
  rendered off-screen, not a real `<input type="radio">`, so it needs a real DOM
  `.evaluate("el => el.click()")` rather than a coordinate click; and the dialog's `Description:`
  field is silently required — plus a SEPARATE, easy-to-miss "Key Management Service is Disabled"
  confirmation modal that pops on Finish itself and must be dismissed or the job never actually
  gets created (the wizard just looks permanently "saving"). All three are now handled by
  `set_encryption_password()` and `finish()`/`finish_and_run()`; `test_njm_123509.py` and
  `test_njm_130057.py` (`test_flbv2v3_ObjectStorage/`) confirm end-to-end.
- **More repository-list environment drift, confirmed live 2026-07-23**: `NFS_REPO` and
  `Wasabi_Repo` (plain, non-immutable) have both been removed from nbr-84 since
  `test-data/environment.md` was written — confirmed via the FLB wizard's own Destination-combo
  search (a same-session search for a repo known to still exist, e.g. "Onboard", DID match,
  ruling out a locator/search bug). Blocks `test_njm_83372.py` (NFS Share repo recovery) until a
  real NFS-Share-type repository is re-added; any TC needing a plain Wasabi target now reuses
  `Wasabi-immutable`. Separately, the Synology C2 repository (previously blocking NJM-123129/
  123130) is confirmed up, but under a different name than first recorded: `SynologyC2` (one
  word, no underscore) — not two separate repos `Synology_C2`/`Synology_C2_Immutable` as an
  earlier finding claimed. Both TCs now pass against the corrected name. General lesson
  reinforced: always re-verify a repo name/existence live against the wizard's own Destination
  combo before writing a test against it, never trust a prior session's recorded name unchecked.

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

- **One test file per Jira TC, one Jira TC per test file — no exceptions.** Every file is
  `tests/e2e/test_flbv2v3_<Suite>/test_njm_<id>.py`, named `test_njm_<id>.py`, with exactly one
  `pytest.mark.jira("NJM-<id>")` matching that filename. A single TC needing several
  sub-assertions gets several functions in the same file, not several files (e.g. one function
  per source OS) — but never the reverse: `@pytest.mark.parametrize` is never used to bundle
  *different* TCs into one file, even when their bodies are byte-for-byte identical apart from
  fixture data (see `docs/parametrize-pattern.md` — a real prior attempt at exactly that was
  reversed). A TC whose steps are exactly satisfied by a sibling TC's own test body documents that
  fact in its own single-marker file's docstring instead of duplicating the live job run.
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
