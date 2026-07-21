r"""NJM-182423 — [FLB v3] FLB - Recovery - Recover selected files/folders to original location
(Recover to Source) [UC4].

The general happy-path use case underlying every other TC in this suite — build a job, run it,
select a backed-up item, recover it to original location, confirm it lands back correctly.
TWO-PHASE, SAFETY-GATED TEST — see this suite's `_helpers.py` for the authorization scope.
  1. `test_baseline_backup` — builds+runs a job over `uc4_general\note.txt` (seeded
     `UC4_BACKED_UP_182423`). No cleanup call.
  2. Agent (via WinRM): DELETES `note.txt` from the source (genuinely absent at recovery time).
  3. `test_execute_uc4_recovery` — recovers `note.txt` to its original location with 'Overwrite
     the original item'. Real verdict (note.txt reappears with `UC4_BACKED_UP_182423`) is read
     via WinRM by the agent and reported alongside this test's result.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import FileLevelRecoveryLocators as L

from ._helpers import build_flb_job, extract_item_names, flr_browse, recover_to_source, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-182423")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-182423_uc4"
DRILL_TO_PARENT = ["Local Disk (C:)", "RecoverToSource_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "RecoverToSource_ForFLB", "uc4_general"]


@allure.title("NJM-182423 phase 1/2 — baseline backup of uc4_general\\note.txt")
@pytest.mark.flaky(reruns=0)
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["uc4_general"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == {"note.txt"}, f"expected the seeded note.txt, got {names}"


@allure.title("NJM-182423 phase 2/2 — UC4: recover a selected file to its original location")
@pytest.mark.flaky(reruns=0)
def test_execute_uc4_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    started = recover_to_source(
        page, JOB_NAME, FLR_DRILL_TO_FOLDER, ["note.txt"], L.OVERWRITE_OVERWRITE,
    )
    assert started, "the FLR wizard did not confirm the recover-to-source recovery started"
    flb_job_cleanup(JOB_NAME)
