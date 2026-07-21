r"""NJM-182440 — [FLB v3] FLB - Recover to Source - Restores file and folder permissions.

Reuses the ACLTest_ForFLB fixture already seeded on win11 for NJM-70356/68956
(C:\ACLTest_ForFLB\secured has inheritance disabled + an explicit 'NT AUTHORITY\NETWORK
SERVICE:(OI)(CI)(R)' ACE on the folder and an explicit 'NT AUTHORITY\BATCH:(R)' ACE on
acl_probe.txt — both distinctive markers no default Windows ACL carries). Unlike NJM-70356 (whose
destination was a CIFS share and lost both ACEs — a documented, real product limitation of that
recovery type), THIS TC recovers to the SOURCE itself, which is exactly the path that should
preserve ACLs.

TWO-PHASE, SAFETY-GATED TEST — see this suite's `_helpers.py` for the authorization scope.
  1. `test_baseline_backup` — builds+runs a job over `ACLTest_ForFLB\secured` with
     acl_mode='Back up folder and file permissions' (per the TC's own step 1). No cleanup call.
  2. Agent (via WinRM): STRIPS the distinctive 'NT AUTHORITY\BATCH:(R)' ACE from
     `acl_probe.txt` on the source (icacls .../remove) — a real, verifiable permission change to
     restore FROM.
  3. `test_execute_acl_recovery` — recovers `acl_probe.txt` to its original location with
     'Overwrite the original item'. Real verdict (does icacls show the BATCH ACE restored on the
     source file afterward?) is read via WinRM by the agent and reported alongside this test's
     result — pytest itself has no host access to assert on ACLs directly.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import FileLevelRecoveryLocators as L

from ._helpers import build_flb_job, extract_item_names, flr_browse, recover_to_source, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-182440")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-182440_acl"
DRILL_TO_PARENT = ["Local Disk (C:)", "ACLTest_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "ACLTest_ForFLB", "secured"]


@allure.title("NJM-182440 phase 1/2 — baseline backup of ACLTest_ForFLB\\secured with folder+file ACLs")
@pytest.mark.flaky(reruns=0)
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(
        page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["secured"],
        acl_mode="Back up folder and file permissions",
    )
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert "acl_probe.txt" in names, f"expected acl_probe.txt in the backed-up folder, got {names}"


@allure.title("NJM-182440 phase 2/2 — recover to source restores the stripped file-level ACE")
@pytest.mark.flaky(reruns=0)
def test_execute_acl_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    started = recover_to_source(
        page, JOB_NAME, FLR_DRILL_TO_FOLDER, ["acl_probe.txt"], L.OVERWRITE_OVERWRITE,
    )
    assert started, "the FLR wizard did not confirm the recover-to-source recovery started"
    flb_job_cleanup(JOB_NAME)
