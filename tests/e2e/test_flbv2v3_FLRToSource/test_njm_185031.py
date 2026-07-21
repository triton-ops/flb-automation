r"""NJM-185031 — [FLB v3] FLR from FLB - Functional - Recover from a pre-upgrade recovery point
after version update.

BLOCKED — not an automation gap. The TC's own precondition (step 1) requires taking a recovery
point on the CURRENT product version, then literally upgrading the shared nbr-84 appliance to a
newer version, then recovering from the pre-upgrade recovery point. Upgrading the appliance
mid-session is an irreversible, appliance-wide action affecting every other suite's tests for the
rest of the session (same category of constraint as suite D's NJM-70079/70077, which need a
version change/reinstall to exercise their own preconditions) — not something to do to satisfy a
single TC's setup step.

If a dedicated, disposable appliance (or a scheduled maintenance window on nbr-84 with explicit
user go-ahead) becomes available for a real version-upgrade test pass, this TC becomes buildable:
take a recovery point, upgrade, then run File Level Recovery against the pre-upgrade recovery
point and confirm the browse tree loads correctly and recovered content matches.
"""
from __future__ import annotations

import allure
import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-185031")]

_SKIP_REASON = (
    "Needs a real product version upgrade of the shared nbr-84 appliance mid-test — irreversible, "
    "appliance-wide, affects every other suite for the rest of the session. See module docstring."
)


@pytest.mark.skip(reason=_SKIP_REASON)
@allure.title("NJM-185031 — FLR from a pre-upgrade recovery point survives a version update")
def test_recover_from_pre_upgrade_recovery_point_after_version_update():
    pass
