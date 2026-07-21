r"""NJM-68623 — [FLB v1] FLB - Multi-Tenancy - Verify Job for Windows Machine from Master Tenant.

BLOCKED — Environment: nbr-84 is NOT deployed in Multi-Tenant mode. Confirmed live 2026-07-21 via
Settings > MSP: "There is no MSP" (the page whose whole purpose is connecting to/managing an MSP
relationship — the precursor to Multi-Tenant sub-tenants existing at all). Every one of this
suite's 6 Multi-Tenancy TCs (68623-68629) shares this exact precondition failure — see this
file's siblings. Setting up Multi-Tenant mode on this shared, single-tenant lab appliance would
be a major, appliance-wide reconfiguration well beyond the AUTO_FLB_* safety fence, needing
explicit user authorization before even being considered.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-68623")]


@pytest.mark.skip(
    reason="BLOCKED (Environment): nbr-84 is not deployed in Multi-Tenant mode ('There is no "
    "MSP', confirmed live via Settings > MSP) — this TC's precondition cannot be met without an "
    "appliance-wide reconfiguration requiring explicit user authorization. See module docstring."
)
def test_job_windows_machine_from_master_tenant():
    pass
