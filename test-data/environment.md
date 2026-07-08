# Environment — FLB automation

> Connection-level facts. Everything here is a fixture: cases reference these names,
> never hardcode addresses or VIDs. If the lab changes, update this file only.
>
> **Re-verified live 2026-07-06.** The old single appliance `nbr-149` (10.10.15.149) was
> uninstalled. There are now **two** appliances, split by area. The old PM-9/PM-10 Windows-source
> discrepancy is resolved by this migration (those VIDs belonged to the retired nbr-149).

## Appliances (NBR Directors — RPC targets)

| nbr MCP alias | Address | Product | Role | User |
|---|---|---|---|---|
| **`nbr-84`** | `10.10.16.84:4443` | NBR 11.2.1 (build 106315) | **File-Level Backup (FLB)** | `test1` |
| **`nbr-5`**  | `10.10.15.5:4443`  | NBR 11.2.1 (build 106316) | **File Share Backup (FSB)** | `test1` |

All RPC calls use `mcp__nbr__call` with `alias="nbr-84"` (FLB) or `alias="nbr-5"` (FSB).
UI (screenshots): `https://10.10.16.84:4443` / `https://10.10.15.5:4443`.

> ⚠️ Pick the appliance by area: **FLB jobs → `nbr-84`**, **File Share Backup jobs → `nbr-5`**.
> They are separate Directors with independent inventories.

## FLB sources (nbr-84 — physical machines, discovered, state OK)

| Logical name | OS | NBR target VID | NBR discovery VID | remoting alias | Source directory |
|---|---|---|---|---|---|
| `linux-src`  | Linux   | `PM-2` | `PHYSICAL_DISCOVERY_ITEM-1` | `flb-linux` (10.10.16.84, ssh root)   | `/TestData_ForFLB` |
| `windows-src`| Windows | `PM-3` | `PHYSICAL_DISCOVERY_ITEM-2` | `win11` (10.10.16.157, winrm `test`)  | `C:\TestData_ForFLB` |

- **NBR side** (backup source selection): use the **target VID** (`PM-2` / `PM-3`).
- **remoting side** (seed/verify files on the host): use the **remoting alias** (`flb-linux` / `win11`).
- `windows-src` (`win11`) holds the known **110-file / 235,569,506-byte** `C:\TestData_ForFLB`
  fileset — **byte-identical** to `manifest-windows.sha256` (parity re-verified 2026-07-06),
  so the stored manifest is still the FLR oracle. It also has a large `C:\Data_25GB` (8 ISOs, ~18.8 GB).
- `linux-src` (`flb-linux`) holds `/TestData_ForFLB` (341 files, 28 dirs, 241,866,839 bytes
  ~242 MB — `ft_*` folders, media, `Subfolder_200Folders`, `Wilcard_Recheck`,
  `FolderEmpty_test4/5`, plus loose top-level files); differs from the old 110-file set.
  **Manifest regenerated 2026-07-08** — `manifests/manifest-linux.sha256`/`.md5` (341 entries
  each) are current; see `test-data.md` §1 for the full breakdown and the now-broken host-parity
  note (`windows-src` was not re-mirrored, still holds the old 110-file set).

## FLB target repositories (nbr-84)

| Name | id | Type | State | Notes |
|---|---|---|---|---|
| Onboard repository | `2` | LOCAL (`/opt/nakivo/repository`) | OK | `objectLockSupported:true`, but `backupImmutabilitySupport:false` (no active immutable policy); fastest — default for quick runs |
| NFS_REPO | `7` | NFS_SHARE (`10.10.15.3:/NFS_Share_Win`) | OK | no immutability support |
| Wasabi_Repo | `6` | WASABI | OK | no immutability support (`objectLockSupported:false`) |
| **Wasabi-immutable** | `17` | WASABI (`s3://s3.ap-northeast-2.wasabisys.com/tuan-immutable`) | OK (fixed 2026-07-08) | import issue resolved by the user — now `isAccessible:true`, `attached:true`, **`objectLockSupported:true`**. Already has pre-existing backups on it (`backupCount:9`, imported history). |
| CIFS_REPO | `3` | SHARE (`\\10.10.15.211\CIFS_Source`) | **INACCESSIBLE** | do not use |
| ~~Ceph_S3~~ | ~~`8`~~ | ~~S3_COMPATIBLE~~ | **REMOVED 2026-07-08** | unstable, replaced by `Cloudian` (id `14`) per explicit user request — do not reference id 8 in new work |
| Cloudian | `14` | S3-compatible (`s3://s3-cloudian213.nakivo.vno:443/tri-cloudian-test1`) | OK | added 2026-07-08 (Ceph_S3 replacement); no immutability support (`objectLockSupported:false`) |
| **Cloudian-immutable** | `16` | S3-compatible (`s3://s3-cloudian213.nakivo.vno:443/tri-cloudian-immutable`) | OK | added 2026-07-08; **`objectLockSupported:true`** — use this for any Ceph_S3-immutable test case that was substituted to Cloudian (e.g. NJM-123185) |
| Amazon_Repo | `9` | AWS S3 (`s3://s3.ap-east-1.amazonaws.com/tri-s3-amazon`) | OK | added 2026-07-08; no immutability support (`objectLockSupported:false`) |
| **Amazon_Immutable** | `10` | AWS S3 (`s3://s3.ap-east-1.amazonaws.com/tri-s3-ama-immutable`) | OK | added 2026-07-08; **`objectLockSupported:true`** (Object Lock capability present at the storage layer — `backupImmutabilitySupport` still shows `false` until a job actually creates an immutable savepoint here) |
| Azure_Repo | `11` | AZURE_BLOB (`azure://tritonimmutable.blob.core.windows.net/repo-azure-test1`) | OK | added 2026-07-08; **`objectLockSupported:true`** |
| **Azure_Immutable** | `12` | AZURE_BLOB (`azure://tritonimmutable.blob.core.windows.net/repo-immutable-test1`) | OK | added 2026-07-08; **`objectLockSupported:true`** |
| **BlackBlaze_Immutable** | `13` | BACKBLAZE (`backblaze://s3.us-west-004.backblazeb2.com/tri-immutable-bucket1`) | OK | added 2026-07-08; **`objectLockSupported:true`** |
| **Local-Immutable** | `15` | LOCAL (`/Local_repo`) | OK (fixed 2026-07-08) | re-added/fixed by the user — now `isAccessible:true`, **`objectLockSupported:true`**. (Immutability is still applied via the job-level `retentionPolicy.retentionMode="RULESET"` option — this repo, like Onboard, just needs that option set on the job; either repo works, but this one matches the TC's literal "Local Linux" intent more directly.) |

> ⚠️ None of the repos above — including the `*_Immutable`-named ones — have actually produced an
> immutable savepoint yet (`backupImmutabilitySupport:false` on all of them, re-verified
> 2026-07-08). `objectLockSupported:true` means the storage layer/bucket has Object Lock capability
> — it does NOT by itself prove NBR can successfully write an immutable savepoint there. Treat
> immutability-dependent test cases as newly **buildable** (repo now exists with the right
> capability flag), not as **pre-verified passing** — the actual `retentionPolicy.retentionMode`
> + immutable-savepoint creation path has not been live-tested end-to-end yet.

- Reference by VID `BACKUP_REPOSITORY-<id>` (e.g. `BACKUP_REPOSITORY-2`).
- FLB jobs build via **R4c** from `test-data/job-templates/flb_job.template.json` (self-contained).
  **Job 25 `FLB_NFS_REPO` no longer exists** (re-verified 2026-07-08: `JobManagement.getJob(25)`
  errors "the object does not exist"; `getJobId("FLB_NFS_REPO")` returns empty) — it is gone from
  the appliance, not merely a stale reference. This has no effect on R4c (never depended on it);
  it only means R4a (deprecated clone-based builder) has no golden source left to clone from.
- **Backup Copy (BC) jobs work** on this build for FLB sources — see
  `recipes/file-backup-recipes.md` R4d. The one gotcha: a BC job's top-level `hvType` must be the
  fixed value `"VMWARE"`, regardless of what it's actually copying.

## Tape (nbr-84) — added 2026-07-08

| Item | Value |
|---|---|
| Tape library | `VLT_Tape` (`TAPE_LIBRARY-1`, device id `1`) — HP D2DBS emulation, 8 cartridges, 1 drive, 9 slots |
| State | `OK`, `attached:true` |
| Media pool | `test1` (id `1`), linked to the library (`mediaPoolId:1`) |
| Transporter | `10.10.15.3` (win-fs3) |

Individual cartridge readiness (formatted/blank vs. needs erase) has **not** been confirmed —
check `TapeCartridgeManagement.getCartridges` live before the first tape-dependent run this
session (exact filter shape not yet calibrated — introspect/experiment before use, per CLAUDE.md
rule 2). Backup-to-tape is done via a **Backup Copy Job** (R4d) targeting the tape library/media
pool rather than a disk repository — the exact job-payload shape for a tape destination is
uncalibrated; confirm via `describe_method` before first use.

## FSB source + repositories (nbr-5)

| Item | Value |
|---|---|
| File share source | `FILE_SHARE-18` (name `CIFS-FileTypeSamples`) — holds a `sample.*` file-type set |
| FSB job build | **R4c** from `test-data/job-templates/fsb_job.template.json` (self-contained, no live-job dependency) |
| FSB reference job (read-only) | **job 22 `Backup job for file share`** — `getJobForEditing(22, null)` |
| Repositories | Onboard `1` (LOCAL, OK), Backblaze `3`, Ceph `5`, Cloudian `2`, HPE `6`, Wasabi `4` (all OK) |

## Transporters

- nbr-84: `Onboard transporter` (`TRANSPORTER-1`), `Linux_Tranporter_15.62` (`TRANSPORTER-7`, backs the S3/NFS/Wasabi repos).
- nbr-5: `Onboard transporter` (`TRANSPORTER-1`).

## Remoting hosts (host access — already registered)

| Alias | Address | Proto | Role |
|---|---|---|---|
| `flb-linux` | 10.10.16.84 | ssh (root) | FLB Linux source (also the FLB Director host) |
| `win11` | 10.10.16.157 | winrm (`test`) | FLB Windows source (`Windown` / PM-3) |
| `win-fs3` | 10.10.15.3 | winrm (Administrator) | NFS/CIFS share host (repo backing + FLR export target) |
| `win2019` | 10.10.15.211 | winrm (Administrator) | legacy Windows host / CIFS_REPO backing |

## Conventions

- Job name prefix: **`AUTO_FLB_`** (FLB) / **`AUTO_FSB_`** (File Share Backup) →
  a case for `NJM-1234` creates `AUTO_FLB_NJM-1234` on nbr-84 (or `AUTO_FSB_NJM-1234` on nbr-5).
- Cleanup: on **PASS**, delete the job and its backups (`remove(id, false)`); on **FAIL**, leave them.
- Claude must **never** touch any host/job/repository whose name does not start with `AUTO_FLB_`/
  `AUTO_FSB_`. Golden templates (jobs 25 / 22) and all discovered sources/repos/shares are
  **read-only references** — never delete or edit them.
