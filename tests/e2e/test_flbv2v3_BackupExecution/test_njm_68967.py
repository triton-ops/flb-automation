r"""NJM-68967 — [FLB v1] FLB - Functional - Verify Backup of Locked/In-Use Files (VSS).

Per the Jira TC's own step 3 ("Accept defaults (VSS will handle locked files)"), this deliberately
does NOT enable App-aware mode — VSS-based locked-file handling is the FLB default on a Windows
physical source regardless of that setting (App-aware mode is for *application-consistent*
quiescing of VSS-aware apps like SQL Server, a separate concern from "can it back up a file another
process has open").

Requires a real OS-level file lock held DURING the job run — something only the driving agent can
set up via WinRM (pytest code has no live host access). Procedure:
  1. Agent seeds C:\TestData_ForFLB\LockedFileTest_ForFLB\{locked_file.txt,keep.txt} on win11 and
     computes their real SHA-256 via Get-FileHash -> test-data/manifests/manifest-lockedfile-forflb.sha256.
  2. Agent starts a DETACHED background PowerShell process (Start-Process, survives past the WinRM
     session) that opens locked_file.txt with FileShare.None for 900s — an genuine exclusive OS lock,
     confirmed live 2026-07-20 by a second WinRM call failing to open the same file exclusively
     (MethodInvocationException / sharing violation) while the process was running. The lock-holder
     script itself lives OUTSIDE LockedFileTest_ForFLB (one level up, in TestData_ForFLB) — putting
     it inside the backed-up folder itself was a real authoring bug caught live 2026-07-20: the
     job's own item scope swept the helper script up as an extra recovered file, failing the
     filename-set assertion for a reason that had nothing to do with the product.
  3. This test runs while the lock is held: builds+runs the job, then verifies via FLR both that
     the locked file is present with correct content (checksum match) alongside the untouched
     control file — proving VSS captured a consistent snapshot despite the open handle, not that
     the job merely skipped/errored on the locked file.
  4. Agent kills the lock-holding process afterward (WinRM Stop-Process) — it also self-expires
     after 900s if not killed, so no lock survives past this session either way.

⚠ If this test is run standalone or in a different session, locked_file.txt must actually be
locked by a live process on win11 at Job Run time for the TC to be exercised meaningfully — running
this test against an unlocked file only proves normal FLB backup works, not the VSS/locked-file
path.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-68967")]

MACHINE = "Window11"
DRILL_TO_PARENT = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "TestData_ForFLB", "LockedFileTest_ForFLB"]
EXPECTED_FILES = {"locked_file.txt", "keep.txt"}
MANIFEST = "manifest-lockedfile-forflb.sha256"


@allure.title("NJM-68967 — FLB backup of a folder containing a locked/in-use file (VSS)")
def test_backup_of_locked_file(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68967_locked-file")

    build_flb_job(page, job_name, MACHINE, DRILL_TO_PARENT, ["LockedFileTest_ForFLB"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", (
        f"job with a locked source file did not succeed (VSS should have handled it): {status}"
    )

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_FOLDER)))
    assert names == EXPECTED_FILES, (
        f"expected both the locked file and the untouched control file to be backed up, got {names}"
    )

    # Real content-integrity check, not just presence: proves the VSS snapshot captured the
    # locked file's actual bytes correctly, not a truncated/corrupted read around the open handle.
    verify_checksum(page, job_name, FLR_DRILL_TO_FOLDER, "locked_file.txt", MANIFEST)
    verify_checksum(page, job_name, FLR_DRILL_TO_FOLDER, "keep.txt", MANIFEST)
