# flb-automation

Claude-executable test automation for NAKIVO B&R — **File-Level Backup, File Share Backup, Backup
Copy, and File-Level Recovery** — built on the `nbr` MCP (NBR Director RPC) + the `remoting` MCP
(host access) + Playwright (UI-validation via XPath POM). Operating prompt: **`docs/EXECUTION_PROMPT.md`**.

## The flow

```
You: "run QA-1234"
        │
        ▼
1. Claude fetches the TC from Jira         (mcp__jira__get_issue QA-1234)
2. Claude generates  cases/QA-1234.md      (runbook from cases/TEMPLATE.md + test-data)
3. Claude executes it step by step         (mcp__nbr__call — nbr-84 FLB / nbr-5 FSB)
4. Claude verifies (savepoint + FLR vs checksum manifest) and screenshots (browser/nbr_ui.py)
5. Claude writes  results/reports/QA-1234__<stamp>.md   (per-step RPC evidence + screenshots + verdict)
6. Cleanup on PASS (delete AUTO_FLB_QA-1234 + backups); keep artifacts on FAIL
```

## Layout

| Path | What |
|---|---|
| `CLAUDE.md` | Binding execution rules — read before running anything |
| `docs/EXECUTION_PROMPT.md` | Autonomous-executor operating prompt (the 8-stage pipeline) |
| `test-data/environment.md` | Connection fixtures (appliance, sources, repo, transporters) |
| `test-data/test-data.md` | Reusable test data: seeded fileset + checksum manifest + job defaults |
| `test-data/manifests/` | Per-host SHA-256 + MD5 checksum manifests (FLR verification oracle) |
| `recipes/file-backup-recipes.md` | Named RPC building blocks R0–R9 |
| `browser/nbr_ui.py` | Playwright helper: login + navigate + screenshot |
| `browser/config/` | `ui_config.json` (secrets) + `ui_values.json` (UI-check data) |
| `cases/TEMPLATE.md` | Runbook skeleton |
| `cases/<JIRA-ID>.md` | Generated, executable runbook per testcase |
| `results/reports/<JIRA-ID>__<stamp>.md` | Run report with evidence |
| `results/screenshots/<TC>/` | Curated PNG evidence per testcase |
| `results/screenshots/_scratch/` | Throwaway calibration/debug shots (not evidence) |

## Environment (summary — details in `test-data/environment.md`)

- **Two appliances (NBR 11.2.1), split by area:** `nbr-84` (10.10.16.84) = **FLB**,
  `nbr-5` (10.10.15.5) = **File Share Backup**. User test1. (Old `nbr-149`/11.3.0 retired.)
- FLB sources (nbr-84): `linux-src` (PM-2, `/TestData_ForFLB`), `windows-src` (PM-3, `C:\TestData_ForFLB`).
- FLB repos: Onboard (id 2, fast) / NFS_REPO (id 7). FSB source (nbr-5): `FILE_SHARE-18`.
- Jobs named `AUTO_FLB_<JIRA-ID>` (nbr-84) / `AUTO_FSB_<JIRA-ID>` (nbr-5).

## Coverage — re-validated on the new build 2026-07-06 (NBR 11.2.1)

| Area | Appliance | Golden template | Verified |
|---|---|---|---|
| File-Level Backup (physical) | `nbr-84` | job 25 `FLB_NFS_REPO` | ✅ create (**folder + file** via `sourceIdentifierType`) → run → `lrState:OK` → FLR browse, sizes match manifest |
| File Share Backup | `nbr-5` | job 22 `Backup job for file share` | ✅ create (per-file selection) → run → `lrState:OK` |
| File-Level Recovery | `nbr-84` | — (`FileLevelRecoveryManagement`) | ✅ mount→browse: FILE mapping = 1 file, FOLDER mapping = full tree |
| Backup Copy | — | not present | ⛔ out of scope until a golden BC job exists |
| UI-validation TCs | — | Playwright XPath POM (`browser/`) | ⏳ POM present; re-point to new UIs before use |

## Status checklist
- [x] Two-appliance setup mapped + fixtures re-pointed (nbr-84 FLB, nbr-5 FSB)
- [x] Checksum oracle re-verified: win11 `C:\TestData_ForFLB` byte-identical to `manifest-windows.sha256`
- [x] Golden templates calibrated: FLB (job 25), File Share Backup (job 22)
- [x] **New capability proven: file AND folder selection** (`mappings[].sourceIdentifierType`)
- [x] FLB + FSB pipelines: create → run (`runType:ALL`) → verify (`lrState:OK`) → cleanup-on-pass
- [ ] Re-generate Linux `/TestData_ForFLB` manifest (fileset differs from old set)
- [ ] Re-point browser POM (`browser/config/`) to the new appliance UIs
- [ ] Backup Copy: create a golden BC job on an appliance to restore BC coverage

## Usage

Give Claude a JIRA TC id (e.g. *"Execute NJM-70013 using flb-automation"*). Claude follows
**`docs/EXECUTION_PROMPT.md`** (the autonomous executor prompt) and the rules in `CLAUDE.md`.
To (re)generate a runbook without executing, ask for "generate only".

The operating prompt is `docs/EXECUTION_PROMPT.md` — paste it (or reference it) to drive a run.

## Conventions

Keep the tree tidy so "where does X go" stays obvious:

- **Run reports** → `results/reports/<TC-or-label>__<YYYYMMDD_HHMM>.md`. Use the JIRA id when a
  report maps to one TC (`NJM-122651__20260626_1620.md`); a descriptive label is fine for
  batches/dry-runs (`FSB-dryrun__20260629.md`, `repo-coverage-batch__20260629.md`).
- **Screenshots** → curated evidence under `results/screenshots/<TC>/NN_step.png`; throwaway
  calibration/debug/exploration shots go under `results/screenshots/_scratch/` and are not
  treated as evidence.
- **Generated runbooks** → persist to `cases/<JIRA-ID>.md` (from `cases/TEMPLATE.md`) — don't
  discard them after a run; they're the record of what was executed.
- **Checksum manifests** → `test-data/manifests/`; regenerate on the host after any fileset change.
- **Browser POM** → edit in one place: selectors in `browser/pom/locators.py`, actions in
  `browser/pom/base_page.py`, config/data in `browser/config/`. See `browser/README.md`.
