r"""NJM-70027 — [FLB v1] FLB - Licensing - Verify Job Behavior After License Change (Supported to
Unsupported and vice versa).

BLOCKED — needs explicit user authorization, not buildable within the AUTO_FLB_* safety fence.
Changing the appliance's license edition (Administration > Licenses > "Change License") is an
APPLIANCE-WIDE action affecting every job on nbr-84, not just this session's own AUTO_FLB_*
entities — squarely the kind of blast-radius-beyond-own-entities action CLAUDE.md's Golden Rule
3 requires explicit go-ahead for, same as repository-level maintenance.

Extra risk factor confirmed live 2026-07-21: nbr-84's current license is already fragile — a
Trial/Enterprise Plus license, EXPIRED, with only a 10-day grace period remaining ("Your license
has expired. The grace period is activated and will end in 9 days 23 hours" banner, visible on
every page). Any license-edition change attempted on this appliance risks disrupting or ending
that grace period for every OTHER suite's test run that still depends on this shared lab
appliance being usable — not something to attempt speculatively.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-70027")]


@pytest.mark.skip(
    reason="BLOCKED: requires changing nbr-84's appliance-wide license edition — explicit user "
    "authorization needed (Golden Rule 3, blast radius beyond own AUTO_FLB_* entities), and the "
    "appliance's license is already in a fragile expired/grace-period state shared by every "
    "other suite. See module docstring."
)
def test_job_behavior_after_license_change():
    pass
