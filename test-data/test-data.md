# Test data — FLB automation

> The **single source of truth** for reusable test data. Every case reads from here.
> Cases must not invent their own values. See `environment.md` for connection fixtures.

## 1. The fileset ("general test data") — VERIFIED 2026-06-26

A fileset already lives in the source directory on each host. It is **reusable by any case**:
back it up, then verify the restored files match the recorded checksums. This section reflects
the **actual** content on the hosts (verified live), not an idealized layout.

### linux-src (`flb-linux` : `/TestData_ForFLB`) — **341 files, 28 dirs, 241,866,839 bytes (~242 MB)** — RE-VERIFIED 2026-07-08 (fileset grew from the old 110-file/235 MB set; manifest regenerated)

```
/TestData_ForFLB/
  (7 loose top-level files) 6× .mkv (short clips, ~0.2–1.4 MB each) + atest1.txt (5 bytes)
  Folder_test1/   33 files — full example set + large media + FLB project docs:
                  3× .mp4 (0.6–1.7 MB), 3× .mkv (incl. 87 MB 2026-06-04 09-42-11.mkv),
                  GIF/MP3/ODP/ODS/OGG/PDF/PPT/SVG/TIFF(10MB)/WAV(10MB)/WEBP/XLS/XLSX/XML/ICO/JSON,
                  file-sample_1MB.{doc,odt,rtf} (+ a duplicate "file-sample_1MB (1).doc"),
                  FLB_spec_body.txt, FLB_TCs_Missing_Step_Details.{csv,xlsx},
                  FLB_TC_Step_Templates.docx, Screenshot 2026-06-02 171940.png,
                  Test_Case_Automation_Feasibility_Assessor_v4.md
  Folder_test2/   21 files — the example-file set only (no large media, no docs)
  Folder_test3/   21 files — identical example-file set to Folder_test2
  FolderEmpty_test4/   NEW — empty folder (0 files) — for empty-folder backup coverage
  FolderEmpty_test5/   NEW — empty folder (0 files) — for empty-folder backup coverage
  ft_access/      sample_access.{accdb,mdb}
  ft_audio/       sample_audio.{flac,mp3,wav}
  ft_code/        sample_code.{c,cpp,h,java,js,py}
  ft_excel/       sample_excel.{xls,xlsb,xlsm,xlsx}
  ft_generic/     sample_generic.{bin,iso,txt,zip}
  ft_outlook/     sample_outlook.{ost,pst}
  ft_pdf/         sample_pdf.pdf
  ft_ppt/         sample_ppt.{potx,ppt,pptm,pptx}
  ft_psd/         sample_psd.{psb,psd}
  ft_video/       sample_video.{avi,mov,mp4}
  ft_word/        sample_word.{doc,docm,docx,dotx}
  Subfolder_200Folders/   NEW — 218 files across 4 top-level dirs (incl. nested Folder1/Folder2 +
                          an ft_video copy + ~200 Item_NNN.txt-style leaf files) — deep-nesting /
                          large-item-count coverage
  Wilcard_Recheck/   NEW — 10 files with glob-special names for inclusion/exclusion filter
                     testing: two**stars, [sa]bracket, *star, ???sa, {brace}set, plus
                     clip.mp4/report.mp4/data01/sales/sample
```
Note: the `Folder_test1/2/3` example files are byte-identical across the three folders
(same checksums), and `file-sample_1MB.doc` == `file-sample_1MB (1).doc`. The `ft_*` files are
small (~5–7 KB) format-coverage samples. `FolderEmpty_test4/5`, `Subfolder_200Folders`, and
`Wilcard_Recheck` are new additions (added between 2026-06-26 and 2026-07-08) not present in the
original 110-file set — likely purpose-built for empty-folder, deep-nesting, and
inclusion/exclusion-wildcard test cases respectively.

### windows-src (`win2019` : `C:\TestData_ForFLB`) — 110 files, **235,569,506 bytes (~235 MB)**

**Mirrored from Linux on 2026-06-26** — identical structure and byte-identical content
(`Folder_test1/2/3` + all 11 `ft_*` folders + large media). Parity verified: the per-file
SHA-256 sets of the two hosts match exactly (see below).

### Checksum manifests (verification oracle for FLR)

Full per-file SHA-256 **and** MD5 manifests are stored under `manifests/` next to this file and
were generated directly on each host (no transcription):

| Host | SHA-256 | MD5 |
|---|---|---|
| linux-src   | `manifests/manifest-linux.sha256` (341, **regenerated 2026-07-08**) | `manifests/manifest-linux.md5` (341, **regenerated 2026-07-08**) |
| windows-src | `manifests/manifest-windows.sha256` (110, stale — old set) | `manifests/manifest-windows.md5` (110, stale — old set) |

Manifest line format: `<hash>  <relative-path>` (Linux paths are `./…`; Windows are `sub\…`).
Re-generate after any change to the fileset:
- Linux: `cd /TestData_ForFLB && find . -type f -exec sha256sum {} \;` (or `md5sum`)
- Windows: `Get-ChildItem C:\TestData_ForFLB -Recurse -File | Get-FileHash -Algorithm SHA256`

### Host parity — BROKEN (as of 2026-07-08)

The two hosts **no longer hold the same fileset**. `linux-src` was extended (110 → 341 files,
235 MB → 242 MB — `FolderEmpty_test4/5`, `Subfolder_200Folders`, `Wilcard_Recheck`, and 7 loose
top-level files added) but `windows-src` was **not** re-mirrored and still holds the original
110-file/235 MB set. Do not assume a Linux-only case's fixtures (e.g. `Wilcard_Recheck`,
`Subfolder_200Folders`, the empty folders) exist on Windows — verify per-host before building a
case that needs them. `manifest-linux.*` is the current oracle for Linux content only;
`manifest-windows.*` is stale for the old Windows content only. To re-establish parity: tar the
Linux dir, serve it over `python3 -m http.server` from `flb-linux`, download on `win2019` via
`WebClient.DownloadFile`, wipe + `tar -xzf` into `C:\TestData_ForFLB`, then regenerate the
Windows manifests. (Note: `winrm_put` cannot carry multi-MB binaries — it hits the Windows
command-length limit; use the HTTP-pull path instead.) **Not done as part of this manifest
regen — only Linux was re-verified, per the explicit request.**

## 2. Job defaults (file-level physical backup) — updated 2026-07-06 (nbr-84)

| Field | Value |
|---|---|
| Appliance | `nbr-84` (FLB) |
| Job type | `FILE_LEVEL` |
| hvType | `PHYSICAL` |
| Name | `AUTO_FLB_<JIRA-ID>` (optionally `_<n>` if a case needs multiple jobs) |
| Target repository id | `2` (Onboard repository, LOCAL — fastest) or `7` (NFS_REPO) |
| Default source | per-case: `linux-src` (`PM-2`) and/or `windows-src` (`PM-3`) |
| Default source path | `linux-src`→`/TestData_ForFLB`, `windows-src`→`C:\TestData_ForFLB` |
| Schedule | none (manual run via `JobManagement.run`) |
| Retention | keep last 1 (cases that don't test retention) |

## 3. FLB reference job — RESOLVED 2026-07-06 (nbr-84); build method updated 2026-07-07;
## job 25 gone as of 2026-07-08

A real file-level job (`FLB_NFS_REPO`, job 25) existed on **nbr-84** and originally served as the
clone source (R4a, deprecated). Jobs are now built via **R4c** from the repo-owned
`test-data/job-templates/flb_job.template.json` (no dependency on this or any live job) — which is
exactly why this no longer matters operationally: **job 25 has since been removed from the
appliance** (re-verified 2026-07-08: `JobManagement.getJob(25)` errors "the object does not
exist"; `getJobId("FLB_NFS_REPO")` returns empty). R4c never depended on it and is unaffected;
R4a (already deprecated) simply has no golden source left to clone from at all now.

| Field | Value |
|---|---|
| Reference job name | `FLB_NFS_REPO` |
| Reference job id | `25` |
| hvType / type | `PHYSICAL` / `FILE_LEVEL` |
| Source machine | `objects[0].sourceVid = "PM-3"` (windows-src `Windown`) |
| Repository target | `objects[0].targetStorageVid = "BACKUP_REPOSITORY-7"` (NFS_REPO); use `-2` (Onboard) for fast runs |
| Top-level | `targetStorageType = "DISK"`, `containers = []` |

### Resolved payload conventions (the bits the spec left ambiguous)

- **Item selection** lives in `objects[0].mappings[]`. Each selected item is one entry with an
  explicit type:
  ```json
  { "type": "NORMAL", "sourceIdentifier": "C:/TestData_ForFLB/ft_code",             "sourceIdentifierType": "FOLDER" }
  { "type": "NORMAL", "sourceIdentifier": "C:/TestData_ForFLB/ft_pdf/sample_pdf.pdf", "sourceIdentifierType": "FILE"   }
  ```
  Paths use **forward slashes even on Windows**. Other mapping fields are null.
- ✅ **NEW build supports both FILE and FOLDER selection** (verified 2026-07-06, build 106315).
  The mapping carries **`sourceIdentifierType`** (`FOLDER` or `FILE`) — the old "folder-level only"
  limitation of nbr-149 (11.3.0) is **gone**. A single job may mix folder and file mappings; FLR
  browse confirms a `FILE` mapping restores just that one file, a `FOLDER` mapping the whole tree.
- **Repository** is referenced by VID `BACKUP_REPOSITORY-<id>` (e.g. `BACKUP_REPOSITORY-2`),
  NOT the null `vid` from `getBackupRepositories`.
- **Machine** is `objects[0].sourceVid` = the physical target VID (`PM-3` win, `PM-2` linux).
- For a Linux source, `sourceIdentifier` uses Linux paths, e.g. `/TestData_ForFLB/ft_code`.

See `recipes/file-backup-recipes.md` → R4 for the clone+patch procedure.

## 4. Backup Copy — VERIFIED WORKING (2026-07-08, nbr-84)

The retired nbr-149 had a BC golden template (job 96). Neither nbr-84 nor nbr-5 hosted a live
Backup Copy job as of 2026-07-07 — but Backup Copy is **not blocked**; it works, and the earlier
"BLOCKED" conclusion here was our own payload bug, since corrected:

- **First attempt (job 34, `AUTO_FLB_bctest_dryrun`, 2026-07-07):** `saveJob` accepted
  `type="BACKUP_COPY"`, `hvType="PHYSICAL"` (matched to the FLB source's own hvType) with
  `sourceVid="BACKUP_OBJECT-8"` → target `BACKUP_REPOSITORY-7` NFS_REPO
  (`{result:"OK", jobId:34}`). Running it failed **immediately** (~200ms, per the event log):
  action `BackupCopyEnforcePreconditions` threw
  `com.company.product.services.core.exceptions.FeatureNotSupportedException`, then NBR
  auto-retried every 15 minutes rather than terminal-failing — `crState` stayed `RUNNING` with
  `crProgress` frozen (see `recipes/file-backup-recipes.md` R6's warning on why
  `getJobShortInfo` alone missed this). Misdiagnosed at the time as a licensing/feature-flag gate.
- **Root cause found (2026-07-08):** the user built the equivalent job manually through the
  Director UI (job 35) and it ran successfully. Its DTO (`JobManagement.getJob(35)`) showed
  **`hvType:"VMWARE"` at the top level**, despite copying the same `PHYSICAL`/`FILE_LEVEL` FLB
  source — the wizard's own URL even defaults to `hv=VMWARE` before any source is picked. A
  Backup Copy job's top-level `hvType` is a **fixed value**, unrelated to the source's real type.
- **Confirmed via RPC (job 36, `AUTO_FLB_bctest_dryrun2`, 2026-07-08):** same source
  (`BACKUP_OBJECT-8`) → target `BACKUP_REPOSITORY-6` Wasabi (Disk-type destination), this time
  with `hvType:"VMWARE"`. `saveJob` OK → ran → `lrState:"OK"`, `lrVmOk:1` → real, accessible
  savepoint on Wasabi (`consumed:67208529`, matching the source almost exactly). Job removed
  cleanly afterward. Working now proven twice, across two different target repos (NFS and Wasabi).

**Conclusion:** Backup Copy **works** for FLB (`PHYSICAL`/`FILE_LEVEL`) sources on this build,
provided the job's top-level `hvType` is set to the fixed `"VMWARE"` value — this was purely a
payload bug on our side, not a licensing tier or product limitation (the appliance license is
`Enterprise Plus`, valid, "No Issues"). BC-dependent test cases should be re-evaluated
individually rather than blanket-BLOCKED — immutability specifically still needs a repo with
`backupImmutabilitySupport:true` (none of nbr-84's current repos have this — see
`environment.md`), and the Director UI's own wizard greys out `Tape` as a destination type (no
tape hardware) — those remain genuine, separate blockers where a test case depends on them.

Canonical, corrected shape now lives in
`test-data/job-templates/backup_copy_job.template.json`: `type=BACKUP_COPY`, `hvType="VMWARE"`
(fixed, always — do not parametrize this to the source), `sourceVid=BACKUP_OBJECT-<id>`, target a
*different* repo, `differentialTrackingMode="NONE"`, `retentionPolicy.retentionMode="RULESET"`
(only meaningful on a repo with immutability actually enabled), `mappings=[]`. Do NOT clone an FLB
job into a BC job. See `recipes/file-backup-recipes.md` R4d for the full recipe.

## 5. File Share Backup job shape — RESOLVED 2026-07-07 (nbr-5)

| Field | Value |
|---|---|
| Appliance | `nbr-5` (FSB) |
| Job build | **R4c** — self-contained canonical template `test-data/job-templates/fsb_job.template.json` (no live-job dependency; see recipe R4). Job 22 `Backup job for file share` remains as a read-only reference only. |
| type / hvType | `BACKUP` / **`NAS`** |
| Source | `objects[0].sourceVid = "FILE_SHARE-18"` (name `CIFS-FileTypeSamples`) |
| Target repo | `objects[0].targetStorageVid = "BACKUP_REPOSITORY-1"` (Onboard) — or `-2` Cloudian / `-3` Backblaze / `-4` Wasabi / `-5` Ceph / `-6` HPE |
| Options | `differentialTrackingMode="PROPRIETARY"` (OK for NAS — unlike BC) |
| Selection | `mappings[]` of individual files, each `sourceIdentifierType="FILE"` (file-level selection on the share root); `[]` = whole share |

Verified 2026-07-06 (R4a, historical): clone job 22 → `AUTO_FSB_newbuild_verify` (job 23, 3-file
subset) → run → `lrState:OK`, lrVmOk 1 → removed.
Verified 2026-07-07 (**R4c**, current default): built `AUTO_FSB_r4c_dryrun` straight from
`fsb_job.template.json` (no read of job 22) → `saveJob` (jobId 27, 1-file scope) → run
(`runType:ALL`) → **`lrState:OK`, lrVmOk 1** → removed after. NBR serializes jobs on the same
`FILE_SHARE-*` (a 2nd backup waits for the 1st; the queued run may show `lrState:STOPPED` then
restart — normal).
