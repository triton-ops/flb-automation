"""NJM-83235 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow on Windows 10 Enterprise
(via FLR recovery to CIFS share).

Deliberately NOT part of test_njm_83226_83255_os_support_flr_matrix.py: the Window_10 source has
no seeded MixedTypes subtree or checksum manifest, and its host (win10 / 10.10.17.109) was
UNREACHABLE via WinRM at port time (2026-07-17, connection refused) so one couldn't be seeded or
hashed — its body genuinely differs from the matrix rows, failing docs/parametrize-pattern.md's
byte-identical bar.

Follows NJM-67701's live-verified precedent instead (the Inventory suite's Window_10 test, whose
documented scope is coverage-not-content-matching for exactly this reason): back up the whole
TestData_ForFLB tree that exists on Window_10, recover it all to the CIFS share.

SCOPE + ORACLE LIMITATION (stated honestly, per CLAUDE.md): pytest asserts job status + the
wizard's recovery-started confirmation. The destination check (by the agent, WinRM on win-fs3)
can verify the landed zip is present, non-empty, and structurally intact (a TestData_ForFLB tree
with >0 files) — but NOT byte-compare against the source, since no manifest exists and the
source host is unreachable for hashing. The TC's "content matches the source" step is therefore
only partially verifiable until the win10 host is reachable again (at which point seeding
MixedTypes + generating a manifest would promote this into the matrix).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-83235")]

MACHINE = "Window_10"


@allure.title("NJM-83235 — OS-support E2E via FLR to CIFS on Windows 10 Enterprise")
def test_win10_os_support_flr_e2e(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-83235")
    # Whole-tree scope, same as NJM-67701 (no MixedTypes exists on this source).
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    started = recover_to_share(page, job_name, ["C:"], ["TestData_ForFLB"], "cifs")
    assert started, "the FLR wizard did not confirm the recovery started"
