r"""NJM-68972 — [FLB v1] FLB - Functional - Verify Permissions are Preserved on Backup and
Recovery. Has a Windows (NTFS ACL) part and a Linux (POSIX mode/owner) part — one function each.

⚠ DOCUMENTED PRODUCT LIMITATION — inherited directly from the already-live-verified sibling
findings NJM-70356 (NTFS ACL) and NJM-70359 (POSIX perms) in the FLRFunctional suite: recovery to
a CIFS/NFS share lands the data as a Recovered-items-*.zip, and a zip container has NO
representation for NTFS security descriptors or POSIX mode/owner/extended-ACL metadata. So the
recovered files' CONTENT is byte-identical to the source, but their ACLs/permissions are NOT
preserved (they take the destination's inherited defaults). This TC's preservation check therefore
FAILS as written on this build — exactly as NJM-70356/70359 documented, verified live 2026-07-17
with distinctive marker ACEs (NETWORK SERVICE / BATCH) and non-default POSIX modes (750/640/754,
daemon:games). Preservation, if supported at all, would be a property of the safety-gated
'Recover to original location' recovery type, never the share-recovery path this suite exercises.

Because the finding is already live-verified in the sibling suite over the SAME fixtures, this
test is written-but-not-run by default (the pytest body below is genuinely executable — it builds,
runs, and starts a share recovery — but re-running it would only re-confirm 70356/70359's finding
against identical inputs). Run explicitly (`-m sourceselection -k 68972`) if a fresh
re-verification is wanted.

FIXTURES (already seeded, reused from the FLRFunctional suite):
  * Windows: C:\ACLTest_ForFLB\secured on Window11 (win11) — inheritance disabled + explicit
    NETWORK SERVICE (folder) / BATCH (file) ACEs (test-data/test-data.md §6, NJM-70356).
  * Linux: /PermTest_ForFLB/permdir on flb-linux — dir 750, files 640/754, daemon:games
    (test-data/test-data.md §6, NJM-70359).

SCOPE NOTE: pytest asserts job Successful + FLR recovery-started; the ACL/POSIX-preservation
verdict (the TC's actual point) is the agent-driven destination check, reported alongside, and is
the documented FAIL above — not a pytest assertion.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-68972")]

SKIP_REASON = (
    "Documented product limitation already live-verified by NJM-70356/70359 over these exact "
    "fixtures: zip-based share recovery preserves content but not NTFS ACLs / POSIX modes. Written "
    "and executable; run explicitly to re-confirm."
)


@allure.title("NJM-68972 — permission preservation (windows-ntfs-acl) — recover to CIFS")
@pytest.mark.xdist_group(name="Window11")
@pytest.mark.skip(reason=SKIP_REASON)
def test_permission_preservation_windows(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68972_windows-ntfs-acl")
    # NOTE: build_flb_job()'s drill_path here is reused verbatim from the original combined
    # file's own computation (drill_parent[:-1] + [drill_parent[-1]], i.e. drill_parent
    # unchanged) — preserved exactly as this never-yet-run, skip-marked test already had it
    # rather than "fixing" untested logic as a side effect of splitting files.
    build_flb_job(page, job_name, "Window11", ["C:", "ACLTest_ForFLB"], ["secured"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed (windows-ntfs-acl): {status}"
    started = recover_to_share(page, job_name, ["C:", "ACLTest_ForFLB"], ["secured"], "cifs")
    assert started, "the FLR wizard did not confirm the recovery started (windows-ntfs-acl)"


@allure.title("NJM-68972 — permission preservation (linux-posix) — recover to NFS")
@pytest.mark.xdist_group(name="Linux_16.84")
@pytest.mark.skip(reason=SKIP_REASON)
def test_permission_preservation_linux(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68972_linux-posix")
    build_flb_job(page, job_name, "Linux_16.84", ["root", "PermTest_ForFLB"], ["permdir"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed (linux-posix): {status}"
    started = recover_to_share(page, job_name, ["root", "PermTest_ForFLB"], ["permdir"], "nfs")
    assert started, "the FLR wizard did not confirm the recovery started (linux-posix)"
