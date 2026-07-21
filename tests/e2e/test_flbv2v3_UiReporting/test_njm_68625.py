r"""NJM-68625 — [FLB v1] FLB - Multi-Tenancy - Verify Job with Mixed OS Machines from Master
Tenant.

BLOCKED — same reason as NJM-68623 (see that file's module docstring): nbr-84 is not deployed in
Multi-Tenant mode ("There is no MSP", confirmed live 2026-07-21 via Settings > MSP).
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-68625")]


@pytest.mark.skip(
    reason="BLOCKED (Environment): nbr-84 is not deployed in Multi-Tenant mode ('There is no "
    "MSP', confirmed live via Settings > MSP) — see NJM-68623's module docstring for the shared "
    "reasoning across all 6 Multi-Tenancy TCs in this suite."
)
def test_job_mixed_os_from_master_tenant():
    pass
