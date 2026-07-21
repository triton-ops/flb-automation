r"""NJM-70022 — [FLB v1] FLB - Licensing - Verify Job Creation with All Supported License Editions.

BLOCKED — the TC's own steps require cycling nbr-84's live license through 17 different editions
(Default, Free, Beta, Promo, Trial, Basic, Pro Essentials, Enterprise Essentials, Pro,
Enterprise, Enterprise Plus, MSP Pro, MSP Enterprise, MSP Enterprise Plus, and the 3
API-RBAC-flavored variants), each requiring an appliance-wide license swap — an order of
magnitude beyond a single "explicit go-ahead" action; this would repeatedly disrupt every other
suite's ability to use the shared nbr-84 appliance across the whole matrix, and there is no
practical way to do it safely within a single test session. See NJM-70027/70024 for the same
underlying blast-radius concern applied to a single license change; this TC needs it applied 17
times over.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-70022")]


@pytest.mark.skip(
    reason="BLOCKED: requires cycling nbr-84's appliance-wide license through 17 editions — far "
    "beyond a single explicit-authorization action, and would repeatedly disrupt every other "
    "suite's use of the shared appliance. See module docstring."
)
def test_job_creation_all_license_editions():
    pass
