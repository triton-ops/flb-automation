r"""NJM-69981 — [FLB v1] FLB - Alarms - Verify Alarm "lic6" (Job Disabled Due to License Issue).

BLOCKED — needs explicit user go-ahead, not an automation gap. The TC's own precondition (step 1)
requires the environment to have NO valid license assigned (expired/revoked), disabling the job.
The license state is an APPLIANCE-WIDE setting shared by every job and every other suite in this
project — manipulating it to provoke this alarm would disable (or risk disabling) every job on
nbr-84 for the rest of the session, not just this suite's own AUTO_FLB_* entities. Real blast
radius well beyond what this project's safety fence allows without explicit, scoped authorization
each time (same posture as repository maintenance / the win2022-discovery machine-removal case).

nbr-84 is ALREADY showing "Your license has expired. The grace period is activated..." in its own
UI banner as of this session — a real, currently-true license-issue condition — but confirming
whether that alone already produces a lic6/lic3-style alarm on some job, versus needing further
license-state changes, has not been investigated; that investigation itself should wait for
explicit go-ahead given the appliance-wide nature of anything touching Settings -> Licensing.
"""
from __future__ import annotations

import allure
import pytest

pytestmark = [pytest.mark.flb, pytest.mark.alarms, pytest.mark.jira("NJM-69981")]

_SKIP_REASON = (
    "Needs the appliance's license state manipulated (no valid license / job disabled) — "
    "license is a shared, appliance-wide setting affecting every job, not just AUTO_FLB_*. "
    "Needs explicit per-action authorization. See module docstring."
)


@pytest.mark.skip(reason=_SKIP_REASON)
@allure.title("NJM-69981 — a job disabled by a license issue shows the lic6 alarm")
def test_job_disabled_by_license_issue_shows_lic6_alarm():
    pass
