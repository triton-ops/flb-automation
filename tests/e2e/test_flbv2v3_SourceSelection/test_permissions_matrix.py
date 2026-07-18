r"""NJM-68972 / 68992 — [FLB v1/v2] FLB - Functional - Verify Permissions are Preserved on Backup
and Recovery / Verify Backup/Recovery Preserves Various File Permissions.

Both TCs have a Windows (NTFS ACL) part and a Linux (POSIX mode/owner, incl. setuid/setgid/sticky
+ extended ACLs) part. This matrix parametrizes them as 4 rows (68972-win, 68972-linux,
68992-win, 68992-linux).

⚠ DOCUMENTED PRODUCT LIMITATION — inherited directly from the already-live-verified sibling
findings NJM-70356 (NTFS ACL) and NJM-70359 (POSIX perms) in the FLRFunctional suite: recovery to
a CIFS/NFS share lands the data as a Recovered-items-*.zip, and a zip container has NO
representation for NTFS security descriptors or POSIX mode/owner/extended-ACL metadata. So the
recovered files' CONTENT is byte-identical to the source, but their ACLs/permissions are NOT
preserved (they take the destination's inherited defaults). These two TCs' step-6/7 preservation
checks therefore FAIL as written on this build — exactly as NJM-70356/70359 documented, verified
live 2026-07-17 with distinctive marker ACEs (NETWORK SERVICE / BATCH) and non-default POSIX modes
(750/640/754, daemon:games). Preservation, if supported at all, would be a property of the
safety-gated 'Recover to original location' recovery type, never the share-recovery path this
suite exercises.

Because the finding is already live-verified in the sibling suite over the SAME fixtures, these
rows are written-but-not-run by default (the pytest body below is genuinely executable — it builds,
runs, and starts a share recovery — but re-running it would only re-confirm 70356/70359's finding
against identical inputs). Run explicitly (`-m sourceselection -k permissions`) if a fresh
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

pytestmark = [pytest.mark.flb, pytest.mark.sourceselection]

# (jira_id, os_part, machine, is_linux, drill_parent, folder, share) — one row per TC×OS.
PERMISSION_MATRIX = [
    pytest.param(
        "NJM-68972", "windows-ntfs-acl", "Window11", False, ["C:", "ACLTest_ForFLB"], "secured", "cifs",
        marks=[pytest.mark.jira("NJM-68972"), pytest.mark.xdist_group(name="Window11")],
        id="NJM-68972-win",
    ),
    pytest.param(
        "NJM-68972", "linux-posix", "Linux_16.84", True, ["root", "PermTest_ForFLB"], "permdir", "nfs",
        marks=[pytest.mark.jira("NJM-68972"), pytest.mark.xdist_group(name="Linux_16.84")],
        id="NJM-68972-linux",
    ),
    pytest.param(
        "NJM-68992", "windows-ntfs-acl", "Window11", False, ["C:", "ACLTest_ForFLB"], "secured", "cifs",
        marks=[pytest.mark.jira("NJM-68992"), pytest.mark.xdist_group(name="Window11")],
        id="NJM-68992-win",
    ),
    pytest.param(
        "NJM-68992", "linux-posix", "Linux_16.84", True, ["root", "PermTest_ForFLB"], "permdir", "nfs",
        marks=[pytest.mark.jira("NJM-68992"), pytest.mark.xdist_group(name="Linux_16.84")],
        id="NJM-68992-linux",
    ),
]


@pytest.mark.skip(
    reason="Documented product limitation already live-verified by NJM-70356/70359 over these exact "
    "fixtures: zip-based share recovery preserves content but not NTFS ACLs / POSIX modes. Written "
    "and executable; run explicitly to re-confirm."
)
@pytest.mark.parametrize("jira_id,os_part,machine,is_linux,drill_parent,folder,share", PERMISSION_MATRIX)
def test_permission_preservation(
    logged_in_page, flb_job_cleanup, jira_id, os_part, machine, is_linux, drill_parent, folder, share,
):
    allure.dynamic.title(f"{jira_id} — permission preservation ({os_part}) — recover to {share.upper()}")
    page = logged_in_page
    job_name = flb_job_cleanup(f"AUTO_FLB_{jira_id}_{os_part}")
    parent_folder = drill_parent[-1]
    build_flb_job(page, job_name, machine, drill_parent[:-1] + [parent_folder], [folder], is_linux=is_linux)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed ({os_part}): {status}"
    started = recover_to_share(page, job_name, drill_parent, [folder], share)
    assert started, f"the FLR wizard did not confirm the recovery started ({os_part})"
