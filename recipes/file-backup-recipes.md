# Recipes — file-level physical backup

> Reusable building blocks for cases. Each recipe is a named, copy-pasteable NBR MCP call
> (or remoting call) with the expected result. Cases reference recipes by id (R1, R2, …).
>
> **Golden rule (see CLAUDE.md):** before executing any *write* recipe for the first time in
> a session, run `mcp__nbr__describe_method` to confirm the parameter shape against the live
> spec. Payloads below are verified against NBR **11.2.1** (builds 106315/106316), re-calibrated
> 2026-07-06, but spec can drift.

`nbr` calls use `alias="nbr-84"` for **FLB** and `alias="nbr-5"` for **File Share Backup**
(two separate Directors — see `environment.md`). `remoting` calls use the host alias from
`environment.md` (`flb-linux` / `win11` / `win-fs3`).

---

## R0 — Seed test data (one-time setup, reusable by all cases)

Create the fileset from `test-data.md §1` on each host, then record checksums.

**Linux (`flb-linux`, ssh):** `mcp__remoting__ssh_run` a script that makes the tree under
`/TestData_ForFLB`, writes the text files with fixed content, and generates deterministic
binaries (e.g. `head -c 2097152 /dev/zero | tr '\0' 'A' > binary/blob_2mb.bin`, or
`dd if=/dev/urandom ... ` with a fixed seed alternative). Then `sha256sum -b` every file.

**Windows (`win2019`, winrm):** `mcp__remoting__winrm_run` a PowerShell script that makes the
tree under `C:\TestData_ForFLB`, writes the text files, generates the binaries
(`fsutil file createnew` then fill, or `[byte[]]` buffer write), then
`Get-FileHash -Algorithm SHA256`.

**After seeding:** write the size + sha256 of each file into the manifest tables in
`test-data.md §1`. The manifest is the verification oracle for FLR (R7).

> Detailed seed scripts live alongside this repo once run; keep them deterministic so a
> re-seed reproduces identical content (and identical checksums).

> ⚠️ **After seeding NEW folders onto an already-discovered physical machine, refresh
> `PhysicalDiscovery` before building/running any job against them** — calibrated 2026-07-15,
> NJM-182424. A source machine discovered before the new fixtures were created keeps a stale
> cached folder-tree snapshot; `saveJob` + `run` against a path in the new tree fails fast
> (~8s) with `lrState:FAILED` and the event log shows `BackupEnforcePreconditions: the
> infrastructure has changed` → `The "<path>" folder cannot be found` — even though the folder
> demonstrably exists (verified independently via `winrm_run`/`ssh_run`). **Fix:**
> `mcp__nbr__call <nbr-84|nbr-5> PhysicalDiscovery refreshAll []` (async, no args), wait ~20s,
> confirm via `PhysicalDiscovery.getFolders ["PM-3","<parent-path>"]` that the new folders are
> now listed, then (re)run the job. One `refreshAll` call refreshes every discovery item on the
> appliance — no need to repeat per-TC within the same seeding batch, only after seeding a fresh
> round of fixtures.

---

## R1 — Confirm a source machine is present and OK  (FLB → nbr-84)

```
mcp__nbr__call nbr-84 PhysicalDiscovery getDiscoveryItems
```
Expect: `result.items[]` contains the source with `state == "OK"`.
- linux-src → name `Linux_16.84`, `targetVid == "PM-2"`
- windows-src → name `Windown`, `targetVid == "PM-3"`

If the machine is missing or not OK → the case cannot run; report blocked.

---

## R2 — List folders on a source (for source selection)

```
mcp__nbr__describe_method nbr-84 PhysicalDiscovery getFolders   # confirm 2-param shape first
mcp__nbr__call nbr-84 PhysicalDiscovery getFolders <args>
```
Used to confirm `/TestData_ForFLB` (or `C:\TestData_ForFLB`) is visible to the Director and
to obtain the folder reference the job payload needs.

---

## R3 — Inspect the target repository

```
mcp__nbr__call nbr-84 BackupManagement getBackupRepositories {"request":{"filter":{"start":0,"count":1000,"useUnlimitedCount":true}}}
```
Expect (nbr-84 FLB): `id == 2` `Onboard repository` (LOCAL, fast) or `id == 7` `NFS_REPO`, both
`state == "OK"`, `isAccessible == true`. This id is the job's backup target. (⚠️ `id == 3`
`CIFS_REPO` is INACCESSIBLE — don't use.)

---

## R4 — Create the file-level backup job

`JobManagement.saveJob(SaveJobRequestDto{ origin, job: JobDto })` →
returns `{ result: "OK", jobId: <n> }`.

> **Default = R4c (self-contained builder).** NBR has **no server-side default/factory job API**
> (only `saveJob`, `getJobForEditing`, `cloneJob`), and `saveJob` does **not** merge server defaults
> for omitted fields — it needs a complete, valid `JobDto`. So the framework ships a canonical
> repo-owned skeleton and patches only the required fields. **Do not clone a live job (R4a is
> deprecated).**

**R4c — Build from the canonical repo template (DEFAULT; self-contained, no live-job dependency).**
Creates a NEW job without reading/cloning job 25 (FLB) or job 22 (FSB) or any live job. A clean
appliance (sources/shares discovered + a repo online) is sufficient. The valid shape ships in the
repo — one template per job type:
- FLB: `test-data/job-templates/flb_job.template.json` (nbr-84, `type=FILE_LEVEL`/`hvType=PHYSICAL`)
- FSB: `test-data/job-templates/fsb_job.template.json` (nbr-5, `type=BACKUP`/`hvType=NAS`)

```
1. Load the canonical skeleton for the area (flb_job.template.json | fsb_job.template.json) →
   working copy. (single maintained artifact per type; NEVER read job 25 or job 22.)
2. Patch ONLY the substitution-contract fields (modular "builders"):
   SourceBuilder      FLB: objects[0].sourceVid = "PM-2"|"PM-3" ; targetName = "Linux_16.84"|"Windown"
                      FSB: objects[0].sourceVid = "FILE_SHARE-18" ; targetName = "CIFS-FileTypeSamples"
   MappingBuilder     objects[0].mappings = [ {type:"NORMAL", sourceIdentifier:"<fwd-slash path>",
                        sourceIdentifierType:"FOLDER"|"FILE", sourceVid:null, targetVid:null, target:null,
                        availabilityZoneVid:null, securityGroupVids:null, primaryIp:null,
                        diskControllerType:null}, ... ]  — FLB: FOLDER or FILE; FSB: FILE only
                        (or leave [] for FSB's whole-share scope)
   RepositoryBuilder  objects[0].targetStorageVid = "BACKUP_REPOSITORY-<id>"  (nbr-84 or nbr-5 ids — see environment.md)
   IdentityBuilder    name = "AUTO_FLB_<JIRA-ID>" | "AUTO_FSB_<JIRA-ID>"  (id/lockUuid/options.id/objects[0].id stay null)
   BackupOptionsBuilder (ONLY when the TC needs it; else keep defaults):
                        options.backupEncryptionMode + options.encryptionPasswordId ;
                        options.accessControlList = FOLDER_PERMISSIONS|FOLDER_AND_FILE_PERMISSIONS ;
                        options.applicationAwareMode ; options.differentialTrackingMode
   ScheduleBuilder    schedules = []  (on-demand)  OR a real schedule (immutability REQUIRES a schedule)
3. ValidationBuilder — FAIL FAST → report BLOCKED before saveJob unless ALL hold:
   • source/share present & OK (R1)  • repo present & OK (R3)  • mappings (if any) non-empty, fwd
     slashes, sourceIdentifierType ∈ {FOLDER,FILE} (FSB: FILE only)  • name starts with
     AUTO_FLB_/AUTO_FSB_  • no __PLACEHOLDER__ tokens left
4. Strip the _README/_SUBSTITUTION keys, then (introspect once per session) saveJob:
   mcp__nbr__describe_method <nbr-84|nbr-5> JobManagement saveJob
   mcp__nbr__call <nbr-84|nbr-5> JobManagement saveJob {"origin":"NONE","job":<patched>}   (args_path — large)
   Expect { result:"OK", jobId:<n> } → a NEW independent job; no live template touched.
```

> **Self-healing / maintenance:** one repo-owned template per job type → no job-25/job-22 coupling,
> portable to any appliance, deterministic. If `saveJob` ever rejects a field (spec drift / new
> required field), fix the **single** relevant template file and every runbook inherits it.
> `describe_method` before the first write catches drift early. Verified shape vs NBR 11.2.1
> (FLB: build 106315 on nbr-84; FSB: build 106316 on nbr-5).

**R4a — Clone the golden template (DEPRECATED — emergency fallback only).** Couples every generated
job to a live job (25 for FLB, 22 for FSB — must exist and stay unchanged) — avoid. Kept only for
when the canonical template is missing/stale. Reuse the proven `options` block verbatim; only
patch identity, source, target, and item selection.

```
1. template = mcp__nbr__call nbr-84 JobManagement getJobForEditing [25, null]
              # returns the full editable JobDto (+ a lockUuid; the lock auto-expires in 15s)
2. Build `job` from template.result with these patches:
     job.id                     = null              # null id => saveJob CREATES a new job
     job.name                   = "AUTO_FLB_<JIRA-ID>"
     job.lockUuid               = null
     job.schedules              = []                # manual run (R5); or keep to test scheduling
     job.options.id             = null
     job.objects[0].id          = null
     job.objects[0].sourceVid   = "PM-3"  (windows-src `Windown`)  | "PM-2" (linux-src `Linux_16.84`)
     job.objects[0].targetName  = "Windown"                        | "Linux_16.84"
     job.objects[0].targetVid   = null              # server assigns the new BACKUP_OBJECT
     job.objects[0].targetStorageVid = "BACKUP_REPOSITORY-2"   # Onboard (fast) or -7 (NFS_REPO)
     job.objects[0].mappings    = [ one entry per selected item, see below ]
     # keep job.targetStorageType="DISK", job.containers=[] as-is
3. saveJob:  mcp__nbr__call nbr-84 JobManagement saveJob {"origin":"NONE","job": <patched job>}
   (payload is large -> write JSON to disk and use args_path)
```

**Item selection** — each protected item is one `mappings[]` entry. The build encodes the item
kind with **`sourceIdentifierType`** (`FOLDER` or `FILE`); paths use FORWARD slashes even on
Windows:
```json
{ "type": "NORMAL", "sourceIdentifier": "C:/TestData_ForFLB/ft_code",              "sourceIdentifierType": "FOLDER" }  // windows folder
{ "type": "NORMAL", "sourceIdentifier": "C:/TestData_ForFLB/ft_pdf/sample_pdf.pdf", "sourceIdentifierType": "FILE"   }  // windows single file
{ "type": "NORMAL", "sourceIdentifier": "/TestData_ForFLB/ft_code",                 "sourceIdentifierType": "FOLDER" }  // linux folder
```
All other mapping fields (`sourceVid`, `targetVid`, `target`, …) are null.

> ✅ **NEW build (11.2.1, 106315) supports BOTH file and folder selection** — verified end-to-end
> 2026-07-06. Set `sourceIdentifierType` to `FOLDER` or `FILE` per entry; a single job may mix
> both. FLR browse (R7) confirms a `FILE` mapping restores exactly that one file and a `FOLDER`
> mapping the whole tree. **This retires the old nbr-149 "folder-level only" limitation** — the
> NJM-122651 Volume/File steps are back in scope. **VOLUME selection CONFIRMED WORKING via the
> UI, 2026-07-08** (`browser/checks/check_njm_122651.py`, live PASS): ticking a volume row (e.g.
> `Local Disk (C:)`) directly in the Select Items dialog — without drilling into it — registers
> correctly in the selected-items count, and unticking clears it. Not yet re-verified at the
> RPC/`sourceIdentifierType` level (only FOLDER/FILE are calibrated there) — if a runbook needs a
> volume-scoped mapping via `saveJob` directly, confirm the exact `sourceIdentifierType` value for
> a volume (likely `VOLUME`, unconfirmed) via `describe_method` first.

> ⚠️ **Known UI-only gotcha (Linux, RPC-built mapping on a secondary mounted volume) —
> calibrated 2026-07-13, NJM-68934 (XFS coverage).** If a **Linux** FOLDER mapping's
> `sourceIdentifier` crosses a **mount-point boundary** — i.e. the path lives on a *secondary*
> mounted filesystem (e.g. `/mnt/xfs_testdata/TestData_XFS`, a separate disk mounted under
> `/mnt`, not a subdirectory of the root volume) — and that mapping was built via **R4c/saveJob
> (RPC)** rather than clicked through the Director UI wizard, then **re-opening that job's
> Select Items dialog in the UI renders every top-level folder as "partial selected"**
> (`boot`, `cdrom`, `dev`, `etc`, `home`, `lost+found`, `media`, …), not just the real ancestor
> (`mnt`). Root-caused via a 3-way A/B/C comparison, live on nbr-84:
> | Build path | Mapping path | Select Items render |
> |---|---|---|
> | RPC (`saveJob`) | `/TestData_ForFLB` (root volume) | ✅ correct — only the real ancestor shows partial |
> | RPC (`saveJob`) | `/mnt/xfs_testdata/TestData_XFS` (secondary volume) | ❌ **broken** — every top-level folder shows partial |
> | Manual UI click-through | `/mnt/xfs_testdata/TestData_XFS` (same secondary volume) | ✅ correct — only `mnt` shows partial |
>
> **Not a `nbr` MCP bug** — the persisted job (`JobManagement.getJob`) matches the sent payload
> byte-for-byte; the MCP transmits the mapping faithfully. The likely explanation: the Director
> UI's own wizard attaches extra volume-scoping metadata when a human clicks through the Select
> Items tree (needed to resolve *which* volume a cross-mount path belongs to), and the plain
> `sourceIdentifier` + `sourceIdentifierType` pair accepted by `saveJob` has no field to carry
> that. Windows is unaffected — verified live that an RPC mapping onto a **secondary drive
> letter** (`F:/`, a distinct volume from `C:`) renders correctly in Select Items, because
> Windows drive letters are already separate, explicitly-identified top-level tree nodes, unlike
> a Linux mount point (which is just an ordinary-looking subfolder under `/`).
> **Impact: cosmetic only** — the job itself builds and runs correctly (`lrState:OK`, correct
> savepoint content); this only affects a human/UI review of the job's Source step afterward.
> No known workaround via `saveJob` alone; if a case needs a clean Select Items render for a
> Linux cross-mount source, build that one job via the UI wizard (or accept the cosmetic
> discrepancy and note it in the runbook).
>
> **Broader defect confirmed 2026-07-14: RPC-built Linux jobs also fail File Level Recovery
> browse**, regardless of mount-crossing — even a plain, one-level-deep mapping
> (`/TestData_ForFLB/MixedTypes`). Live A/B on the identical mapping, same source (Rocky_Linux9,
> `PM-22`): a `saveJob`-built job's FLR "Files" step shows the mapped folder as **"No items are
> available"**; the identical mapping built through the Director UI wizard shows all files
> correctly. The backed-up data itself is correct (byte sizes match) — only the recovery-browse
> index is affected, and only for RPC-built Linux jobs. See **R4e** below for the batch-safe
> workaround.

> ⚠️ **Separate defect, Windows source, ANY Inclusion/Exclusion filter active — calibrated
> 2026-07-15, NJM-182426 + NJM-185018.** When either `options.enabledSourceItemsInclusion` OR
> `options.enabledSourceItemsExclusion` is enabled on a job whose mapped FOLDER contains
> **nested subfolders** (e.g. `PathTest/{A,B,C}`, or `Unicode/文件夹/inside.txt`), the backup
> engine correctly captures the matching bytes (`consumed` on the savepoint matches the expected
> total) and FLR's listing correctly shows the matching top-level subfolder names — but
> `FileLevelRecoveryManagement.list` returns **empty** when browsing *into* any of those
> subfolders, regardless of how broad the pattern is (even `sourceItemsInclusion:"*"`, matching
> everything, still fails) and **regardless of whether it's an Inclusion or Exclusion rule**
> (confirmed on both: NJM-182426 used Inclusion, NJM-185018 used Exclusion-only and hit the
> identical symptom — `consumed` bytes proved `inside.txt` was captured, but browsing into
> `文件夹` returned 0 items). Tried and ruled out as pattern-syntax mistakes on the Inclusion
> side: absolute path (hangs the job entirely — see below), `A\*`, `A/*`, exact relative file
> path — all either match nothing or produce this same empty-nested-browse symptom. **Impact:**
> R7 (FLR-browse) verification is unreliable for any Include/Exclude TC whose fixture nests
> matched files more than one level below the mapped root, **whenever any Inclusion/Exclusion
> filter is active at all** — byte-count (`consumed`) is the only fallback signal, and it only
> proves total bytes, not which specific files were included (cross-check against `ssh_run`/
> `winrm_run wc -c`/`Get-ChildItem` sizes on the source to disambiguate). **Also noted:** a
> pattern that is a literal absolute Windows path with **no trailing wildcard** (e.g.
> `C:\TestData_ForFLB\...\PathTest\A`, no `*`) can make the job hang indefinitely
> (`crState:RUNNING`, `crProgress` frozen, no failure event) — stop it manually
> (`JobManagement.stop {"jobIds":[<id>]}`) rather than waiting it out.

**R4e — Scripted UI wizard (Playwright) — use for Linux sources needing a clean FLR browse.**
`browser/checks/build_flb_jobs_linux_batch.py` drives the real Director UI wizard via the
existing POM (`FlbWizardPage`) instead of `saveJob`, looping over a `MACHINES` list so multiple
Linux jobs build back-to-back in one unattended run — batchable like RPC, but goes through the
real UI so it does not carry the RPC-only FLR-browse defect above. Edit `MACHINES` (ui_name,
drill_path, checks, job_name) and run `cd browser && python checks/build_flb_jobs_linux_batch.py`
(add `--headed` to watch). Builds only (Finish, not Finish & Run); run the resulting jobs via the
normal R5. Verified live 2026-07-14: 4 Linux jobs (Rocky9, Debian12, SLES15, Ubuntu24) built in
two batch runs, all reached `lrState:OK`, all confirmed FLR-browsable in the UI (files visible,
correct sizes/timestamps) — unlike their `saveJob`-built predecessors.

**R4b — From scratch (only if no template).** Build the full `JobDto`
(`type="FILE_LEVEL"`, `hvType="PHYSICAL"`, full `options`, `objects[0]` as above). Large/brittle
— prefer R4a. A copy of the proven shape is always available live via `getJobForEditing(25,null)`.

Record on success: `jobId` and `SaveJobResponseDto.result == "OK"`.

> Verified 2026-07-06 (R4a, historical): cloned job 25 → `AUTO_FLB_newbuild_verify` (job 26, one
> FOLDER + one FILE) → run → `lrState:OK` → FLR-browsed → cleaned up.
> Verified 2026-07-07 (**R4c**, current default): built `AUTO_FLB_NJM-67687` straight from
> `flb_job.template.json` (no read of job 25) → `saveJob` → run → `lrState:OK` → FLR-browsed →
> cleaned up. Same proof repeated for FSB: built `AUTO_FSB_r4c_dryrun` from `fsb_job.template.json`
> on nbr-5 (no read of job 22) → `saveJob` (jobId 27) → run → `lrState:OK`, `lrVmOk:1` → removed.
> The self-contained create path is exercised end to end for **both** areas.

**File Share Backup (nbr-5):** same `saveJob` shape, built from `fsb_job.template.json`
(`type="BACKUP"`, `hvType="NAS"`, `sourceVid="FILE_SHARE-18"`, `differentialTrackingMode="PROPRIETARY"`);
mappings are per-file `sourceIdentifierType="FILE"` entries on the share (or `[]` for the whole
share). See `test-data.md §5`. **This is a different job *area* (a primary backup job against a
NAS file-share source on a different appliance) — not to be confused with R4d below, which is a
different job *type* (a secondary copy job against an existing backup) on the same nbr-84.**

---

## R4d — Backup Copy job — VERIFIED WORKING (2026-07-08, nbr-84)

**Not the same feature as File Share Backup above.** A Backup Copy (BC) job doesn't back up a
live source — it copies an *already-existing* backup (a `BACKUP_OBJECT` produced by some other
job, FLB or otherwise) into a second, different repository, normally for retention diversity or
immutable/off-site retention. Same `JobManagement.saveJob` RPC as any other job, just a different
`type`.

```
1. sourceVid       = "BACKUP_OBJECT-<id>"   # an EXISTING backup object, not a discovery/source VID
2. hvType          = "VMWARE"   # FIXED — always this literal value, regardless of the source
                      backup's actual hvType. Do NOT match it to the source (PHYSICAL for an
                      FLB-produced object) — that is the one thing that broke it (see below).
3. targetStorageVid = a repo DIFFERENT from the source object's own repo
4. mappings        = []   (BC copies the whole backup object; no item-level selection)
5. options.differentialTrackingMode = "NONE"
6. options.retentionPolicy.retentionMode = "RULESET"   (only meaningful if the target repo
   actually supports immutability — see the caveat below)
```

**Root-cause history (kept for context — don't repeat this mistake):** an initial live attempt
(job 34, `AUTO_FLB_bctest_dryrun`) set `hvType:"PHYSICAL"` to match its FLB source. `saveJob`
accepted it (`{result:"OK", jobId:34}`), but running it failed **immediately** (~200ms): the
`BackupCopyEnforcePreconditions` action threw
`com.company.product.services.core.exceptions.FeatureNotSupportedException`, then NBR
auto-retried every 15 minutes rather than terminal-failing — `crState` stayed `RUNNING` with
`crProgress` frozen the whole time (see R6's warning on why `getJobShortInfo` alone missed this).
This was misread as a product/license limitation. It was not: the user manually built the
equivalent job through the Director UI (job 35) and it ran successfully — the UI-submitted DTO
had **`hvType:"VMWARE"`** at the top level despite copying the same `PHYSICAL`/`FILE_LEVEL`
source. Re-tested via RPC with `hvType:"VMWARE"` (job 36, `AUTO_FLB_bctest_dryrun2`, source
`BACKUP_OBJECT-8` → target `BACKUP_REPOSITORY-6` Wasabi, a **Disk**-type destination): `saveJob`
OK → ran → `lrState:"OK"`, `lrVmOk:1` → a real, accessible savepoint landed on Wasabi
(`consumed:67208529`, matching the source almost exactly) → job removed cleanly. Confirmed twice,
across two different target repos (NFS and Wasabi).

**Conclusion:** Backup Copy **works** for FLB (`PHYSICAL`/`FILE_LEVEL`) sources on this build —
the earlier block was entirely our own payload bug (`hvType` mismatch), not a licensing/feature
gate. Canonical, corrected shape: `test-data/job-templates/backup_copy_job.template.json`.
BC-dependent test cases are no longer blocked by "BC doesn't exist" — re-evaluate each on its own
remaining merits (e.g. immutability still requires a repo with `backupImmutabilitySupport:true`,
which none of nbr-84's current repos have — see `environment.md` — and Tape destination is
greyed out in the UI, no tape hardware). Full detail: `test-data/test-data.md §4`.

---

## R5 — Run the job  (CALIBRATED)

`run` takes a `RunRequestDto`. **Use `runType: "ALL"`** to run the whole job:
```
mcp__nbr__call nbr-84 JobManagement run [{"runType": "ALL", "jobIds": [<jobId>]}]   # FLB (nbr-5 for FSB)
```
Async — returns `null`. Proceed to R6 to poll.

> ⚠️ **Pitfall (verified NJM-122651):** `runType: "SPECIFIC"` means "run a specific *source*
> list" and, with no `sourceVids`, the run fails fast with
> `CreateExecutionSteps … unsupported condition: empty VMs to run`. For a normal whole-job run
> always use `ALL`.

---

## R6 — Poll job until finished

```
mcp__nbr__call nbr-84 JobSummaryManagement getJobShortInfo [[<jobId>]]   # light; read crState/lrState
mcp__nbr__call nbr-84 JobManagement getJob <jobId>                       # full job DTO if needed
```
Poll `getJobShortInfo` on a 15–30s interval; `crState` is the current run, `lrState` the last run.
**Terminal success = `lrState:"OK"`** (with `crState` back to `WAITING_DEMAND`, `lrVmOk≥1`,
`lrVmFailed=0`). `RUNNING`/`GREEN` alone is NOT success. Also usable: `ActivityManagement`.

> ⚠️ **`crState:"RUNNING"` can mean "failed and idling until an internal auto-retry timer," not
> "actively processing"** (verified 2026-07-07, `AUTO_FLB_bctest_dryrun` job 34): the job hit a
> precondition failure (`BackupCopyEnforcePreconditions` → `FeatureNotSupportedException`) within
> ~200ms of starting, then NBR scheduled a **15-minute auto-retry** and left `crState` at
> `RUNNING`/`crProgress` frozen for the whole wait — `getJobShortInfo` alone gave zero signal that
> anything had gone wrong. **Cross-check `EventManagement.getEvents` for the jobId whenever
> `crProgress` is unchanged across 2+ poll intervals** — look for `job.object.action.run.failed`
> / `job.object.processing.failed` events; don't rely on `crState` alone to distinguish "still
> working" from "failed, waiting to retry."
> ```
> mcp__nbr__call nbr-84 EventManagement getEvents [{"start":0,"count":50,"useUnlimitedCount":true}]
> ```
> ⚠️ This returns the **entire** event history (no working filter found for job/date scoping in
> this build) — can be MBs; grep the response for the jobId or job name rather than reading it whole.

Capture the run result + any alert/error text into the report.

---

## R7 — Verify the backup (savepoint + FLR)  (CALIBRATED NJM-122651)

1. **Savepoint:** `JobManagement.getSavepoints ["BACKUP_OBJECT-<id>", 5]` → savepoint `id` (=spId),
   `isAccessible`, `checkState`. Find `BACKUP_OBJECT-<id>` via `getJob [<jobId>]` →
   `objects[0].targetVid` (populated after the first successful run).
2. **FLR mount + browse (non-destructive — strong verification):**
   - `FileLevelRecoveryManagement.createSession [{"hvType":<hvType>,"type":"BACKUP_OBJECT","id":<boId>,"spId":<spId>}]` → `sessionUuid` (spId is REQUIRED)
   - poll `getState [sessionUuid]` until `state:"ACTIVE"` (also keeps the session alive — it times out ~1 min)
   - `list [sessionUuid, null, "NORMAL", "FS_ROOT", 0, 100]` → root = the selected folders (proves folder scope)
   - `list [sessionUuid, "<C:\\...\\folder\\>", "NORMAL", "NORMAL", 0, 200]` → files with name + size; compare to the manifest
   - `closeSession [sessionUuid, false]` when done
   - **`hvType` depends on the ORIGINAL source type being recovered, never the wrapping job's own type** — CALIBRATED live 2026-07-08:
     | Original source | Appliance | `hvType` | Director UI menu label |
     |---|---|---|---|
     | FLB (physical machine) | `nbr-84` | `"PHYSICAL"` | 'File level recovery' |
     | FSB (file share, `BACKUP`/`NAS`) | `nbr-5` | `"NAS"` | 'File share recovery' (a DIFFERENTLY-worded menu item, opens a 'File Share Recovery Wizard' — same underlying 4-step flow otherwise; the calendar/table recovery-point picker on step 1 comes pre-selected to the latest point when entered via a specific job's own Recover button) |
     | Backup Copy of an FLB backup | `nbr-84` | `"PHYSICAL"` (the copy's OWN backup object/savepoint id — never the fixed `"VMWARE"` the Backup Copy job itself uses) | 'File level recovery' — verified live: built two temporary Backup Copy jobs copying an FLB backup, confirmed `createSession` with `hvType:"PHYSICAL"` mounts + browses the COPY's own savepoint successfully |
     | Backup Copy of an FSB backup | `nbr-5`/`nbr-84`† | `"NAS"` (expected by the same logic — not separately live-verified) | 'File share recovery' (expected) |

     †Whichever appliance holds the Backup Copy job. The Director UI's own Recover menu is
     the SAME 'GRANULAR RECOVERY' menu for every job type (Individual files / File level
     recovery / File share recovery / Object recovery for .../ etc., plus a 'PHYSICAL MACHINE
     FULL RECOVERY' section) — it is **not** a distinct per-job-type menu. Only the items
     matching the backup's ORIGINAL source type render enabled; the rest are present but
     greyed out. Confirmed live: a Backup Copy of an FLB backup shows 'File level recovery'
     enabled and 'File share recovery' present-but-disabled in that same menu.

     **Environment gotcha, not a recipe bug:** a freshly-completed Backup Copy's savepoint can
     come back `isAccessible:false` on some target repos (observed live on an S3-compatible
     Cloudian repo — `createSession` succeeded but the session immediately went to `CLOSED`
     instead of `ACTIVE`; the Director UI's own Recover button was correctly greyed out too,
     consistent with the RPC state) while an otherwise-identical copy to a LOCAL repo was
     `isAccessible:true` immediately and mounted cleanly. If a Backup Copy's Recover is
     disabled or `createSession` closes immediately, check the target repo's own
     accessibility/health first — see `test-data/environment.md` for current repo state —
     before assuming a locator or recipe problem.
3. **Byte-level checksum (recover the data OUT, then hash) — VERIFIED NJM-122651:** `recover` to an
   **export share** (custom-location recovery **requires a CIFS or NFS share target**):
   ```
   mcp__nbr__call nbr-84 FileLevelRecoveryManagement recover [{
     "recoveryType":"EXPORT", "location":"CIFS",          // or "NFS"
     "pathToTheShare":"\\\\10.10.15.3\\SharedData",        // NFS form: "10.10.15.3:/NFSSS" (share host = win-fs3)
     "credential":{"type":"PASSWORD","username":"Administrator","password":"<pw>"},
     "sessionUuid":"<uuid>", "items":["C:\\TestData_ForFLB\\ft_code\\"] }]
   ```
   NBR writes a **`Recovered-items-*.zip`** to the share root. Then via the remoting MCP: mount the
   share (PowerShell `New-PSDrive ... -Credential`), copy the zip with **`-LiteralPath`** (the name has
   `[ ]` wildcards), `Expand-Archive`, `Get-FileHash -Algorithm SHA256`, and compare each to
   `test-data/manifests/manifest-<host>.sha256`. Clean up the zip + temp afterward.
   - ⚠️ `recoveryType:"ORIGINAL"`+`OVERWRITE` overwrites the source — **blocked by safety** (destructive).
   - ✅ **`recoveryType:"ORIGINAL"`+Rename is VERIFIED WORKING and non-destructive on a Windows
     physical source** (PM-3). Naming convention (confirmed live 2026-07-08): when the recovered
     item's name already exists at the destination, NBR appends a **`-recovered`** suffix (hyphen,
     no space) to the conflicting item's name — e.g. recovering the `ft_pdf` folder back to
     `C:\TestData_ForFLB\` (where `ft_pdf` already exists) produced a sibling
     **`ft_pdf-recovered`** folder, with the original file names preserved *inside* it
     (`ft_pdf-recovered\sample_pdf.pdf`, unchanged content/size). The original `ft_pdf` folder and
     its contents were confirmed completely untouched (checksum + `LastWriteTime` unchanged). The
     suffix applies at whatever level the naming conflict actually occurs (folder or file).
   - ❌ **Same operation FAILS on a Linux (agentless SSH) physical source** (PM-2): Activities
     showed `"The file recovery cannot be executed on the 'null' share. Target share cannot be
     opened"`, target logged as `null file Recovered-items-[...].zip`. The failure happens
     *before* the Rename logic ever engages — NBR can't resolve a share to write back to for this
     source type. The original file was confirmed untouched. **Recovery-to-original-location
     (any overwrite behavior) is therefore currently Linux-physical-specific BLOCKED(env)**, not a
     general product limitation — Windows physical sources work fine.
   - **Scope note (per product behavior):** "Recovery to original location" is only applicable to
     **File-Level Backup jobs and File Share Backup jobs** — not other job/backup types (e.g. VM
     image backups). Both tests above used `type:"FILE_LEVEL"` jobs, so job type was never the
     variable — the Linux failure is specific to that source's agentless write-back path.
   - The FLR Files-step root checkbox locator (`FILES_ROOT_CHECKBOX` in `locators.py`) was
     Windows-only (matched on a literal `'C:'` substring) and silently failed for a Linux-sourced
     backup — recalibrated 2026-07-08 to target the actual `<input class="gridCb">` inside the
     locked check-column panel, OS-agnostic now.
   - ⚠️ **Export ONE folder per `recover` call.** A single export with many `items` (11 folders) was
     observed to **hang** (`areActiveDownloads` stays true, no zip lands). Single-item export is fast +
     reliable. For many folders, loop one-at-a-time.
   - The CIFS/NFS share path + credentials are NOT auto-discoverable — ask the user.

4. **Evidence block (2026-07-14) — two DIFFERENT kinds of comparison; do not conflate them:**

   **(a) Listing-screenshot-pair — catches UI-vs-RPC divergence, shown as images.**
   A screenshot pair proving "we asked for X, we can recover X" at the file/folder-NAME level
   (names, counts, sizes/dates — NOT checksums, the Director UI has no checksum column anywhere).
   This is the exact pair that caught the Linux RPC-built-job defect (R4 note above): a
   `saveJob`-built job can return a clean `{result:"OK"}` and `lrState:OK` while the UI itself
   shows the wrong thing (partial-selected Source tree, or an empty FLR browse) — RPC responses
   alone cannot catch that, only the UI can.
   - **Screenshot A ("selected"):** right after build, open the job's **Edit** view in the
     Director UI → Source step → Select Items → screenshot the selected-items tree.
   - **Screenshot B ("recovered"):** after the run completes, open **Recover → File level
     recovery** (or File share recovery for FSB), browse to the same path, screenshot the file
     listing (names/sizes/dates visible).
   - Save both under `results/screenshots/<JIRA-ID>__<stamp>/` (e.g. `02_selected_items.png`,
     `03_flr_browse.png`) and embed them side-by-side in the runbook's evidence section.
   - **When to apply:** MANDATORY for **R4c-built (raw `saveJob`) Linux-source** jobs — this is
     where the divergence risk is real and proven. OPTIONAL/opportunistic for Windows R4c jobs
     (already validated clean across this Test Execution — see R4 note) and for R4e-built jobs
     (the build itself already went through the real UI wizard, so Screenshot A adds little; a
     single FLR-browse screenshot as a sanity check is enough there).

   **(b) Checksum-table — the actual content-verification proof, shown as TEXT, never an image.**
   A screenshot cannot show "checksums match" — no UI surface in Director renders a hash. For any
   TC that requires content verification, still do the real R7 step-3 flow (export/recover the
   file OUT to a CIFS/NFS share, hash it locally, diff against the manifest) and print the result
   as a markdown table directly in the runbook/report:
   ```
   | File | Expected SHA256 | Actual SHA256 | Match |
   |---|---|---|---|
   | sample.pdf | <hash> | <hash> | ✅ |
   ```
   A screenshot of the recovered file listing (from (a) above) is a fine supplementary visual but
   is **never a substitute** for this table — text is more precise, greppable, and diffable than a
   picture of a hash string.

---

## R8 — Screenshot via the UI (evidence)

```
python flb-automation/browser/nbr_ui.py --view jobs --out results/screenshots/<JIRA-ID>__<stamp>/stepN.png
```
Logs into `https://10.10.16.84:4443` (FLB) or `https://10.10.15.5:4443` (FSB) as test1,
navigates, saves a PNG. Run at the verify step and at any failed step. The report links the PNG.

---

## R9 — Cleanup (PASS only)

```
mcp__nbr__call nbr-84 JobManagement remove [<jobId>, false]   # FLB (nbr-5 for FSB). (id, keepPhysicalItems)
```
`keepPhysicalItems=false` deletes the job **and its backups** (recovery points); `true` keeps the
backups. Returns `{result: "OK"|"CANNOT_LOCK"}`.
Policy (confirmed): **delete on PASS, keep on FAIL** (failed jobs stay for debugging).
Safety: only ever remove a job whose name starts with `AUTO_FLB_` (FLB) or `AUTO_FSB_` (FSB).
