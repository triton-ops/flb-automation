r"""NJM-68627 — [FLB v1] FLB - Multi-Tenancy - Verify Job for Linux Machine from a Sub-Tenant.

BLOCKED — same reason as NJM-68623 (see that file's module docstring): nbr-84 is not deployed in
Multi-Tenant mode ("There is no MSP", confirmed live 2026-07-21 via Settings > MSP) — there is no
sub-tenant to even log in as.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-68627")]


@pytest.mark.skip(
    reason="BLOCKED (Environment): nbr-84 is not deployed in Multi-Tenant mode ('There is no "
    "MSP', confirmed live via Settings > MSP) — no sub-tenant exists to log in as. See "
    "NJM-68623's module docstring for the shared reasoning across all 6 Multi-Tenancy TCs."
)
def test_job_linux_machine_from_sub_tenant():
    pass
