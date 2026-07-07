# flb-automation

Claude-executable test automation for NAKIVO B&R — **File-Level Backup, File Share Backup, and
File-Level Recovery** — built on the `nbr` MCP (NBR Director RPC) + the `remoting` MCP (host
access) + Playwright (UI-validation via XPath POM), with a decoupled **Allure reporting layer**.
Operating prompt: **`docs/EXECUTION_PROMPT.md`**.

Repo: https://github.com/triton-ops/flb-automation (private)

## The flow

```
You: "run NJM-1234"
        │
        ▼
1. Claude fetches the TC from Jira           (mcp__jira__get_issue NJM-1234)
2. Claude generates  cases/<area>/NJM-1234.md  (runbook from cases/TEMPLATE.md + test-data)
3. Claude builds the job from the canonical template — R4c (test-data/job-templates/*.json;
   no dependency on any live/golden job) and executes it step by step (mcp__nbr__call —
   nbr-84 for FLB / nbr-5 for FSB)
4. Claude verifies (savepoint + FLR vs checksum manifest) and screenshots (browser/ POM) for
   UI-state assertions
5. Execution emits a structured event journal (results/runs/<run-id>/journal.jsonl); Claude
   writes results/reports/NJM-1234__<stamp>.md (prose evidence) AND runs
   `python -m reporting.generate --latest` (Allure HTML report with per-step timings,
   attachments, environment info, and failure analysis)
6. Cleanup on PASS (delete AUTO_FLB_NJM-1234 + backups); keep artifacts on FAIL/BLOCKED
```

## Layout

| Path | What |
|---|---|
| `CLAUDE.md` | Binding execution rules — read before running anything |
| `docs/EXECUTION_PROMPT.md` | Autonomous-executor operating prompt (pipeline + reporting contract) |
| `test-data/environment.md` | Connection fixtures (appliances, sources, repos, transporters) |
| `test-data/test-data.md` | Reusable test data: seeded fileset + checksum manifest + job defaults |
| `test-data/job-templates/flb_job.template.json` , `fsb_job.template.json` | Canonical, repo-owned `JobDto` skeletons (FLB / FSB) — the **R4c self-contained builder** source of truth (no live-job dependency) |
| `test-data/manifests/` | Per-host SHA-256 + MD5 checksum manifests (FLR verification oracle) |
| `recipes/file-backup-recipes.md` | Named RPC building blocks R0–R9 (R4c = build-from-template, default) |
| `cases/TEMPLATE.md` | Runbook skeleton |
| `cases/CoreFunctional_Backup/NJM-*.md` | 35 generated runbooks covering core FLB functional/reliability/repository/platform TCs |
| `browser/` | Playwright XPath POM — FLB wizard, FSB wizard, File-Level Recovery flow (see `browser/README.md`) |
| `browser/checks/` | Runnable UI-state checks (`check_flb_wizard_smoke.py`, `check_fsb_wizard_smoke.py`, `check_flr_flow.py`, `check_njm_122652.py`) |
| `reporting/` | Allure reporting layer — execution-event journal → Allure results/report (see `reporting/README.md`) |
| `tests/` | pytest suite for `reporting/`, the runbook parser (over all real `cases/**/*.md`), and the job templates — CI's "unit tests" tier |
| `requirements.txt` , `requirements-dev.txt` | Pinned runtime (Playwright) / dev+CI (+ pytest, ruff) dependencies |
| `pyproject.toml` | pytest + ruff tool config (no `[build-system]` — this isn't a distributed package) |
| `.github/workflows/ci.yml` | GitHub Actions pipeline — lint, unit tests + Allure report artifact, gated self-hosted Playwright smoke (see **CI** below) |
| `results/runs/<run-id>/` | Per-execution event journal + raw artifacts (permanent, never overwritten) |
| `results/allure-results/` , `results/allure-report/` | Generated Allure results / HTML report — **gitignored**, regenerated fresh by CI/`reporting.generate` each time |
| `results/reports/<JIRA-ID>__<stamp>.md` | Prose run report with evidence |
| `results/screenshots/<TC>/` | Curated PNG evidence per testcase |
| `results/screenshots/_scratch/` | Throwaway calibration/debug shots (not evidence) |

## Environment (summary — details in `test-data/environment.md`)

- **Two appliances (NBR 11.2.1), split by area:** `nbr-84` (10.10.16.84) = **FLB**,
  `nbr-5` (10.10.15.5) = **File Share Backup**. User test1. (Old `nbr-149`/11.3.0 retired.)
- FLB sources (nbr-84): `linux-src` (PM-2, `/TestData_ForFLB`), `windows-src` (PM-3, `C:\TestData_ForFLB`).
- FLB repos: Onboard (id 2, fast) / NFS_REPO (id 7) / Wasabi (id 6) / Ceph_S3 (id 8).
  FSB source (nbr-5): `FILE_SHARE-18` (`CIFS-FileTypeSamples`).
- Jobs named `AUTO_FLB_<JIRA-ID>` (nbr-84) / `AUTO_FSB_<JIRA-ID>` (nbr-5).

## Coverage — re-validated on NBR 11.2.1

| Area | Appliance | Job build | Verified |
|---|---|---|---|
| File-Level Backup (physical) | `nbr-84` | **R4c** — self-contained canonical template (no golden-job clone) | ✅ create (**folder + file** via `sourceIdentifierType`) → run → `lrState:OK` → FLR browse, sizes match manifest |
| File Share Backup | `nbr-5` | **R4c** — self-contained canonical template (no golden-job clone) | ✅ create (per-file selection) → run → `lrState:OK` |
| File-Level Recovery | `nbr-84` | — (`FileLevelRecoveryManagement`) | ✅ mount→browse: FILE mapping = 1 file, FOLDER mapping = full tree; recovery-type options incl. **Recovery to original location** (+ Overwrite behavior) calibrated (safety-gated, never auto-executed) |
| UI-validation (wizards) | both | Playwright XPath POM (`browser/`) | ✅ **calibrated end-to-end**: FLB wizard full drive (`check_flb_wizard_smoke.py`), FSB wizard full drive (`check_fsb_wizard_smoke.py`), FLR flow (`check_flr_flow.py`), NJM-122652 gating check — all headless, all pass |
| Reporting | — | `reporting/` (Allure) | ✅ proven end-to-end on a real execution (NJM-67687): metadata, nested steps, RPC attachments, environment.properties, categories, history — zero reporting code in runbooks |
| Backup Copy | — | not present | ⛔ out of scope until a golden BC job exists |

## CI (`.github/workflows/ci.yml`)

**Read this before expecting CI to "run the tests"** — the actual NBR test cases are executed by
an LLM agent (Claude) issuing RPC calls against **private lab appliances** (`10.10.16.84`,
`10.10.15.5`); those are not reachable from GitHub-hosted runners, and there's no scriptable
pytest suite for them. So the pipeline honestly runs what *can* run on hosted infrastructure:

| Job | Runs on | What |
|---|---|---|
| `lint` | GitHub-hosted, every push/PR | `ruff` over `reporting/`, `browser/`, `tests/` |
| `test` | GitHub-hosted, every push/PR | `pytest` (reporting pipeline, all 35 real runbooks, all job templates) → `reporting.generate --all` → uploads `allure-results`/`allure-report`/JUnit XML as workflow artifacts |
| `playwright-lab-smoke` | **self-hosted runner only**, manual `workflow_dispatch` opt-in (`run_lab_smoke: true`) — a no-op on ordinary pushes | Installs Playwright + cached Chromium, runs `browser/checks/check_flb_wizard_smoke.py` against real UI credentials from GitHub Secrets (`NBR_FLB_UI_URL`/`_USER`/`_PASSWORD`) |

To view a CI run's Allure report: open the workflow run → download the `allure-report` artifact →
`python -m reporting.serve --port <n>` pointed at the extracted folder (or `allure open .` if you
have the Allure CLI). To enable `playwright-lab-smoke`, register a self-hosted runner labeled
`nbr-lab` with network access to the appliances, and add the three UI secrets in repo settings.

## Status checklist
- [x] Two-appliance setup mapped + fixtures re-pointed (nbr-84 FLB, nbr-5 FSB)
- [x] Checksum oracle re-verified: win11 `C:\TestData_ForFLB` byte-identical to `manifest-windows.sha256`
- [x] **Self-contained job builder (R4c)**: canonical `flb_job.template.json` + `fsb_job.template.json`,
  no dependency on any live/golden job; proven live on both appliances (build → saveJob → run →
  verify → cleanup) without touching job 25 (nbr-84) or job 22 (nbr-5)
- [x] **New capability proven: file AND folder selection** (`mappings[].sourceIdentifierType`)
- [x] FLB + FSB pipelines: create → run (`runType:ALL`) → verify (`lrState:OK`) → cleanup-on-pass
- [x] **35 runbooks generated** in `cases/CoreFunctional_Backup/`, each with a feasibility flag
  (RUNNABLE / PARTIAL / BLOCKED-env) and a fail-fast precondition guard
- [x] **Playwright POM calibrated** for the current build: FLB wizard, FSB wizard, File-Level
  Recovery (incl. the new recovery-type/original-location option)
- [x] **Allure reporting layer** (`reporting/`): execution-event journal → Allure results/report,
  auto metadata/attachments/environment/categories/failure-analysis/history
- [x] **GitHub Actions CI** (`.github/workflows/ci.yml`): lint + pytest + Allure-artifact upload on
  every push/PR; Playwright lab-smoke gated to a self-hosted runner, opt-in only
- [ ] Re-generate Linux `/TestData_ForFLB` manifest (fileset differs from the old set)
- [ ] Backup Copy: create a golden BC job on an appliance to restore BC coverage
- [ ] Register a self-hosted `nbr-lab` runner + UI secrets to actually exercise `playwright-lab-smoke`

## Usage

Give Claude a JIRA TC id (e.g. *"Execute NJM-70013 using flb-automation"*). Claude follows
**`docs/EXECUTION_PROMPT.md`** (the autonomous executor prompt), the rules in `CLAUDE.md`, and the
**reporting contract** (emit journal events; never call Allure directly). To (re)generate a runbook
without executing, ask for "generate only". 35 core-functional runbooks already exist under
`cases/CoreFunctional_Backup/` — check there before generating a new one.

After a run, view the Allure report:
```
python -m reporting.generate --latest    # or --all to rebuild every run's history
python -m reporting.serve                # serves results/allure-report/ and prints the URL
```

## Conventions

Keep the tree tidy so "where does X go" stays obvious:

- **Run reports** → `results/reports/<TC-or-label>__<YYYYMMDD_HHMM>.md`. Use the JIRA id when a
  report maps to one TC; a descriptive label is fine for batches/dry-runs.
- **Execution journals** → `results/runs/<UTCstamp>__<TC-id>/` (one per run, never overwritten —
  this is the reporting layer's input and the long-term history/trend source).
- **Screenshots** → curated evidence under `results/screenshots/<TC>/NN_step.png`; throwaway
  calibration/debug/exploration shots go under `results/screenshots/_scratch/` and are not
  treated as evidence.
- **Generated runbooks** → persist to `cases/<area>/<JIRA-ID>.md` (from `cases/TEMPLATE.md`) —
  don't discard them after a run; they're the record of what was executed AND the metadata
  source the reporting layer parses.
- **Job templates** → `test-data/job-templates/`; the single maintained source of a valid JobDto
  per job type (R4c). Never clone a live job as the build source.
- **Checksum manifests** → `test-data/manifests/`; regenerate on the host after any fileset change.
- **Browser POM** → edit in one place: selectors in `browser/pom/locators.py`, actions in
  `browser/pom/base_page.py`, config/data in `browser/config/`. See `browser/README.md`.
- **Reporting** → never call the Allure API outside `reporting/allure_mapper.py`; extend via the
  patterns in `reporting/README.md` (new label, new attachment kind, new failure category, …).
- **Tests/CI** → add unit tests under `tests/`; keep them offline/deterministic (no live-appliance
  calls — that's what the runbooks are for). `ruff check reporting browser tests` and `pytest` must
  both pass locally before pushing; CI runs the same commands.
