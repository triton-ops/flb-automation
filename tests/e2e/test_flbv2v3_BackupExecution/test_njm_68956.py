r"""NJM-68956 — [FLB v1] FLB - Functional - Verify Backup Preserves File and Folder Permissions
(ACLs).

Standalone script in suite D (per explicit instruction — each suite's TCs are executed
separately, so this is its own file here rather than a pointer at suite A/FLRFunctional's
overlapping ACL coverage).

Reuses the ACLTest_ForFLB fixture already seeded on win11 for NJM-70356
(test_flbv2v3_FLRFunctional/test_njm_70356.py's own docstring has the idempotent re-seed
PowerShell): C:\ACLTest_ForFLB\secured has inheritance disabled + an explicit
'NT AUTHORITY\NETWORK SERVICE:(OI)(CI)(R)' ACE on the folder and an explicit
'NT AUTHORITY\BATCH:(R)' ACE on acl_probe.txt inside it — both distinctive markers no default
Windows ACL carries.

⚠ KNOWN, ALREADY-DOCUMENTED PRODUCT LIMITATION (NJM-70356, verified live 2026-07-17): recovering
to a CIFS share packages the result as a plain zip, which has no representation for NTFS security
descriptors — both distinctive source ACEs were confirmed ABSENT at the destination even though
file CONTENT was byte-identical. ACL preservation, if supported at all, would be a property of
'Recover to original location' instead, which stays safety-gated in this project (never
auto-executed — must ask the user first per CLAUDE.md). Reuses recover_to_share() from
test_flbv2v3_FLRFunctional/_helpers.py directly (pragmatic single-caller reuse — it is 100%
suite-agnostic FLR-to-share plumbing, not worth duplicating ~50 lines for one new caller).

SCOPE: this pytest test asserts the mechanical parts (job succeeds, recovery wizard confirms it
started) — the actual ACL comparison (the TC's own real verdict) is performed by the agent
driving the session via WinRM against the destination share, reported alongside this test's
result, same convention as NJM-70356/70319/70327/70328.
"""
from __future__ import annotations

import allure
import pytest

from tests.e2e.test_flbv2v3_FLRFunctional._helpers import recover_to_share

from ._helpers import build_flb_job, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-68956")]

MACHINE = "Window11"


@allure.title("NJM-68956 — backup + recovery of an ACL-bearing folder to a CIFS share")
def test_acl_preservation(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68956_acl-preservation")

    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["ACLTest_ForFLB"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    started = recover_to_share(page, job_name, ["C:", "ACLTest_ForFLB"], ["secured"], "cifs")
    assert started, "the FLR wizard did not confirm the recovery started"
