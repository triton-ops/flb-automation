"""NJM-83372 — [FLB v1] FLR from FLB - Functional - Verify Recovery from an NFS Share Repository.

⚠ BLOCKED — environment drift, confirmed live 2026-07-23: `NFS_REPO` (test-data/environment.md's
own record: id 7, type NFS_SHARE at 10.10.15.3:/NFS_Share_Win, state OK) no longer exists as a
destination-repository option on nbr-84. Verified directly in the FLB wizard's own Destination-step
combo: searching the repo picker for "NFS" returns "No matching items found." (a search for
"Onboard" in the same combo, in the same session, DOES return a match — ruling out a search-box
bug and confirming this is a real repository-list difference, not a locator/timing issue). This is
the same class of drift already documented for `test_flbv2v3_ObjectStorage` (Wasabi_Repo removed
between when environment.md was written and when the suite was actually run) — `environment.md`
needs a fresh live re-survey of nbr-84's repository list, not just this one row's assumption
corrected.

Per the TC's own Xray steps (for when a real NFS Share repository exists again): confirm an FLB
job targeting an NFS Share repository has a valid recovery point; open Recover > Individual files;
on the Files step select items to recover; on the Options step choose Recover to NFS Share (or
CIFS Share), finish and run; on the destination share, verify recovered files match the source
content. The test body below is genuinely executable once a real NFS-Share-type repository is
re-added and its name substituted for `REPOSITORY` — not a stale placeholder.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-83372")]

MACHINE = "Window11"
REPOSITORY = "NFS_REPO"

SKIP_REASON = (
    "BLOCKED: no NFS-Share-type repository exists on nbr-84 (confirmed live 2026-07-23 — "
    "NFS_REPO, documented in test-data/environment.md, is no longer offered in the FLB wizard's "
    "Destination-step repo picker; a same-session search for 'Onboard' in the same combo DID "
    "match, ruling out a locator/search bug). Re-run once a real NFS Share repository is added "
    "back and this file's REPOSITORY constant is updated to match."
)


@pytest.mark.skip(reason=SKIP_REASON)
@allure.title("NJM-83372 — recovery from an NFS Share repository, recover to CIFS Share")
def test_recover_from_nfs_share_repository(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-83372")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"], repository=REPOSITORY)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed on {REPOSITORY}: {status}"

    started = recover_to_share(
        page, job_name, ["C:", "TestData_ForFLB"], ["atest1.txt", "Folder_test2"], "cifs"
    )
    assert started, "the FLR wizard did not confirm the recovery started"
