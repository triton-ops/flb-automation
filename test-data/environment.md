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
| `linux-src`  | Linux (Ubuntu Server 24.04.3 LTS, `ext4` root fs) | `PM-2` | `PHYSICAL_DISCOVERY_ITEM-1` | `flb-linux` (10.10.16.84, ssh root)   | `/TestData_ForFLB` |
| `windows-src`| Windows (Windows 11 Pro, `NTFS` root fs; also has a small unlettered `FAT32` system-reserved partition — not test-data-suitable) | `PM-3` | `PHYSICAL_DISCOVERY_ITEM-2` | `win11` (10.10.16.157, winrm `test`)  | `C:\TestData_ForFLB` |
| `win-fs3-src`| Windows Server 2019 Datacenter — added 2026-07-13 as an FLB source (was previously only the NFS/CIFS share host + FLR export target, see below; that role is unchanged, this is an additional use of the same discovered machine). Volumes: `C:` NTFS, `E:` **FAT (FAT16)** ~1.1GB, unlettered `FAT32` system-reserved (99MB, not test-data-suitable) | `PM-9` | `PHYSICAL_DISCOVERY_ITEM-6` | `win-fs3` (10.10.15.3, winrm `Administrator`) | TBD per case (e.g. `E:\` for FAT16 coverage) |
| `win2022-src`| Windows Server 2022 Datacenter — **REPLACED 2026-07-20**: the original VM (10.8.81.58) went down; a fresh VM was deployed at a new address. Old NBR discovery entry (`PM-11`/`PHYSICAL_DISCOVERY_ITEM-7`) is stale until re-discovered against the new IP — **not yet re-discovered in NBR Inventory as of this entry**, so the `win2022` remoting alias works (WinRM seeding/verification) but no FLB job can target this machine by NBR display name until discovery is redone. Volumes recreated to match the original role: `C:` NTFS (system, 149GB), `F:` NTFS (10GB, disk 0), `E:` **ReFS** (15GB, disk 2), `A:` **FAT32** (20GB, disk 3, added 2026-07-20). Seeded: `C:\TestData_ForFLB\MixedTypes` (7-file convention, manifest `manifest-win2022-mixed.sha256` — regenerated 2026-07-20; docx/jpg/mp4/sys hashes byte-identical to the old host's deterministic content, pdf/xml/json/differ since exact legacy text wasn't recoverable from a hash alone) and `E:\FSCoverage_ForFLB\keep.txt` (NJM-123274's ReFS fixture, manifest `manifest-refs-fscoverage.sha256` — regenerated, same logical content as before but a different hash due to a BOM/encoding difference between PowerShell's `Set-Content -Encoding UTF8` (adds BOM) and `[IO.File]::WriteAllText` (no BOM)). | `PM-11` (stale) | `PHYSICAL_DISCOVERY_ITEM-7` (stale) | `win2022` (10.10.15.158, winrm `Administrator`) | `F:\`/`E:\`/`A:\` for NTFS/ReFS/FAT32 coverage; `C:\TestData_ForFLB\MixedTypes` for OS-support/app-aware tests |
| `win2016-src`| Windows Server 2016 Datacenter Evaluation — added 2026-07-13 via `PhysicalDiscovery.create` (NJM-67697 OS-support coverage); newly discovered (not previously in inventory) | `PM-12` | `PHYSICAL_DISCOVERY_ITEM-8` | `win2016` (10.10.15.19, winrm `Administrator`) | `C:\TestData_ForFLB` (to be seeded) |
| `win2025-src`| Windows Server 2025 Datacenter Evaluation — added 2026-07-13 via `PhysicalDiscovery.create` (NJM-67692 OS-support coverage); newly discovered. **Note:** target VID shifted from `PM-13` to `PM-19` after a re-discovery — `PM-19` is current | `PM-19` | `PHYSICAL_DISCOVERY_ITEM-13` | `win2025` (10.10.15.245, winrm `Administrator`) | `C:\TestData_ForFLB\MixedTypes` — seeded, manifest `manifest-win2025-mixed.sha256` |
| `ubuntu22-desktop-src`| Ubuntu 22.04 LTS **Desktop** (`ubuntu-desktop`/`ubuntu-desktop-minimal` packages present, `ext4` root fs) — added 2026-07-13 via `PhysicalDiscovery.create` (NJM-67816 coverage); newly discovered | `PM-14` | `PHYSICAL_DISCOVERY_ITEM-10` | `ubuntu22` (10.10.16.98, ssh `root`) | `/TestData_ForFLB` (to be seeded) |
| `ubuntu22-xfs-vol` | Same physical machine as `ubuntu22-desktop-src` (PM-14) — a second, dedicated disk (`/dev/sdb1`, 16GB, GPT) added 2026-07-13 by the user and formatted **XFS** (label `XFS_TestData`, mounted at `/mnt/xfs_testdata`, persisted in `/etc/fstab` by UUID) for NJM-68934 (XFS filesystem coverage) | `PM-14` | `PHYSICAL_DISCOVERY_ITEM-10` | `ubuntu22` (10.10.16.98, ssh `root`) | `/mnt/xfs_testdata/TestData_XFS` — seeded 2026-07-13, 5 files (~3.1MB): `readme.txt`, `docs/notes.txt`, `docs/sample.json`, `media/blob_1mb.bin`, `media/blob_2mb.bin` |
| `ubuntu24-desktop-src`| Ubuntu 24.04.4 LTS **Desktop** (`ubuntu-desktop-minimal` package present, `ext4` root fs) — added 2026-07-13 via `PhysicalDiscovery.create` (NJM-67817 coverage); newly discovered | `PM-15` | `PHYSICAL_DISCOVERY_ITEM-11` | `ubuntu24` (10.10.16.119, ssh `root`) | `/TestData_ForFLB` (to be seeded) |
| `almalinux9-src`| AlmaLinux 9.4 (Seafoam Ocelot), `xfs` root fs — added 2026-07-13 via `PhysicalDiscovery.create` (NJM-67813 coverage). **First attempt failed** (`state:INACCESSIBLE`, "deployed physical agent is inaccessible") because `firewalld` on this host only allowed `cockpit/dhcpv6-client/ssh` — the NAKIVO agent port **9446/tcp** (confirmed via `flb-linux`'s own `bhsvc` transporter process) was blocked. Fixed by `firewall-cmd --permanent --add-port=9446/tcp && firewall-cmd --reload` on the host, then retried via `PhysicalDiscovery.update` (needs a `confirmed:true` field the initial `create` didn't require) — succeeded | `PM-17` | `PHYSICAL_DISCOVERY_ITEM-12` | `almalinux9` (10.10.16.48, ssh `root`) | `/TestData_ForFLB/MixedTypes` — seeded, manifest `manifest-almalinux9-mixed.sha256` |
| `rocky9-src` | Rocky Linux 9.5 (Blue Onyx) — pre-added to nbr-84 inventory (not by this automation session) | `PM-22` | `PHYSICAL_DISCOVERY_ITEM-15` | `rocky9` (10.10.16.150, ssh `root`) | `/TestData_ForFLB/MixedTypes` — seeded, manifest `manifest-rocky9-mixed.sha256` |
| `debian12-src` | Debian GNU/Linux 12 (bookworm) — pre-added to nbr-84 inventory (not by this automation session) | `PM-23` | `PHYSICAL_DISCOVERY_ITEM-16` | `debian12` (10.10.16.202, ssh `root`) | `/TestData_ForFLB/MixedTypes` — seeded, manifest `manifest-debian12-mixed.sha256` |
| `sles15-src` | SUSE Linux Enterprise Server 15 SP6 — pre-added to nbr-84 inventory (not by this automation session) | `PM-20` | `PHYSICAL_DISCOVERY_ITEM-14` | `sles15` (10.10.15.205, ssh `root`) | `/TestData_ForFLB/MixedTypes` — seeded, manifest `manifest-sles15-mixed.sha256` |
| `rhel9-src` | Red Hat Enterprise Linux 9.5 (Plow) — machine came up 2026-07-14 (10.10.16.115); discovery first failed identically to the AlmaLinux9 case (`firewalld` blocking `9446/tcp`), fixed the same way, then confirmed via `PhysicalDiscovery.update` | `PM-28` | `PHYSICAL_DISCOVERY_ITEM-18` | `rhel9` (10.10.16.115, ssh `root`) | `/TestData_ForFLB/MixedTypes` — seeded 2026-07-14 via SSH, manifest `manifest-rhel9-mixed.sha256` |

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
| ~~NFS_REPO~~ | ~~`7`~~ | ~~NFS_SHARE (`10.10.15.3:/NFS_Share_Win`)~~ | **REMOVED (confirmed live 2026-07-23)** | no longer offered in the FLB wizard's Destination-step repo picker — searching that combo for "NFS" returns "No matching items found." (a same-session search for "Onboard" DID match, ruling out a locator/search bug). Blocks NJM-83372 until a real NFS-Share-type repository is re-added. |
| ~~Wasabi_Repo~~ | ~~`6`~~ | ~~WASABI~~ | **REMOVED (confirmed live 2026-07-23)** | plain non-immutable Wasabi repo no longer offered in the wizard's Destination combo — only `Wasabi-immutable` below remains. Any TC that assumed a plain (non-immutable) Wasabi target must reuse `Wasabi-immutable` instead (same substitution convention already used for Backblaze — see `BlackBlaze_Immutable`'s own note). |
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
| SynologyC2 | — | Synology C2 Object Storage | OK (confirmed live 2026-07-23) | Previously blocked (NJM-123129/123130) as "no Synology C2 repository configured" — a repo now exists and is reachable. Display name is `SynologyC2` (no underscore) — an earlier finding recorded it as `Synology_C2`/`Synology_C2_Immutable` (two separate repos), which was wrong on both counts: it's one repo, one word. Immutability (NJM-123130) is applied via the same job-level 'Immutable for N days' option as Local-Immutable/Onboard, not a separate `_Immutable`-named repo. |

> ⚠️ None of the repos above — including the `*_Immutable`-named ones — have actually produced an
> immutable savepoint yet (`backupImmutabilitySupport:false` on all of them, re-verified
> 2026-07-08). `objectLockSupported:true` means the storage layer/bucket has Object Lock capability
> — it does NOT by itself prove NBR can successfully write an immutable savepoint there. Treat
> immutability-dependent test cases as newly **buildable** (repo now exists with the right
> capability flag), not as **pre-verified passing** — the actual `retentionPolicy.retentionMode`
> + immutable-savepoint creation path has not been live-tested end-to-end yet.
>
> **UPDATE 2026-07-18 (via the UI wizard, NJM-70517 calibration) — this now HAS been proven for
> Local-Immutable.** Built `AUTO_FLB_IMMUT_CALIB` (Window11 -> Local-Immutable) through the
> real 6-step FLB wizard with the Schedule step's 'Immutable for 1 day(s)' ticked
> (`FlbWizardPage.set_immutable(1)`), ran it to completion (`Successful`), then opened its
> recovery point's own detail grid (Settings -> Repositories -> Local-Immutable -> Window11):
> two columns not visible without horizontal scroll, 'Immutable until' and 'Protected until',
> show real computed values (created-time + 1 day / + 10 days) — a genuinely immutable
> savepoint. Deleting the JOB (Manage -> Delete) is NOT blocked — the job disappears from the
> Jobs sidebar normally — but the underlying BACKUP/recovery point is NOT removed from the
> repository; it survives as an orphaned ('no job') entry until the immutable window elapses.
> So the real protection is repo-level DATA survival, not a blocked Delete click. See
> `browser/checks/check_immutability_calibration.py` for the reproducing script; the RPC-level
> `backupImmutabilitySupport` flag noted above may simply not reflect this (it was never
> re-checked via RPC after this UI-driven run — an open cross-check, see Golden Rule 2).
>
> **UPDATE 2026-07-19 — the 'job delete leaves the backup behind' behavior above was a POM gap,
> not solely a product default.** The 'Delete this job?' dialog (once a job has a real recovery
> point) offers a 'Delete scope:' radio defaulting to 'Delete the job and keep the backups' — a
> second radio, 'Delete the job and the backups' (behind its own follow-up 'Permanently delete...'
> confirm), actually removes both. `JobManagementPage.delete_job()` — used by every suite's
> `flb_job_cleanup` fixture — now selects that second option. This means every prior test run in
> this project's history left its backup behind by default; the two orphaned `AUTO_FLB_IMMUT_CALIB`
> backups on Local-Immutable from the run above are one visible instance of this (harmless,
> self-clearing once their immutability window elapses — see the entry itself for the date).
>
> ⚠️ Repository-level maintenance actions (self-healing, reclaim unused space, repair,
> verify-all-backups — `RepositoryManagementPage`, added alongside this) act on the WHOLE
> repository, not just your own `AUTO_FLB_*` data, and require the user's explicit go-ahead each
> time before running — see CLAUDE.md's Golden Rule 3. Do not run these routinely as part of a
> test suite.

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
| FSB reference job (read-only) | **job 22 `Backup job for file share`** — `getJobForEditing(22, null)`. Still exists (confirmed live 2026-07-08 — don't assume removed just because the nbr-84 golden job 25 is) — target `BACKUP_OBJECT-26`, savepoint id `44`, `isAccessible:true`. Used for File Share Recovery calibration: `FileLevelRecoveryManagement.createSession` needs `hvType:"NAS"` (not `"PHYSICAL"`) for this backup object — see recipes/file-backup-recipes.md R7 |
| Repositories | Onboard `1` (LOCAL, OK), Backblaze `3`, Ceph `5`, Cloudian `2`, HPE `6`, Wasabi `4` (all OK) |

## Transporters

- nbr-84: `Onboard transporter` (`TRANSPORTER-1`), `Linux_Tranporter_15.62` (`TRANSPORTER-7`, backs the S3/NFS/Wasabi repos).
- nbr-5: `Onboard transporter` (`TRANSPORTER-1`).

## Remoting hosts (host access — already registered)

| Alias | Address | Proto | Role |
|---|---|---|---|
| `flb-linux` | 10.10.16.84 | ssh (root) | FLB Linux source (also the FLB Director host) |
| `win11` | 10.10.16.157 | winrm (`test`) | FLB Windows source (`Windown` / PM-3) |
| `win-fs3` | 10.10.15.3 | winrm (Administrator) | NFS/CIFS share host (repo backing + FLR export target); **also** an FLB source as of 2026-07-13 (`win-fs3-src` / PM-9, NJM-182726 filesystem coverage — dual role, the share-host use is unchanged) |
| `win2019` | 10.10.15.211 | winrm (Administrator) | legacy Windows host / CIFS_REPO backing — **unreachable 2026-07-13** (WinRM connect timeout); not currently a viable FLB source |
| `win2022` | 10.10.15.158 | winrm (Administrator) | FLB source `win2022-src` (Windows Server 2022 Datacenter) — **re-pointed 2026-07-20** to a fresh VM (old 10.8.81.58 went down); NBR Inventory discovery not yet redone against this new address, see `win2022-src`'s own row above |
| `win2016` | 10.10.15.19 | winrm (Administrator) | FLB source `win2016-src` / PM-12 (Windows Server 2016 Datacenter Evaluation) — added 2026-07-13 for NJM-67697 |
| `win2025` | 10.10.15.245 | winrm (Administrator) | FLB source `win2025-src` / PM-13 (Windows Server 2025 Datacenter Evaluation) — added 2026-07-13 for NJM-67692 |
| `ubuntu22` | 10.10.16.98 | ssh (root) | FLB source `ubuntu22-desktop-src` / PM-14 (Ubuntu 22.04 LTS Desktop) — added 2026-07-13 for NJM-67816 |
| `ubuntu24` | 10.10.16.119 | ssh (root) | FLB source `ubuntu24-desktop-src` / PM-15 (Ubuntu 24.04 LTS Desktop) — added 2026-07-13 for NJM-67817 |
| `almalinux9` | 10.10.16.48 | ssh (root) | FLB source `almalinux9-src` / PM-17 (AlmaLinux 9.4) — added 2026-07-13 for NJM-67813; required opening `9446/tcp` in `firewalld` on the host (see fixture note above) |
| `rocky9` | 10.10.16.150 | ssh (root) | FLB source `rocky9-src` / PM-22 (Rocky Linux 9.5) — for NJM-67702 |
| `debian12` | 10.10.16.202 | ssh (root) | FLB source `debian12-src` / PM-23 (Debian GNU/Linux 12) — for NJM-67806 |
| `sles15` | 10.10.15.205 | ssh (root) | FLB source `sles15-src` / PM-20 (SLES 15 SP6) — for NJM-67809 |
| `rhel9` | 10.10.16.115 | ssh (root) | FLB source `rhel9-src` / PM-28 (RHEL 9.5) — for NJM-67808; came up 2026-07-14, required opening `9446/tcp` in `firewalld` (same fix as `almalinux9`) |

## Conventions

- Job name prefix: **`AUTO_FLB_`** (FLB) / **`AUTO_FSB_`** (File Share Backup) →
  a case for `NJM-1234` creates `AUTO_FLB_NJM-1234` on nbr-84 (or `AUTO_FSB_NJM-1234` on nbr-5).
- Cleanup: on **PASS**, delete the job and its backups (`remove(id, false)`); on **FAIL**, leave them.
- Claude must **never** touch any host/job/repository whose name does not start with `AUTO_FLB_`/
  `AUTO_FSB_`. Golden templates (jobs 25 / 22) and all discovered sources/repos/shares are
  **read-only references** — never delete or edit them.
