r"""NJM-85730 — [FLB v1] FLB - Repository - Verify Self-Healing Functionality for FLB Backups.

⚠ SAFETY-GATED, SKIPPED BY DEFAULT — do not unskip without the user's explicit go-ahead for THIS
run. This TC exercises a REPOSITORY-LEVEL maintenance action (self-healing scans/repairs every
backup in the repo, not just this suite's own AUTO_FLB_* data) against a shared, pre-existing
repository (Onboard repository) — CLAUDE.md's Golden Rule 3 explicitly covers this as requiring
the same per-action authorization as any other action with blast radius beyond your own created
entities, not just delete/edit. An earlier session in this project authorized a subagent to run
this without asking first, reasoning "maintenance isn't a delete" — the security classifier
correctly flagged that as a safety-fence violation. See the [[repository-maintenance-safety-fence]]
memory. Never authorize running this as part of a routine/automatic suite pass.

CONFIRMED LIVE 2026-07-18 (browser/checks/check_repository_reclaim_and_selfheal.py): 'Run
repository self-healing' is offered ONLY for LOCAL-type repos (present on Onboard/Local-Immutable;
absent — not disabled, absent — on S3/Azure-type repos). Confirms via a native Start/Cancel
dialog; the global Activities panel shows a real 0%->Completed progress entry (a small repo
finished in ~13s in that run).
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.repository_management_page import RepositoryManagementPage

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-85730")]

_SKIP_REASON = (
    "SAFETY-GATED: this test runs a repository-level maintenance action (self-healing) against "
    "SHARED, pre-existing infrastructure (Onboard repository), not an AUTO_FLB_* entity this suite "
    "owns. Per CLAUDE.md's Golden Rule 3, this requires the user's explicit go-ahead for this "
    "specific run, every time — never unskip as part of a routine automated pass. Written and "
    "executable; run manually only with that authorization."
)


@pytest.mark.skip(reason=_SKIP_REASON)
@allure.title("NJM-85730 — repository self-healing completes on a LOCAL-type repository")
def test_repository_self_healing(logged_in_page):
    page = logged_in_page
    rp = RepositoryManagementPage(page)
    rp.open()
    rp.open_repository("Onboard repository")

    assert rp.self_healing_available(), "'Run repository self-healing' should be offered for a LOCAL-type repo"
    rp.run_self_healing()

    rp.open_activities()
    text = rp.activities_text()
    assert "self-healing" in text.lower() and "onboard" in text.lower(), (
        f"expected an Activities entry for self-healing on Onboard repository, got: {text[:500]!r}"
    )

    waited, done = 0, False
    while waited < 120_000:
        page.reload()
        page.wait_for_timeout(1500)
        text = rp.activities_text()
        idx = text.lower().find("self-healing")
        snippet = text[max(0, idx - 10):idx + 120] if idx >= 0 else ""
        if "completed" in snippet.lower():
            done = True
            break
        page.wait_for_timeout(5000)
        waited += 6500
    assert done, f"repository self-healing did not reach 'Completed' within {waited}ms"
