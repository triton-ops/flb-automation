"""NJM-70327 — [FLB v1] FLR from FLB - Functional - Verify 'Recover to CIFS Share' Recovery
Option. Original status: never executed under the old RPC workflow (no cases/*.md runbook
exists).

Per the TC's own Xray steps: confirm a valid FLB recovery point and that the target CIFS share
is reachable with valid credentials; open Recover > Individual files; on the Files step, select
files AND folders (a real mixed selection, unlike NJM-70307 which selected the whole root); on
the Options step choose Recover to File Share > CIFS Share, enter the share path + credentials,
finish and run; on the CIFS share, verify the recovered items are present with matching content.

The share-reachability precondition (step 1) is covered implicitly by the wizard's own
'Test Connection' gate inside recover_to_share() — the Recover button never enables unless the
share connected with the supplied credentials, and the helper asserts on that.

SCOPE NOTE (same convention as NJM-70307/70319): pytest asserts only on what the browser can
observe — the wizard's own recovery-started confirmation and the FLB job's Successful status.
Destination-content verification (recovered file + folder present on the CIFS share with
matching content, TC step 5) is done separately by the agent driving WinRM against win-fs3 and
reported alongside this test's result — pytest itself cannot call the remoting tools this
project uses for that.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70327")]

MACHINE = "Window11"


@allure.title("NJM-70327 — 'Recover to CIFS Share' recovery option (mixed file + folder selection)")
def test_recover_to_cifs_share(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70327")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    # TC step 3: a genuine mixed selection — one file and one folder together (the same seeded
    # pair NJM-70313/70325 use, so the expected destination content is well-known:
    # atest1.txt + the Folder_test2 subtree — see test-data/test-data.md §1).
    started = recover_to_share(
        page, job_name, ["C:", "TestData_ForFLB"], ["atest1.txt", "Folder_test2"], "cifs"
    )
    assert started, "the FLR wizard did not confirm the recovery started"
