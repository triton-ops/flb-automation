"""NJM-70077 — FLB - Scheduling (New) - Verify Job Creation Uses New Scheduling UI on Fresh Install.

⚠ BLOCKED: needs a genuinely fresh NBR install — nbr-84 is a long-lived shared lab
appliance every other suite depends on; reinstalling it isn't something this project can
do without irreversibly resetting every other suite's fixtures and jobs.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-70077")]

SKIP_REASON = (
    "BLOCKED: needs a genuinely fresh NBR install — nbr-84 is a long-lived shared "
    "lab appliance every other suite depends on; reinstalling it isn't something "
    "this project can do without irreversibly resetting every other suite's "
    "fixtures and jobs. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_scheduling_new_verify_job_creation_uses_new():
    pass
