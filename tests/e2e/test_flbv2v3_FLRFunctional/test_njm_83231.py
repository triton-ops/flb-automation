r"""NJM-83231 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow (via FLR recovery to CIFS
share) on Windows Server 2016.

Build an FLB job on the OS's source over the seeded fileset, run it, open FLR, select everything
backed up, recover to a CIFS share.

CALIBRATION NOTE (2026-07-21): this row's C: enumeration in the Select Items picker was
previously BLOCKED on a timeout, isolated to this specific source. Re-tested live after an
environment fix — the enumeration is not actually broken, just slower than the picker's normal
settle time (root listing needs ~5s extra wait; a full C: drill takes ~20s) — no code change was
needed, it now completes and this TC passes.

SCOPE NOTE (same convention as the rest of this suite): pytest asserts job status + the wizard's
recovery-started confirmation; destination-content verification (this TC's final step) is done by
the agent driving WinRM against win-fs3, comparing the landed zip's 7 files against the manifest.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-83231")]

MACHINE = "Win_Server2016_15.19"
MANIFEST = "manifest-win2016-mixed.sha256"


@allure.title("NJM-83231 — OS-support E2E via FLR to CIFS on Windows Server 2016")
def test_os_support_flr_e2e(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-83231")

    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed on Windows Server 2016: {status}"

    started = recover_to_share(page, job_name, ["C:", "TestData_ForFLB"], ["MixedTypes"], "cifs")
    assert started, "the FLR wizard did not confirm the recovery started on Windows Server 2016"
