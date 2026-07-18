r"""NJM-68973 — [FLB v2] FLB - Functional - Verify Backup/Recovery of Items with Maximum Path Length.

Per the TC's Xray steps: create a folder hierarchy whose full path is at/near the legacy NTFS
MAX_PATH (260 chars), place a file at the deepest level, back it up, confirm it's browsable in the
FLR wizard, recover it, and verify the recovered file exists at its full path with matching content.

FIXTURE (seeded 2026-07-18, registered in test-data/test-data.md §7): C:\MaxPathTest_ForFLB on
Window11 (win11) — 5 nested 44-char folders giving a deepest directory of 246 chars and a file
path 'deepfile.txt' at 259 chars (just under the 260 legacy limit). Source SHA-256 of deepfile.txt:
951c8c8d677aa01a72faeac117cff19948ea9c62382aaaebe7271c0eafedb165. Re-seed via the WinRM script in
test-data/test-data.md §7.

The whole folder is recovered (select the top MaxPathTest_ForFLB folder from C:\), so the deep
subtree comes back intact without having to name the 259-char path in code.

SCOPE NOTE (same as the rest of this suite): pytest asserts job Successful + FLR recovery-started;
the "recovered file exists at full path, checksum matches" verdict is the agent-driven destination
check on win-fs3, reported alongside — not a pytest assertion.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-68973"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@allure.title("NJM-68973 — backup/recovery of a maximum-path-length (259-char) file, recover to CIFS")
def test_max_path_length_backup_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68973")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["MaxPathTest_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"
    started = recover_to_share(page, job_name, ["C:"], ["MaxPathTest_ForFLB"], "cifs")
    assert started, "the FLR wizard did not confirm the recovery started"
