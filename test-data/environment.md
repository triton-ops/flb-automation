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
- `linux-src` (`flb-linux`) holds `/TestData_ForFLB` (341 files, ~242 MB — `ft_*` folders,
  media, `Subfolder_200Folders`); this differs from the old set, so re-gen a manifest before
  checksum-verifying Linux content.

## FLB target repositories (nbr-84)

| Name | id | Type | State | Notes |
|---|---|---|---|---|
| Onboard repository | `2` | LOCAL (`/opt/nakivo/repository`) | OK | objectLock supported; fastest — default for quick runs |
| NFS_REPO | `7` | NFS_SHARE (`10.10.15.3:/NFS_Share_Win`) | OK | target of golden job 25 |
| Ceph_S3 | `8` | S3_COMPATIBLE | OK | |
| Wasabi_Repo | `6` | WASABI | OK | |
| CIFS_REPO | `3` | SHARE (`\\10.10.15.211\CIFS_Source`) | **INACCESSIBLE** | do not use |

- Reference by VID `BACKUP_REPOSITORY-<id>` (e.g. `BACKUP_REPOSITORY-2`).
- FLB golden template: **job 25 `FLB_NFS_REPO`** — read via `getJobForEditing(25, null)`.

## FSB source + repositories (nbr-5)

| Item | Value |
|---|---|
| File share source | `FILE_SHARE-18` (name `CIFS-FileTypeSamples`) — holds a `sample.*` file-type set |
| FSB golden template | **job 22 `Backup job for file share`** — `getJobForEditing(22, null)` |
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
