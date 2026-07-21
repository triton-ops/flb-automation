r"""NJM-182438 — [FLB v3] FLB - Recover to Source - Fails with a clear error when source machine
is not in Inventory.

BLOCKED — not an automation gap. The TC's own precondition (step 1) requires the ORIGINAL source
machine to be genuinely absent from Inventory or unreachable at recovery time. Every physical
machine this project uses as an FLB source (Window11, flb-linux, win-fs3, win2022, etc.) is a
shared, real, discovered piece of lab infrastructure that every other suite in this project also
depends on — deliberately removing one from Inventory (or making it unreachable) to satisfy this
TC's precondition would violate the safety fence's 'never touch discovered machines' rule and
would break every other suite's tests that share that same source for the rest of the session.

There is no reversible way to simulate "source not in Inventory" without either (a) actually
removing/disabling the discovery entry (an appliance-wide, shared-infrastructure change, same
class of action as the repository-maintenance safety fence) or (b) a spare, dedicated,
never-otherwise-used physical machine set up specifically to be discovered-then-removed — no such
machine exists in this lab. If one is provisioned in the future, this TC becomes buildable: build
a job on it, take one recovery point, remove it from Inventory, then attempt Recover to Source and
confirm a clear pre-flight error (no partial write) rather than a crash/silent failure.
"""
from __future__ import annotations

import allure
import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-182438")]

_SKIP_REASON = (
    "Needs the source machine to be genuinely absent from Inventory/unreachable — every FLB "
    "source in this lab is shared infrastructure other suites depend on; no dedicated, "
    "disposable machine exists to safely remove from Inventory. See module docstring."
)


@pytest.mark.skip(reason=_SKIP_REASON)
@allure.title("NJM-182438 — Recover to Source fails cleanly when source machine is not in Inventory")
def test_recover_to_source_fails_when_source_not_in_inventory():
    pass
