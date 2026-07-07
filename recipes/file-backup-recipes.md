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
mcp__nbr__describe_method nbr-149 PhysicalDiscovery getFolders   # confirm 2-param shape first
mcp__nbr__call nbr-149 PhysicalDiscovery getFolders <args>
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
Creates a NEW job without reading/cloning job 25 or any live job. A clean appliance (sources
discovered + a repo online) is sufficient. The valid shape ships in the repo:
`test-data/job-templates/flb_job.template.json` (FSB: `fsb_job.template.json`).

```
1. Load the canonical skeleton  test-data/job-templates/flb_job.template.json → working copy.
   (single maintained artifact; NEVER read job 25.)
2. Patch ONLY the substitution-contract fields (modular "builders"):
   SourceBuilder      objects[0].sourceVid = "PM-2"|"PM-3" ; objects[0].targetName = "Linux_16.84"|"Windown"
   MappingBuilder     objects[0].mappings = [ {type:"NORMAL", sourceIdentifier:"<fwd-slash path>",
                        sourceIdentifierType:"FOLDER"|"FILE", sourceVid:null, targetVid:null, target:null,
                        availabilityZoneVid:null, securityGroupVids:null, primaryIp:null,
                        diskControllerType:null}, ... ]
   RepositoryBuilder  objects[0].targetStorageVid = "BACKUP_REPOSITORY-<id>"
   IdentityBuilder    name = "AUTO_FLB_<JIRA-ID>"  (id/lockUuid/options.id/objects[0].id stay null)
   BackupOptionsBuilder (ONLY when the TC needs it; else keep defaults):
                        options.backupEncryptionMode + options.encryptionPasswordId ;
                        options.accessControlList = FOLDER_PERMISSIONS|FOLDER_AND_FILE_PERMISSIONS ;
                        options.applicationAwareMode ; options.differentialTrackingMode
   ScheduleBuilder    schedules = []  (on-demand)  OR a real schedule (immutability REQUIRES a schedule)
3. ValidationBuilder — FAIL FAST → report BLOCKED before saveJob unless ALL hold:
   • source present & OK (R1)  • repo present & OK (R3)  • mappings non-empty, fwd slashes,
     sourceIdentifierType ∈ {FOLDER,FILE}  • name starts with AUTO_FLB_  • no __PLACEHOLDER__ tokens left
4. Strip the _README/_SUBSTITUTION keys, then (introspect once per session) saveJob:
   mcp__nbr__describe_method nbr-84 JobManagement saveJob
   mcp__nbr__call nbr-84 JobManagement saveJob {"origin":"NONE","job":<patched>}   (args_path — large)
   Expect { result:"OK", jobId:<n> } → a NEW independent job; no live template touched.
```

> **Self-healing / maintenance:** one repo-owned template → no job-25 coupling, portable to any
> appliance, deterministic. If `saveJob` ever rejects a field (spec drift / new required field),
> fix the **single** template file and every runbook inherits it. `describe_method` before the
> first write catches drift early. Verified shape vs NBR 11.2.1 (build 106315).

**R4a — Clone the golden template (DEPRECATED — emergency fallback only).** Couples every generated
job to live job 25 (must exist and stay unchanged) — avoid. Kept only for when the canonical
template is missing/stale. Reuse the proven `options` block verbatim; only patch identity, source,
target, and item selection.

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
> NJM-122651 Volume/File steps are back in scope (VOLUME not yet tested on this build).

**R4b — From scratch (only if no template).** Build the full `JobDto`
(`type="FILE_LEVEL"`, `hvType="PHYSICAL"`, full `options`, `objects[0]` as above). Large/brittle
— prefer R4a. A copy of the proven shape is always available live via `getJobForEditing(25,null)`.

Record on success: `jobId` and `SaveJobResponseDto.result == "OK"`.

> Verified 2026-07-06: cloned job 25 → `AUTO_FLB_newbuild_verify` (job 26, one FOLDER + one FILE)
> → run → `lrState:OK` → FLR-browsed → cleaned up. The create path is exercised end to end.

**File Share Backup (nbr-5):** same `saveJob` shape but clone golden **job 22** (`type="BACKUP"`,
`hvType="NAS"`, `sourceVid="FILE_SHARE-18"`, `differentialTrackingMode="PROPRIETARY"`); mappings
are per-file `sourceIdentifierType="FILE"` entries on the share. See `test-data.md §5`.

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

Capture the run result + any alert/error text into the report.

---

## R7 — Verify the backup (savepoint + FLR)  (CALIBRATED NJM-122651)

1. **Savepoint:** `JobManagement.getSavepoints ["BACKUP_OBJECT-<id>", 5]` → savepoint `id` (=spId),
   `isAccessible`, `checkState`. Find `BACKUP_OBJECT-<id>` via `getJob [<jobId>]` →
   `objects[0].targetVid` (populated after the first successful run).
2. **FLR mount + browse (non-destructive — strong verification), FLB → nbr-84:**
   - `FileLevelRecoveryManagement.createSession [{"hvType":"PHYSICAL","type":"BACKUP_OBJECT","id":<boId>,"spId":<spId>}]` → `sessionUuid` (spId is REQUIRED)
   - poll `getState [sessionUuid]` until `state:"ACTIVE"` (also keeps the session alive — it times out ~1 min)
   - `list [sessionUuid, null, "NORMAL", "FS_ROOT", 0, 100]` → root = the selected folders (proves folder scope)
   - `list [sessionUuid, "<C:\\...\\folder\\>", "NORMAL", "NORMAL", 0, 200]` → files with name + size; compare to the manifest
   - `closeSession [sessionUuid, false]` when done
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
   - ⚠️ **Export ONE folder per `recover` call.** A single export with many `items` (11 folders) was
     observed to **hang** (`areActiveDownloads` stays true, no zip lands). Single-item export is fast +
     reliable. For many folders, loop one-at-a-time.
   - The CIFS/NFS share path + credentials are NOT auto-discoverable — ask the user.

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
