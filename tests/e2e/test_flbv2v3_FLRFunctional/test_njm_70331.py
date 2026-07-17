"""NJM-70331 — [FLB v1] FLR from FLB - Functional - Verify Cross-Platform Recovery (Linux
Source to Windows Share, etc.). Original status: never executed under the old RPC workflow (no
cases/*.md runbook exists).

Per the TC's own Xray steps, this is a TWO-part cross-platform matrix in one TC:
  part 1 — a LINUX source's recovery point recovered to a WINDOWS CIFS share;
  part 2 — a WINDOWS source's recovery point recovered to an NFS export.

FIXTURE NOTE: the TC text says "Linux NFS export" for part 2's target; this environment's one
documented FLR NFS export target is win-fs3's NFS export (10.10.15.3:/NFS_Share_Win — a Windows
host serving NFS, see test-data/environment.md). Per this project's fixture-over-abstract-text
rule, the export's host OS doesn't change what the TC exercises: the cross-platform axis under
test is the SOURCE platform vs the share PROTOCOL, both of which are faithfully covered
(Linux->CIFS, Windows->NFS).

Sources: Linux_16.84 (linux-src — FLR left tree top-level node is "root", see the Inventory
suite's calibration) and Window11 (windows-src). Selections use each source's known seeded
fixtures so the destination oracles are the existing manifests (manifest-linux-mixed.sha256 for
part 1's MixedTypes; manifest-windows.sha256's atest1.txt/Folder_test2 entries for part 2).

SCOPE NOTE (same convention as NJM-70307/70319/70327/70328): pytest asserts the wizard's
recovery-started confirmations and both jobs' Successful status; destination-content
verification (TC steps 3 and 5) is done separately by the agent driving WinRM against win-fs3.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [
    pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70331"),
    # Shares Linux_16.84/PM-2 with the Inventory suite's tagged pair — see
    # docs/xdist-parallelization.md (inert under default sequential execution).
    pytest.mark.xdist_group(name="Linux_16.84"),
]

LINUX_MACHINE = "Linux_16.84"
WINDOWS_MACHINE = "Window11"


@allure.title("NJM-70331 — Cross-platform recovery: Linux source → CIFS share, Windows source → NFS export")
def test_cross_platform_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    # --- part 1: Linux source -> Windows CIFS share (TC step 2) ---
    linux_job = flb_job_cleanup("AUTO_FLB_NJM-70331_lin")
    build_flb_job(page, linux_job, LINUX_MACHINE, ["TestData_ForFLB"], ["MixedTypes"], is_linux=True)
    status = run_and_wait_flb_job(page, linux_job)
    assert status == "Successful", f"Linux-source job did not succeed: {status}"
    started = recover_to_share(page, linux_job, ["root", "TestData_ForFLB"], ["MixedTypes"], "cifs")
    assert started, "part 1 (Linux -> CIFS): the FLR wizard did not confirm the recovery started"

    # --- part 2: Windows source -> NFS export (TC step 4) ---
    windows_job = flb_job_cleanup("AUTO_FLB_NJM-70331_win")
    build_flb_job(page, windows_job, WINDOWS_MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"])
    status = run_and_wait_flb_job(page, windows_job)
    assert status == "Successful", f"Windows-source job did not succeed: {status}"
    started = recover_to_share(
        page, windows_job, ["C:", "TestData_ForFLB"], ["atest1.txt", "Folder_test2"], "nfs"
    )
    assert started, "part 2 (Windows -> NFS): the FLR wizard did not confirm the recovery started"
