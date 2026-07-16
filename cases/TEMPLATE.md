<!--
Runbook template. Claude fills this in from a Jira TC, then executes it.
One file per testcase: cases/<JIRA-ID>.md  (e.g. cases/QA-1234.md)
Keep steps explicit and checkable. Reference recipes (R1..R9) and test-data, never hardcode.
-->

# <JIRA-ID> — <testcase title>

- **Source TC:** <Jira issue link / key>
- **Feature:** File-Level Backup (physical machine)  <!-- or File Share Backup -->
- **Generated:** <date>
- **Appliance:** nbr-84 (FLB) — see `test-data/environment.md`  <!-- nbr-5 for File Share Backup -->

## Objective
<one-line restatement of what this TC verifies, informed by the FLB spec>

## Fixtures used (from test-data)
- Source(s): <linux-src PM-2 /TestData_ForFLB | windows-src PM-3 C:\TestData_ForFLB>
- Repository: <Onboard id=2 | NFS_REPO id=7 | Wasabi id=6 | Ceph_S3 id=8>
- Job build: **recipe R4c** — build from the canonical repo template
  `test-data/job-templates/flb_job.template.json` (self-contained; no live-job/clone dependency)
- Job name: `AUTO_FLB_<JIRA-ID>`

## Preconditions
- [ ] Source machine present & OK — **R1** (`getDiscoveryItems` → PM-2/PM-3 state OK)
- [ ] Repository accessible — **R3**
- [ ] Test data seeded & manifest current — **R0 / test-data.md §1**
- [ ] **BLOCKED guard:** if a required fixture is absent (e.g. a specific repo type,
      transporter, or FS volume not present on nbr-84), STOP and report **BLOCKED (env)** with
      the exact missing prerequisite — do not fake a pass.

## Steps

### Step 1 — Build the job from the canonical template — R4c
- **Action:** load `test-data/job-templates/flb_job.template.json` → patch via the R4c builders
  (Source/Mapping/Repository/Identity + Options/Schedule as needed) → ValidationBuilder → `saveJob`
- **Payload:** `sourceVid` = PM-2/PM-3; `mappings[]` with `sourceIdentifierType` FOLDER|FILE
  (fwd slashes); `targetStorageVid` = the TC's repo; `name` = `AUTO_FLB_<JIRA-ID>`
- **Do NOT** clone or read job 25 (R4a is deprecated).
- **Expect:** `{result: OK, jobId: <n>}` — a new independent job
- **On fail:** capture response, mark FAIL, stop

### Step 2 — Run the job — R5
- **Action:** `mcp__nbr__call nbr-84 JobManagement run [{"runType":"ALL","jobIds":[<jobId>]}]`
- **Expect:** async accepted (returns null)

### Step 3 — Wait for completion — R6
- **Action:** poll `JobSummaryManagement.getJobShortInfo [[<jobId>]]`
- **Expect:** terminal `lrState: OK` (`lrVmOk ≥ 1`, `lrVmFailed 0`)

### Step 4 — Verify — R7 (+ R8 screenshot if UI-state)
- **Expect:** ≥1 savepoint; FLR mount/browse shows the selected scope; FLR-export files match
  `test-data/manifests/manifest-<host>.sha256` when the TC requires content verification.

## Evidence
<!-- R7.4 — see recipes/file-backup-recipes.md. Two DIFFERENT kinds of proof; don't conflate. -->
- **Listing-screenshot-pair** (images — MANDATORY for R4c-built Linux-source jobs, opportunistic
  for Windows R4c / R4e-built jobs): `results/screenshots/<JIRA-ID>__<stamp>/02_selected_items.png`
  (Edit → Source → Select Items, right after build) vs. `03_flr_browse.png` (Recover → File level
  recovery, after run completes) — proves the UI shows what we selected AND what we can recover,
  at the name/size/date level.
- **Checksum-table** (text, only when the TC requires content verification — never a screenshot,
  Director has no checksum UI):
  ```
  | File | Expected SHA256 | Actual SHA256 | Match |
  |---|---|---|---|
  | <name> | <hash> | <hash> | ✅/❌ |
  ```

## Cleanup
- On PASS — **R9** (`remove [<jobId>, false]` — deletes `AUTO_FLB_<JIRA-ID>` + backups)
- On FAIL/BLOCKED — leave artifacts; record job name/id

## Expected final verdict
<PASS criteria summarised in one line — tie to the Xray expected result + spec assertion>
