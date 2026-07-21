r"""NJM-182437 — [FLB v3] FLB - Recover to Source - Recover separate files and folders.

TWO-PHASE, SAFETY-GATED TEST — see this suite's `_helpers.py` for the authorization scope.
  1. `test_baseline_backup` — builds+runs a job over the whole `scattered\` tree: `top.txt`
     (`SCATTERED_TOP_182437`), `folderA\deepA.txt` (`SCATTERED_A_182437`), `folderB\deepB.txt`
     (`SCATTERED_B_182437`, deliberately the CONTROL item — never selected for recovery). No
     cleanup call.
  2. Agent (via WinRM): DELETES `top.txt` and the whole `folderA` from the source, then modifies
     `folderB\deepB.txt` to `SCATTERED_B_MODIFIED_182437` (a distinct sentinel — proves isolation:
     if the recovery incorrectly touched an unselected item, this sentinel would be reverted back
     to the original backed-up content instead of staying as the sentinel).
  3. `test_execute_scattered_recovery` — selects ONLY `top.txt` and `folderA` (non-contiguous,
     2 of the 3 backed-up items) and recovers them to original location. Real verdict (top.txt
     and folderA/deepA.txt restored to their backed-up content; folderB/deepB.txt STILL shows
     the `SCATTERED_B_MODIFIED_182437` sentinel, proving the unselected item was untouched) is
     read via WinRM by the agent and reported alongside this test's result.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import FileLevelRecoveryLocators as L

from ._helpers import build_flb_job, extract_item_names, flr_browse, recover_to_source, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-182437")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-182437_scattered"
DRILL_TO_PARENT = ["Local Disk (C:)", "RecoverToSource_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "RecoverToSource_ForFLB", "scattered"]


@allure.title("NJM-182437 phase 1/2 — baseline backup of the whole scattered tree")
@pytest.mark.flaky(reruns=0)
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["scattered"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == {"top.txt", "folderA", "folderB"}, f"expected all 3 seeded items, got {names}"


@allure.title("NJM-182437 phase 2/2 — recover only 2 of 3 non-contiguous items, leaving the "
               "3rd untouched")
@pytest.mark.flaky(reruns=0)
def test_execute_scattered_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    started = recover_to_source(
        page, JOB_NAME, FLR_DRILL_TO_FOLDER, ["top.txt", "folderA"], L.OVERWRITE_OVERWRITE,
    )
    assert started, "the FLR wizard did not confirm the recover-to-source recovery started"
    flb_job_cleanup(JOB_NAME)
