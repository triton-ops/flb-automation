r"""NJM-69998 — [FLB v1] FLB - Alarms - Verify Alarm "error135" (Repository Out of Space).

BLOCKED — needs explicit user go-ahead, not an automation gap. The TC's own precondition (step 2)
is to fill the FLB job's TARGET REPOSITORY to 100% capacity (0 bytes free). Every repository in
this lab (test-data/environment.md) is shared, general-purpose infrastructure used by many other
suites' jobs — filling any of them to capacity would make every OTHER job targeting that same
repository fail with the identical out-of-space condition until cleaned up, a real, disruptive
blast radius well beyond this suite's own AUTO_FLB_* entities (same class of concern as the
repository-maintenance safety fence, see CLAUDE.md Golden Rule 3).

This becomes buildable if either: (a) a small, DEDICATED, disposable-capacity repository is
provisioned specifically for this TC (so filling it to 100% only affects our own test), or (b)
the user gives explicit, scoped go-ahead to temporarily fill an existing repository, with a clear
plan to free the space again afterward.
"""
from __future__ import annotations

import allure
import pytest

pytestmark = [pytest.mark.flb, pytest.mark.alarms, pytest.mark.jira("NJM-69998")]

_SKIP_REASON = (
    "Needs a repository filled to 100% capacity — every repo in this lab is shared "
    "infrastructure other suites' jobs depend on; needs a dedicated repo or explicit "
    "per-run authorization before filling any existing one. See module docstring."
)


@pytest.mark.skip(reason=_SKIP_REASON)
@allure.title("NJM-69998 — job run against a full repository shows the error135 alarm")
def test_repository_out_of_space_shows_error135_alarm():
    pass
