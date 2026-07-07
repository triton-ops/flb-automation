# File Share Backup — R4c self-contained builder proof — 2026-07-07

- **Goal:** replace the FSB job-build method from "clone golden job 22" (R4a) to the same
  **self-contained canonical template** (R4c) approach already proven for FLB, so File Share
  Backup jobs no longer depend on any live job existing on the appliance.
- **Appliance:** nbr-5 (10.10.15.5, NBR 11.2.1 build 106316)
- **Verdict:** ✅ **PASS** — `fsb_job.template.json` added; a job built purely from it ran to
  `lrState:OK` without ever reading job 22; cleaned up.

## What changed
- Added `test-data/job-templates/fsb_job.template.json` — canonical `BACKUP`/`NAS` JobDto
  skeleton, mirrored field-for-field from the proven FLB template's `options` block (same schema,
  same product), with `sourceVid`/`targetName`/`targetStorageVid`/`mappings` as the only
  substitution-contract fields.
- `recipes/file-backup-recipes.md` R4c generalized to cover both FLB and FSB (one template per
  job type); R4a clone note now names both job 25 and job 22 as deprecated-fallback-only sources.
- `test-data/test-data.md` §5 rewritten: R4c is the current default; the job-22-clone proof is
  kept as historical record.
- `docs/EXECUTION_PROMPT.md` "Supported areas" table now points at the canonical templates
  instead of "golden template" job ids.

## Live proof (build → run → verify → cleanup, no read of job 22)
| Step | Call | Result |
|---|---|---|
| Build | load `fsb_job.template.json` → patch (`sourceVid=FILE_SHARE-18`, `targetName=CIFS-FileTypeSamples`, `targetStorageVid=BACKUP_REPOSITORY-1`, one FILE mapping `sample.txt`, name `AUTO_FSB_r4c_dryrun`) → validate | payload built, no `__PLACEHOLDER__` left |
| Create | `JobManagement.saveJob` | ✅ `{result:"OK", jobId:27}` — **new independent job; job 22 never read** |
| Run | `run [{"runType":"ALL","jobIds":[27]}]` | accepted (async) |
| Poll | `getJobShortInfo [[27]]` | **`lrState:OK`, lrVmOk 1, lrVmFailed 0** |
| Cleanup | `remove [27, false]` | ✅ `{result:"OK"}` |
| Confirm clean | `getListJobs` | job 27 absent; job 22 (golden reference) present, untouched |

## Notes
- While inventorying nbr-5 post-cleanup, jobs 24/25/26 (`Backup job for file share`, not
  `AUTO_FSB_*`) were observed on this shared appliance — **not created by this session**. Left
  untouched per the safety fence (only `AUTO_FLB_*`/`AUTO_FSB_*` named entities are ever modified).
- FSB selection is **file-level only** (no FOLDER `sourceIdentifierType`, unlike FLB); `mappings:[]`
  backs up the entire share.

## Cleanup
nbr-5 left in its prior state: golden reference job 22 intact; `AUTO_FSB_r4c_dryrun` (27) removed
along with its backup.
