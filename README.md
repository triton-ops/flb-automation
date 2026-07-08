# flb-automation

Claude-executable test automation for NAKIVO B&R — **File-Level Backup, File Share Backup,
Backup Copy, and File-Level Recovery** — built on the `nbr` MCP (NBR Director RPC) + the
`remoting` MCP (host access) + Playwright (UI-validation via XPath POM), with a decoupled
**Allure reporting layer**.
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
| `test-data/job-templates/flb_job.template.json` , `fsb_job.template.json` , `backup_copy_job.template.json` | Canonical, repo-owned `JobDto` skeletons (FLB / FSB / Backup Copy) — the **R4c/R4d self-contained builder** source of truth (no live-job dependency) |
| `test-data/manifests/` | Per-host SHA-256 + MD5 checksum manifests (FLR verification oracle) |
| `recipes/file-backup-recipes.md` | Named RPC building blocks R0–R9 (R4c = build-from-template, default) |
| `cases/TEMPLATE.md` | Runbook skeleton |
| `cases/BetaSmoke_FLB/NJM-*.md` | 29 generated runbooks covering the FLB beta-smoke suite (supersedes the retired `CoreFunctional_Backup` suite) |
| `browser/` | Playwright XPath POM — FLB wizard, FSB wizard, Backup Copy wizard, File-Level Recovery flow (see `browser/README.md`) |
| `browser/checks/` | Runnable UI-state check scripts — **currently empty**; see `browser/README.md` for the POM layout that any new check builds on |
| `reporting/` | Allure reporting layer — execution-event journal → Allure results/report (see `reporting/README.md`) |
| `tests/` | pytest suite for `reporting/`, the runbook parser (over all real `cases/**/*.md`), and the job templates — CI's "unit tests" tier |
| `requirements.txt` , `requirements-dev.txt` | Pinned runtime (Playwright) / dev+CI (+ pytest, ruff) dependencies |
| `pyproject.toml` | pytest + ruff tool config (no `[build-system]` — this isn't a distributed package) |
| `results/runs/<run-id>/` | Per-execution event journal + raw artifacts (permanent, never overwritten) — **currently empty**, cleared along with the rest of `results/` |
| `results/allure-results/` , `results/allure-report/` | Generated Allure results / HTML report — **gitignored**, regenerated fresh by `reporting.generate` each time |
| `results/reports/<JIRA-ID>__<stamp>.md` | Prose run report with evidence — **currently empty** |
| `results/screenshots/<TC>/` | Curated PNG evidence per testcase — **currently empty** |
| `results/traces/` , `results/dom_dumps/` | Playwright traces / raw calibration dumps — **gitignored**, ephemeral debugging output only, never evidence |

## Environment (summary — details in `test-data/environment.md`)

- **Two appliances (NBR 11.2.1), split by area:** `nbr-84` (10.10.16.84) = **FLB**,
  `nbr-5` (10.10.15.5) = **File Share Backup**. User test1. (Old `nbr-149`/11.3.0 retired.)
- FLB sources (nbr-84): `linux-src` (PM-2, `/TestData_ForFLB`), `windows-src` (PM-3, `C:\TestData_ForFLB`).
- FLB repos on `nbr-84` have grown well beyond the original set: Onboard (id 2, fast) /
  NFS_REPO (id 7) / Wasabi_Repo (id 6), plus several Object-Lock-capable repos added
  2026-07-08 (Cloudian / Cloudian-immutable, Amazon_Repo / Amazon_Immutable, Azure_Repo /
  Azure_Immutable, BlackBlaze_Immutable, Wasabi-immutable, Local-Immutable). `Ceph_S3` (the
  old id 8) was removed and replaced by Cloudian — full current list + state in
  `test-data/environment.md`. FSB source (nbr-5): `FILE_SHARE-18` (`CIFS-FileTypeSamples`).
- Jobs named `AUTO_FLB_<JIRA-ID>` (nbr-84) / `AUTO_FSB_<JIRA-ID>` (nbr-5).

## Coverage — re-validated on NBR 11.2.1

| Area | Appliance | Job build | Verified |
|---|---|---|---|
| File-Level Backup (physical) | `nbr-84` | **R4c** — self-contained canonical template (no golden-job clone) | ✅ create (**folder + file** via `sourceIdentifierType`) → run → `lrState:OK` → FLR browse, sizes match manifest |
| File Share Backup | `nbr-5` | **R4c** — self-contained canonical template (no golden-job clone) | ✅ create (per-file selection) → run → `lrState:OK` |
| File-Level Recovery | `nbr-84` | — (`FileLevelRecoveryManagement`) | ✅ mount→browse: FILE mapping = 1 file, FOLDER mapping = full tree; recovery-type options incl. **Recovery to original location** (+ Overwrite behavior) calibrated (safety-gated, never auto-executed) |
| Backup Copy | `nbr-84` | **R4d** — self-contained canonical template (`backup_copy_job.template.json`) | ✅ create (fixed `hvType:"VMWARE"` — the one gotcha) → run → `lrState:OK`, verified on two different target repos (NFS + Wasabi) |
| UI-validation (wizards) | both | Playwright XPath POM (`browser/pom/`, see `browser/README.md`) | ✅ **POM calibrated** for all four flows (FLB, FSB, Backup Copy, FLR) — page objects, locators, and the known ExtJS gotchas are in place and current as of 2026-07-08. ⚠ `browser/checks/` (the runnable scripts that exercised this POM) was cleared out — there is currently no scripted regression proof; the calibration knowledge lives in the page-object docstrings until a check is rebuilt |
| Reporting | — | `reporting/` (Allure) | ✅ proven end-to-end on a real execution (NJM-67687): metadata, nested steps, RPC attachments, environment.properties, categories, history — zero reporting code in runbooks. (`results/runs/` history was since cleared — the mechanism is proven, the historical run isn't preserved) |

## CI

There is currently **no CI workflow** in this repo (`.github/workflows/ci.yml` was removed). Lint
(`ruff check reporting browser tests`) and tests (`pytest`) still run the same as before — just
locally, not on push/PR. Re-add a workflow if you want that automated again.

## Status checklist
- [x] Two-appliance setup mapped + fixtures re-pointed (nbr-84 FLB, nbr-5 FSB)
- [x] Checksum oracle re-verified: win11 `C:\TestData_ForFLB` byte-identical to `manifest-windows.sha256`
- [x] **Self-contained job builder (R4c/R4d)**: canonical `flb_job.template.json` +
  `fsb_job.template.json` + `backup_copy_job.template.json`, no dependency on any live/golden job;
  proven live on both appliances (build → saveJob → run → verify → cleanup). The old golden jobs
  25 (nbr-84) / 22 (nbr-5) were never touched by this and have since been removed from the
  appliances entirely (confirmed 2026-07-08) — R4a (clone-based) is deprecated with no source left
- [x] **New capability proven: file AND folder selection** (`mappings[].sourceIdentifierType`)
- [x] FLB + FSB pipelines: create → run (`runType:ALL`) → verify (`lrState:OK`) → cleanup-on-pass
- [x] **29 runbooks generated** in `cases/BetaSmoke_FLB/` (supersedes the retired
  `CoreFunctional_Backup` suite), each with a feasibility flag (RUNNABLE / PARTIAL / BLOCKED-env)
  and a fail-fast precondition guard
- [x] **Playwright POM calibrated** for the current build: FLB wizard, FSB wizard, Backup Copy
  wizard, File-Level Recovery (incl. the new recovery-type/original-location option) — reorganized
  under `browser/pom/{base,common,backup_types}/`, see `browser/README.md`
- [x] **Allure reporting layer** (`reporting/`): execution-event journal → Allure results/report,
  auto metadata/attachments/environment/categories/failure-analysis/history
- [x] **Backup Copy (R4d)**: canonical `backup_copy_job.template.json`, fixed `hvType:"VMWARE"`
  (the one gotcha — do not match it to the source's real type); proven end-to-end on two different
  target repos (NFS + Wasabi)
- [ ] Re-generate Linux `/TestData_ForFLB` manifest (fileset differs from the old set)
- [ ] Rebuild runnable check scripts under `browser/checks/` (cleared 2026-07-08 — the POM
  underneath is calibrated and current, there's just no scripted regression proof right now)
- [ ] Re-add a CI workflow if automated lint/test-on-push is wanted again (removed 2026-07-08)

## Usage

Give Claude a JIRA TC id (e.g. *"Execute NJM-1234 using flb-automation"*). Claude follows
**`docs/EXECUTION_PROMPT.md`** (the autonomous executor prompt), the rules in `CLAUDE.md`, and the
**reporting contract** (emit journal events; never call Allure directly). To (re)generate a runbook
without executing, ask for "generate only". Check `cases/<area>/` first — a runbook may already
exist for the id you want.

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
- **Screenshots** → curated evidence under `results/screenshots/<TC>/NN_step.png`. Throwaway
  calibration/debug/exploration output doesn't belong under `results/` at all — use
  `results/traces/` (Playwright traces) or `results/dom_dumps/`, both gitignored and not evidence.
- **Generated runbooks** → persist to `cases/<area>/<JIRA-ID>.md` (from `cases/TEMPLATE.md`) —
  don't discard them after a run; they're the record of what was executed AND the metadata
  source the reporting layer parses.
- **Job templates** → `test-data/job-templates/`; the single maintained source of a valid JobDto
  per job type (R4c/R4d). Never clone a live job as the build source.
- **Checksum manifests** → `test-data/manifests/`; regenerate on the host after any fileset change.
- **Browser POM** → edit in one place: selectors in `browser/pom/common/locators.py`, actions in
  `browser/pom/base/base_page.py`, config/data in `browser/config/`. See `browser/README.md`.
- **Reporting** → never call the Allure API outside `reporting/allure_mapper.py`; extend via the
  patterns in `reporting/README.md` (new label, new attachment kind, new failure category, …).
- **Tests** → add unit tests under `tests/`; keep them offline/deterministic (no live-appliance
  calls — that's what the runbooks are for). `ruff check reporting browser tests` and `pytest` must
  both pass locally before committing (no CI currently enforces this automatically).
