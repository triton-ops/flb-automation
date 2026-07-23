r"""NJM-83244 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow (via FLR recovery to CIFS
share) on RHEL 9.

Build an FLB job on the OS's source over the seeded fileset, run it, open FLR, select everything
backed up, recover to a CIFS share.

SCOPE NOTE (same convention as the rest of this suite): pytest asserts job status + the wizard's
recovery-started confirmation; destination-content verification (this TC's final step) is done by
the agent driving WinRM against win-fs3, comparing the landed zip's 7 files against the manifest.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-83244")]

MACHINE = "RHEL_9"
MANIFEST = "manifest-rhel9-mixed.sha256"


@allure.title("NJM-83244 — OS-support E2E via FLR to CIFS on RHEL 9")
def test_os_support_flr_e2e(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-83244")

    build_flb_job(page, job_name, MACHINE, ["TestData_ForFLB"], ["MixedTypes"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed on RHEL 9: {status}"

    # a Linux source's FLR left tree top-level node is "root" (Inventory calibration 2026-07-16)
    started = recover_to_share(page, job_name, ["root", "TestData_ForFLB"], ["MixedTypes"], "cifs")
    assert started, "the FLR wizard did not confirm the recovery started on RHEL 9"
