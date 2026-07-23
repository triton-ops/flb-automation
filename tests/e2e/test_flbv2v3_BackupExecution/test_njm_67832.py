"""NJM-67832 — FLB - Functional - Verify Job Execution via Scheduling.

⚠ BLOCKED: needs a job to actually fire from a REAL recurring schedule, not run-on-demand
— every other test in this project deliberately uses run-on-demand specifically to avoid
waiting for a real schedule to trigger (bounded, minutes-scale test execution). Waiting
for a genuine scheduled fire is a different, wall-clock-bound test architecture this
project doesn't support yet.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-67832")]

SKIP_REASON = (
    "BLOCKED: needs a job to actually fire from a REAL recurring schedule, not "
    "run-on-demand — every other test in this project deliberately uses "
    "run-on-demand specifically to avoid waiting for a real schedule to trigger "
    "(bounded, minutes-scale test execution). Waiting for a genuine scheduled "
    "fire is a different, wall-clock-bound test architecture this project doesn't "
    "support yet. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_functional_verify_job_execution_via_scheduling():
    pass
