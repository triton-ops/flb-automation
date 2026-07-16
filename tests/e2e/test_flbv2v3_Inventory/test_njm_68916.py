"""NJM-68916 — [FLB v1] FLB - Functional (Windows) - Verify Backup from FAT16/32, NTFS, and ReFS
File Systems. Original verdict (raw-RPC execution): PASS, with a documented scope deviation.

SCOPE NOTE (carried over from the original investigation): the TC describes a single Windows
machine with FAT16, FAT32, NTFS, and ReFS volumes all present. No single discovered machine has
all four; the closest coverage across the fleet is:
  - FAT16 — E: on win-fs3-src (PM-9, Win_Server2019_15.3)
  - FAT32 — A: on win2022-src (PM-11, Win_Server2022_81.58)
  - NTFS  — F: on win2022-src (PM-11)
  - ReFS  — E: on win2022-src (PM-11)
This builds TWO separate single-source jobs (one per machine) to cover all four filesystems —
an earlier attempt combining both machines into one job failed because it shared a source
physical machine with other concurrently-running jobs (the same-source serialization rule).
No test-file seeding was performed on these volumes — whatever content already exists there is
what gets backed up; the TC does not require content verification, only that each filesystem
type backs up successfully.

CALIBRATED live 2026-07-16: confirmed the wizard's Select Items dialog display labels for the
non-C: volumes (same "<label> (X:)" convention as "Local Disk (C:)") —
  - Win_Server2019_15.3: "FAT16 (E:)"
  - Win_Server2022_81.58: "FAT32 (A:)", "New Volume - REFS (E:)", "New Volume - SATA (F:)" (NTFS)
The FLR Files-step left tree, unlike the wizard picker, still uses the bare drive letter (e.g.
"E:") — same C:/"Local Disk (C:)" split already established elsewhere in this suite.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-68916")]

MACHINE_FAT16 = "Win_Server2019_15.3"
MACHINE_MULTI = "Win_Server2022_81.58"


@allure.title("NJM-68916a — Backup from FAT16 (E: on Windows Server 2019)")
def test_fat16_backup(logged_in_page, flb_job_cleanup):
    """No content verification per the TC's own scope (whatever pre-existing content is on the
    volume gets backed up) — the job succeeding is the pass condition; FLR browse is exercised
    as additional evidence that the recovery point actually mounts, not asserted against."""
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68916a")
    build_flb_job(page, job_name, MACHINE_FAT16, [], ["FAT16 (E:)"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"
    flr_browse(page, job_name, ["E:"])


@allure.title("NJM-68916b — Backup from FAT32 + NTFS + ReFS (A:/F:/E: on Windows Server 2022)")
def test_fat32_ntfs_refs_backup(logged_in_page, flb_job_cleanup):
    """Same no-content-verification scope as test_fat16_backup above."""
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68916b")
    build_flb_job(
        page, job_name, MACHINE_MULTI, [],
        ["FAT32 (A:)", "New Volume - SATA (F:)", "New Volume - REFS (E:)"],
    )
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"
    for volume in ("A:", "F:", "E:"):
        flr_browse(page, job_name, [volume])
