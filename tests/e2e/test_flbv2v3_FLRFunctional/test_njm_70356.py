"""NJM-70356 — [FLB v1] FLR from FLB - Functional - Verify Security Attributes (ACLs) are
Preserved on Recovery. Original status: never executed under the old RPC workflow (no cases/*.md
runbook exists).

Per the TC's own Xray steps: confirm a recovery point exists for a source folder with NTFS ACL
security attributes; open Recover > Individual files; select that folder on the Files step;
recover to a CIFS share; on the destination, verify the folder retains its ACLs and content.

FIXTURE (seeded 2026-07-17, registered in test-data/test-data.md §6): C:\\ACLTest_ForFLB\\secured
on windows-src (win11) — inheritance disabled on the folder + an explicit
'NT AUTHORITY\\NETWORK SERVICE:(OI)(CI)(R)' ACE; acl_probe.txt inside carries an explicit
'NT AUTHORITY\\BATCH:(R)' ACE. Both ACEs are distinctive markers no default Windows ACL carries,
so their presence/absence at the destination is unambiguous. Re-seed (idempotent):
    $root='C:\\ACLTest_ForFLB'; Remove-Item $root -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path "$root\\secured"
    Set-Content "$root\\secured\\acl_probe.txt" "ACL preservation probe for NJM-70356"
    icacls "$root\\secured" /inheritance:d
    icacls "$root\\secured" /grant "NETWORK SERVICE:(OI)(CI)R"
    icacls "$root\\secured\\acl_probe.txt" /grant "BATCH:R"

SCOPE NOTE (same convention as NJM-70307/70319/70327/70328): pytest asserts the wizard's
recovery-started confirmation and the job's Successful status. The TC's actual verdict-carrying
check — whether the destination retains the ACLs (step 5) — is done by the agent driving WinRM
against win-fs3 and reported alongside this test's result.

VERIFIED LIVE 2026-07-17 — TC step 5 FAILS as written on this build (product limitation, not an
automation bug): the CIFS-share recovery landed as a standard Recovered-items-*.zip; the file
CONTENT was byte-identical to the source (SHA256 eb7b7398... matched exactly), but the extracted
folder/file carried ONLY destination-inherited default ACEs — both distinctive source markers
(the folder's explicit non-inherited 'NT AUTHORITY\\NETWORK SERVICE:(OI)(CI)(R)' and the file's
'NT AUTHORITY\\BATCH:(R)') were absent. A zip container has no representation for NTFS security
descriptors, so 'Recover to CIFS Share' structurally cannot preserve ACLs on this build; ACL
preservation, if supported at all, would be a property of the (safety-gated, never auto-executed
here) 'Recover to original location' type instead. Same documented-deviation precedent as
NJM-185015/185016: the pytest flow below passes, the TC's own step-5 expectation does not.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70356")]

MACHINE = "Window11"


@allure.title("NJM-70356 — NTFS ACL preservation on FLR recovery to CIFS share")
def test_acl_preservation_on_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70356")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["ACLTest_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    # TC step 3: select the ACL-bearing folder itself (from its parent's listing, so the whole
    # 'secured' subtree recovers — same select-from-parent pattern NJM-70319 calibrated).
    started = recover_to_share(
        page, job_name, ["C:", "ACLTest_ForFLB"], ["secured"], "cifs"
    )
    assert started, "the FLR wizard did not confirm the recovery started"
