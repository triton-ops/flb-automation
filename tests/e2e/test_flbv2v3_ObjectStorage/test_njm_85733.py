r"""NJM-85733 — [FLB v1] FLB - Repository - Verify Space Reclaim Functions Correctly with FLB
Backups.

⚠ SAFETY-GATED, SKIPPED BY DEFAULT — do not unskip without the user's explicit go-ahead for THIS
run. This TC exercises a REPOSITORY-LEVEL maintenance action (reclaim acts on the whole repository,
not just this suite's own AUTO_FLB_* data) against a shared, pre-existing repository (Onboard
repository) — CLAUDE.md's Golden Rule 3 explicitly covers this as requiring the same per-action
authorization as any other action with blast radius beyond your own created entities, not just
delete/edit. An earlier session in this project authorized a subagent to run this without asking
first, reasoning "maintenance isn't a delete" — the security classifier correctly flagged that as
a safety-fence violation. See the [[repository-maintenance-safety-fence]] memory. Never authorize
running this as part of a routine/automatic suite pass.

CONFIRMED LIVE 2026-07-18 (browser/checks/check_repository_reclaim_and_selfheal.py): the menu item
genuinely exists in the DOM but renders hidden+disabled with the tooltip 'No space can be
reclaimed' whenever nothing is reclaimable — the observed state on every repo checked, even after
building+running+deleting a small dedicated job to try to manufacture reclaimable space. HONEST
OPEN FINDING: what actually makes this become enabled is unconfirmed (candidates: dedup-repo
partial deletions, fragmented blocks from a failed self-heal/repair — not exercised). This test
therefore only verifies the documented baseline (offered/disabled state + reason), not a full
reclaim-and-verify cycle.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import RepositoryManagementLocators as RL
from browser.pom.common.repository_management_page import RepositoryManagementPage

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-85733")]

_SKIP_REASON = (
    "SAFETY-GATED: this test runs a repository-level maintenance action (reclaim) against SHARED, "
    "pre-existing infrastructure (Onboard repository), not an AUTO_FLB_* entity this suite owns. "
    "Per CLAUDE.md's Golden Rule 3, this requires the user's explicit go-ahead for this specific "
    "run, every time — never unskip as part of a routine automated pass. Written and executable; "
    "run manually only with that authorization."
)


@pytest.mark.skip(reason=_SKIP_REASON)
@allure.title("NJM-85733 — 'Reclaim unused space' baseline state (offered-but-disabled when nothing reclaimable)")
def test_repository_space_reclaim_baseline(logged_in_page):
    page = logged_in_page
    rp = RepositoryManagementPage(page)
    rp.open()
    rp.open_repository("Onboard repository")

    available = rp.reclaim_available()
    reason = rp.menu_item_disabled_reason(RL.RECLAIM_UNUSED_SPACE)
    # Documented baseline (see module docstring): expected disabled with 'No space can be
    # reclaimed' when nothing is reclaimable. If a future run finds it enabled, that's a real,
    # useful signal (something IS reclaimable) — report it, don't force this assertion to fail.
    assert not available, (
        f"'Reclaim unused space' was unexpectedly enabled — investigate what became reclaimable "
        f"(reason={reason!r})"
    )
