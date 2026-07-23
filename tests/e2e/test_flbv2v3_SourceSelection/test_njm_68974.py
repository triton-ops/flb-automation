r"""NJM-68974 — [FLB v2] FLB - Functional - Verify Backup/Recovery of Items with Maximum Filename
Length. The TC covers BOTH a Windows (255-char NTFS component) and a Linux (255-char) source, so
this file has one function per OS.

Per the TC's Xray steps: create files with the maximum-allowed 255-character filename on each OS,
back them up, confirm they're browsable/selectable in the FLR wizard, recover them, and verify the
recovered filenames retain the full 255-char length and content matches.

FIXTURES (seeded 2026-07-18, registered in test-data/test-data.md §7):
  * Windows: C:\MaxNameTest_ForFLB on Window11 (win11) — one file named 251×'N' + '.txt'
    (255-char component). Source SHA-256: 410faad583e1b8be63fe2f9306b80b004f15ec224990da9546750038cbb3ee7a.
  * Linux: /MaxNameTest_ForFLB/names/ on flb-linux — one file named 251×'L' + '.txt'.
    Source SHA-256: fda5b3cad9310b2e0436c219e8ff80118dbb40a7cf101a80af5d0427d1815048.

The whole containing folder is recovered (select it from its parent), so the 255-char filename
never has to be typed into a locator in code. The Windows fixture keeps the file at the folder
root (checking a folder includes its contents); the Linux fixture nests it under a 'names'
subfolder to match the proven drill-parent/check-child build pattern (NJM-70359).

SCOPE NOTE (same as the rest of this suite): pytest asserts job Successful + FLR recovery-started;
the "recovered filename retains full length + checksum matches" verdict is the agent-driven
destination check, reported alongside — not a pytest assertion.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-68974")]


@allure.title("NJM-68974 — backup/recovery of a 255-char filename (windows), recover to CIFS")
@pytest.mark.xdist_group(name="Window11")
def test_max_filename_length_backup_recovery_windows(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68974_windows")
    build_flb_job(page, job_name, "Window11", ["Local Disk (C:)"], ["MaxNameTest_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed (windows): {status}"
    started = recover_to_share(page, job_name, ["C:"], ["MaxNameTest_ForFLB"], "cifs")
    assert started, "the FLR wizard did not confirm the recovery started (windows)"


@allure.title("NJM-68974 — backup/recovery of a 255-char filename (linux), recover to NFS")
@pytest.mark.xdist_group(name="Linux_16.84")
def test_max_filename_length_backup_recovery_linux(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68974_linux")
    build_flb_job(page, job_name, "Linux_16.84", ["MaxNameTest_ForFLB"], ["names"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed (linux): {status}"
    started = recover_to_share(page, job_name, ["root", "MaxNameTest_ForFLB"], ["names"], "nfs")
    assert started, "the FLR wizard did not confirm the recovery started (linux)"
