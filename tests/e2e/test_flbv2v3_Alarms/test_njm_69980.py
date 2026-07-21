r"""NJM-69980 — [FLB v1] FLB - Alarms - Verify Alarm "lic3" (Insufficient number of licenses).

BLOCKED — same appliance-wide license-state concern as NJM-69981 in this suite (lic6). The TC's
own precondition (step 1) needs fewer active licenses than protected jobs, with an expiry warning
approaching within its threshold — again a shared, appliance-wide license setting, not something
scoped to this suite's own AUTO_FLB_* entities. Needs explicit, scoped user authorization before
touching Settings -> Licensing, same posture as NJM-69981 and the repository-maintenance fence.
"""
from __future__ import annotations

import allure
import pytest

pytestmark = [pytest.mark.flb, pytest.mark.alarms, pytest.mark.jira("NJM-69980")]

_SKIP_REASON = (
    "Needs an insufficient-license-count condition provoked on the shared appliance — same "
    "appliance-wide license-state concern as NJM-69981. Needs explicit per-action authorization. "
    "See module docstring."
)


@pytest.mark.skip(reason=_SKIP_REASON)
@allure.title("NJM-69980 — an insufficient license count shows the lic3 alarm")
def test_insufficient_license_count_shows_lic3_alarm():
    pass
