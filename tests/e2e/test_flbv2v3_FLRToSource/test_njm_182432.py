r"""NJM-182432 — [FLB v3] FLB - Recover to Source - Overwrite the original item.

TWO-PHASE, SAFETY-GATED TEST — see this suite's `_helpers.py` module docstring for the full
authorization scope (2026-07-20, explicit user go-ahead, strictly limited to paths under
`C:\RecoverToSource_ForFLB`). Procedure:
  1. `pytest test_njm_182432.py::test_baseline_backup` — builds+runs a job over
     `overwrite_test\target.txt` (seeded content `BACKED_UP_CONTENT_182432`). No flb_job_cleanup
     call — job survives into phase 2.
  2. Agent modifies `target.txt` LOCALLY via WinRM to different content (`MODIFIED_LOCAL_182432`)
     — simulating a real pre-existing conflicting item at the original path.
  3. `pytest test_njm_182432.py::test_execute_overwrite_recovery` — recovers `target.txt` to its
     original location with overwrite behavior 'Overwrite the original item'. Asserts the wizard
     confirmed the recovery started, then registers cleanup. The actual file-content verdict
     (does the source now show `BACKED_UP_CONTENT_182432` again?) is read by the agent via WinRM
     immediately after and reported alongside this test's result — pytest itself has no host
     access to assert on file content directly.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import FileLevelRecoveryLocators as L

from ._helpers import build_flb_job, extract_item_names, flr_browse, recover_to_source, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-182432")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-182432_overwrite"
DRILL_TO_PARENT = ["Local Disk (C:)", "RecoverToSource_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "RecoverToSource_ForFLB", "overwrite_test"]


@allure.title("NJM-182432 phase 1/2 — baseline backup of overwrite_test\\target.txt")
@pytest.mark.flaky(reruns=0)
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["overwrite_test"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == {"target.txt"}, f"expected the seeded target.txt, got {names}"


@allure.title("NJM-182432 phase 2/2 — recover to source with 'Overwrite the original item'")
@pytest.mark.flaky(reruns=0)
def test_execute_overwrite_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    started = recover_to_source(
        page, JOB_NAME, FLR_DRILL_TO_FOLDER, ["target.txt"], L.OVERWRITE_OVERWRITE,
    )
    assert started, "the FLR wizard did not confirm the recover-to-source recovery started"
    flb_job_cleanup(JOB_NAME)
