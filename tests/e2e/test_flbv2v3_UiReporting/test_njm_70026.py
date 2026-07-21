r"""NJM-70026 — [FLB v1] FLB - Licensing - Verify Job Creation is Blocked When Exceeding Workload
Limit.

BLOCKED — Environment: nbr-84's current license (Trial, Enterprise Plus edition) has NO workload
cap to exceed. Confirmed live 2026-07-21 via Settings > Licensing: "Per-workload subscription
licensing: Workloads — 10 out of UNLIMITED used." Every other perpetual-licensing metric
(Physical servers, Physical workstations, etc.) is likewise "X out of unlimited used." There is
no finite limit this TC's precondition ("select physical machines whose total count exceeds the
remaining licensed workload slots") can actually exceed on this appliance/license — the condition
this TC needs to exercise simply cannot occur under the current license, and forcing a
capped/different license edition onto the shared appliance to manufacture one is the same
appliance-wide, authorization-required action as NJM-70027/70024/70022.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-70026")]


@pytest.mark.skip(
    reason="BLOCKED (Environment): nbr-84's current Trial/Enterprise Plus license has unlimited "
    "workloads (confirmed live: 'Workloads — 10 out of unlimited used') — there is no finite "
    "limit to exceed without forcing an appliance-wide license change, which needs explicit "
    "user authorization. See module docstring."
)
def test_job_creation_blocked_exceeding_workload_limit():
    pass
