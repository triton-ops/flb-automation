r"""NJM-70024 — [FLB v1] FLB - Licensing - Verify Job Creation is Blocked for Unsupported/Expired
Licenses.

BLOCKED — same reasoning as NJM-70027: requires deliberately putting nbr-84 into a
Monitoring-only/expired license state, an APPLIANCE-WIDE change affecting every other suite's
ability to build/run jobs, needing explicit user go-ahead (Golden Rule 3) before attempting.

Note: nbr-84's license is ALREADY expired (Trial/Enterprise Plus, in its 10-day grace period —
confirmed live 2026-07-21), which is an interesting partial precondition match — but the TC
needs the license to actually BLOCK job creation, and a grace period is specifically designed to
NOT block anything yet (that's its purpose). Confirming what happens once the grace period lapses
would require either waiting ~10 real days or forcing the license into a harder-blocked state —
both squarely appliance-wide actions needing authorization, not something to trigger
speculatively on a shared lab appliance every other suite still depends on.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-70024")]


@pytest.mark.skip(
    reason="BLOCKED: requires forcing nbr-84's appliance-wide license into an "
    "unsupported/expired-blocking state — explicit user authorization needed (Golden Rule 3). "
    "See module docstring."
)
def test_job_creation_blocked_unsupported_license():
    pass
