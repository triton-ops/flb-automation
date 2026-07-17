"""NJM-70328 — [FLB v1] FLR from FLB - Functional - Verify 'Recover to NFS Share' Recovery
Option. Original status: never executed under the old RPC workflow (no cases/*.md runbook
exists).

Per the TC's own Xray steps: confirm a valid FLB recovery point and that the target NFS export
is reachable; open Recover > Individual files; on the Files step, select files AND folders (the
same mixed selection as NJM-70327's CIFS sibling); on the Options step choose Recover to File
Share > NFS Share, enter the export path (no credentials — NFS auth is host-based), finish and
run; on the NFS export, verify the recovered items are present with matching content.

The export-reachability precondition (step 1) is covered implicitly by the wizard's own
'Test Connection' gate inside recover_to_share() — the Recover button never enables unless the
export connected, and the helper asserts on that.

NOTE: the NFS export (10.10.15.3:/NFS_Share_Win) doubles as NFS_REPO's backing store — the
destination-verification step must only ever touch the exact Recovered-items zip this run
creates, never anything else in that directory.

SCOPE NOTE (same convention as NJM-70307/70319/70327): pytest asserts only on what the browser
can observe — the wizard's own recovery-started confirmation and the FLB job's Successful
status. Destination-content verification (TC step 5) is done separately by the agent driving
WinRM against win-fs3 and reported alongside this test's result.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70328")]

MACHINE = "Window11"


@allure.title("NJM-70328 — 'Recover to NFS Share' recovery option (mixed file + folder selection)")
def test_recover_to_nfs_share(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70328")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    # TC step 3: the same known mixed selection as NJM-70327 (atest1.txt + Folder_test2), so the
    # identical 22-entry manifest oracle applies to the destination check.
    started = recover_to_share(
        page, job_name, ["C:", "TestData_ForFLB"], ["atest1.txt", "Folder_test2"], "nfs"
    )
    assert started, "the FLR wizard did not confirm the recovery started"
