r"""NJM-68992 — [FLB v2] FLB - Functional - Verify Backup/Recovery Preserves Various File
Permissions. Has a Windows (NTFS ACL) part and a Linux (POSIX mode/owner, incl. setuid/setgid/
sticky + extended ACLs) part — one function each.

⚠ DOCUMENTED PRODUCT LIMITATION — same finding as NJM-68972 (see that file's module docstring for
the full writeup): zip-based share recovery preserves content but not NTFS ACLs / POSIX modes.
Written and executable; run explicitly (`-m sourceselection -k 68992`) to re-confirm.

FIXTURES (already seeded, reused from the FLRFunctional suite):
  * Windows: C:\ACLTest_ForFLB\secured on Window11 (win11).
  * Linux: /PermTest_ForFLB/permdir on flb-linux.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-68992")]

SKIP_REASON = (
    "Documented product limitation already live-verified by NJM-70356/70359 over these exact "
    "fixtures: zip-based share recovery preserves content but not NTFS ACLs / POSIX modes. Written "
    "and executable; run explicitly to re-confirm."
)


@allure.title("NJM-68992 — permission preservation (windows-ntfs-acl) — recover to CIFS")
@pytest.mark.xdist_group(name="Window11")
@pytest.mark.skip(reason=SKIP_REASON)
def test_permission_preservation_windows(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68992_windows-ntfs-acl")
    build_flb_job(page, job_name, "Window11", ["C:", "ACLTest_ForFLB"], ["secured"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed (windows-ntfs-acl): {status}"
    started = recover_to_share(page, job_name, ["C:", "ACLTest_ForFLB"], ["secured"], "cifs")
    assert started, "the FLR wizard did not confirm the recovery started (windows-ntfs-acl)"


@allure.title("NJM-68992 — permission preservation (linux-posix) — recover to NFS")
@pytest.mark.xdist_group(name="Linux_16.84")
@pytest.mark.skip(reason=SKIP_REASON)
def test_permission_preservation_linux(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68992_linux-posix")
    build_flb_job(page, job_name, "Linux_16.84", ["root", "PermTest_ForFLB"], ["permdir"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed (linux-posix): {status}"
    started = recover_to_share(page, job_name, ["root", "PermTest_ForFLB"], ["permdir"], "nfs")
    assert started, "the FLR wizard did not confirm the recovery started (linux-posix)"
