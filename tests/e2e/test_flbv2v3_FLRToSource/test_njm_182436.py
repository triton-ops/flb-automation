r"""NJM-182436 — [FLB v3] FLB - Recover to Source - Recover the entire root folder.

TWO-PHASE, SAFETY-GATED TEST — see this suite's `_helpers.py` for the authorization scope.
  1. `test_baseline_backup` — builds+runs a job over the whole `root_recover\` tree (seeded
     `sub1\a.txt` = `ROOT_A_182436`, `sub2\b.txt` = `ROOT_B_182436`). No cleanup call.
  2. Agent (via WinRM): DELETES the entire `root_recover` folder from the source.
  3. `test_execute_root_recovery` — selects the top-level `root_recover` node itself (not its
     individual children) and recovers it to original location. Real verdict (the WHOLE tree —
     both subfolders and files, matching content — must be restored) is read via WinRM by the
     agent and reported alongside this test's result.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import FileLevelRecoveryLocators as L

from ._helpers import build_flb_job, extract_item_names, flr_browse, recover_to_source, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-182436")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-182436_root"
DRILL_TO_PARENT = ["Local Disk (C:)", "RecoverToSource_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "RecoverToSource_ForFLB"]


@allure.title("NJM-182436 phase 1/2 — baseline backup of the whole root_recover tree")
@pytest.mark.flaky(reruns=0)
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["root_recover"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == {"root_recover"}, f"expected the seeded root_recover folder, got {names}"


@allure.title("NJM-182436 phase 2/2 — recover the entire root_recover folder to source")
@pytest.mark.flaky(reruns=0)
def test_execute_root_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    started = recover_to_source(
        page, JOB_NAME, FLR_DRILL_TO_FOLDER, ["root_recover"], L.OVERWRITE_OVERWRITE,
    )
    assert started, "the FLR wizard did not confirm the recover-to-source recovery started"
    flb_job_cleanup(JOB_NAME)
