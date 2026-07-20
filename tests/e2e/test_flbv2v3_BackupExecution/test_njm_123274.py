r"""NJM-123274 — [FLB v1] FLB - Functional - Verify Backup from Various Supported File Systems
(NTFS, XFS, EXT4, etc.).

SCOPE (per the flb-test-plan-structure memory's own "fold rather than duplicate" note): the
literal TC wants a single-run-then-incremental-run-then-checksum-recover cycle repeated across
every filesystem type. Most of these already have solid, independently-verified single-run
FLR+checksum coverage elsewhere in this project — duplicating that here would add no new signal:
  - NTFS  — windows-src (win11) TestData_ForFLB, verified extensively across suites A/D/G.
  - EXT4  — ubuntu22-desktop-src/ubuntu24-desktop-src TestData_ForFLB, suite G's OS-support matrix.
  - XFS   — ubuntu22-xfs-vol's dedicated /mnt/xfs_testdata volume, test_flbv2v3_Inventory's own
            NJM-68934 (full run + checksum verify already done).
  - ReFS  — win2022-src's E: volume, test_flbv2v3_Inventory's own NJM-68916b (full run + FLR
            BROWSE only — no checksum, no incremental — the one real gap among these four).
  - Btrfs / EXT3 — no fixture anywhere in this lab (test-data/environment.md has no volume of
    either type on any discovered machine) — BLOCKED, no automation gap, nothing to build against.

This test fills the one genuine gap common to ALL of the above and not exercised by any prior
test: a FULL run, a real source content change, an INCREMENTAL run, and FLR-checksum verification
of the new state — demonstrated once on ReFS (the least-verified, most recently added filesystem)
as the representative case, rather than repeating the same combination-test machinery per
filesystem type for marginal additional signal.

TWO-PHASE COMBINATION TEST (same rationale as test_njm_185029.py/test_njm_128609.py — a live WinRM
change between two pytest invocations can only be driven by the session's own agent, not pytest
code):
  1. `pytest test_njm_123274.py::test_refs_full_backup` — builds+runs the job against a seeded
     E:\FSCoverage_ForFLB\keep.txt on Win_Server2022_81.58. No flb_job_cleanup call — job survives.
  2. Agent runs WinRM to add `added_after_full.txt` under the same folder.
  3. `pytest test_njm_123274.py::test_refs_incremental_after_source_change` — reruns the SAME job
     and asserts the new recovery point reflects the change (checksum-verified), then cleans up.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-123274")]

MACHINE = "Win_Server2022_81.58"
JOB_NAME = "AUTO_FLB_NJM-123274_refs-fs-coverage"
DRILL_TO_PARENT = ["New Volume - REFS (E:)"]
FLR_DRILL_TO_FOLDER = ["E:", "FSCoverage_ForFLB"]
BASELINE_FILES = {"keep.txt"}
AFTER_CHANGE_FILES = {"keep.txt", "added_after_full.txt"}
MANIFEST = "manifest-refs-fscoverage.sha256"


@allure.title("NJM-123274 phase 1/2 — full backup from a ReFS volume (Windows Server 2022)")
def test_refs_full_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["FSCoverage_ForFLB"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"full backup from ReFS did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == BASELINE_FILES, f"expected the seeded baseline file, got {names}"

    verify_checksum(page, JOB_NAME, FLR_DRILL_TO_FOLDER, "keep.txt", MANIFEST)


@allure.title("NJM-123274 phase 2/2 — incremental run after a real ReFS-side content change, "
               "FLR-checksum verified")
@pytest.mark.flaky(reruns=0)
def test_refs_incremental_after_source_change(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"incremental run did not succeed: {status}"

    # Recovery-point indexing lag (documented since NJM-70312): a run that just reached
    # 'Successful' can still show only its PREVIOUS recovery point in the FLR picker for 90+
    # seconds. Without this wait, flr_browse() below would silently browse the stale full-backup
    # recovery point instead of the new incremental one — exactly what happened on the first,
    # unfixed attempt at this test (got {'keep.txt'} instead of both files).
    FileLevelRecoveryPage(page).wait_for_recovery_point_count(JOB_NAME, min_count=2)

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == AFTER_CHANGE_FILES, (
        f"expected the new file added_after_full.txt to be reflected in the incremental "
        f"recovery point, got {names}"
    )

    verify_checksum(page, JOB_NAME, FLR_DRILL_TO_FOLDER, "keep.txt", MANIFEST)
    flb_job_cleanup(JOB_NAME)
