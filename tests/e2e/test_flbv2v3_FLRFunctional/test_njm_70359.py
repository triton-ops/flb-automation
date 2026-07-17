"""NJM-70359 — [FLB v1] FLR from FLB - Functional - Verify User/Group Permissions are Preserved
on Recovery. Original status: never executed under the old RPC workflow (no cases/*.md runbook
exists).

Per the TC's own Xray steps: confirm a recovery point exists for a source folder with specific
user/group permissions ("owner, group, others rwx" — POSIX, so this TC uses the LINUX source);
open Recover > Individual files; select that folder; recover to a share (the TC allows CIFS or
NFS — NFS chosen, the natural pairing for POSIX-permission content); on the destination, verify
the folder retains its user/group permissions and content.

FIXTURE (seeded 2026-07-17, registered in test-data/test-data.md §6): /PermTest_ForFLB/permdir
on linux-src (flb-linux) — dir mode 750, perm_probe.txt 640, perm_probe2.sh 754, all owned
daemon:games (uid 1, gid 60) — deliberately non-default so preservation vs. reset-to-default is
unambiguous at the destination. Re-seed (idempotent):
    rm -rf /PermTest_ForFLB && mkdir -p /PermTest_ForFLB/permdir
    echo "POSIX permission probe for NJM-70359" > /PermTest_ForFLB/permdir/perm_probe.txt
    echo "second probe, different mode" > /PermTest_ForFLB/permdir/perm_probe2.sh
    chown -R daemon:games /PermTest_ForFLB/permdir
    chmod 750 /PermTest_ForFLB/permdir
    chmod 640 /PermTest_ForFLB/permdir/perm_probe.txt
    chmod 754 /PermTest_ForFLB/permdir/perm_probe2.sh

SCOPE NOTE (same convention as NJM-70307/70319/70327/70328/70356): pytest asserts the wizard's
recovery-started confirmation and the job's Successful status. The TC's verdict-carrying check —
whether the destination retains uid/gid/mode (step 5) — is done by the agent (inspecting the
landed archive's stored unix attributes on a Linux host) and reported alongside.

VERIFIED LIVE 2026-07-17 — TC step 5 FAILS as written on this build (product limitation, not an
automation bug — the exact POSIX sibling of NJM-70356's NTFS-ACL finding): the NFS recovery
landed as a Recovered-items-*.zip whose entries are marked create_system=UNIX but carry NO unix
mode in external_attr (the seeded 750/640/754 modes absent) and no uid/gid (daemon:games not
preserved) — while both files' CONTENT was byte-identical to the source (SHA256 matched
exactly). The zip container simply doesn't record ownership/mode on this build, so 'Recover to
NFS Share' structurally cannot preserve POSIX permissions; preservation, if supported, would be
a property of the safety-gated 'Recover to original location' type. Also observed: the same
path-flattened entry naming as NJM-70331's Linux recovery ('_PermTest_ForFLB_permdir_/').
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [
    pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70359"),
    # Shares Linux_16.84/PM-2 with other tagged tests — see docs/xdist-parallelization.md.
    pytest.mark.xdist_group(name="Linux_16.84"),
]

MACHINE = "Linux_16.84"


@allure.title("NJM-70359 — POSIX user/group permission preservation on FLR recovery to NFS export")
def test_permission_preservation_on_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70359")
    # PermTest_ForFLB is a root-level folder on the Linux source (like TestData_ForFLB).
    build_flb_job(page, job_name, MACHINE, ["PermTest_ForFLB"], ["permdir"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    # Linux FLR left tree's top-level node is "root" (Inventory-suite calibration 2026-07-16).
    started = recover_to_share(
        page, job_name, ["root", "PermTest_ForFLB"], ["permdir"], "nfs"
    )
    assert started, "the FLR wizard did not confirm the recovery started"
