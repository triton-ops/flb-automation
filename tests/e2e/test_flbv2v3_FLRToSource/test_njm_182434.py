r"""NJM-182434 — [FLB v3] FLB - Recover to Source - Rename recovered item if it exists.

TWO-PHASE, SAFETY-GATED TEST — see this suite's `_helpers.py` for the authorization scope.
  1. `test_baseline_backup` — builds+runs a job over `rename_test\target.txt` (seeded
     `RENAME_BACKED_UP_182434`). No cleanup call.
  2. Agent (via WinRM): modifies `target.txt` locally to `RENAME_LOCAL_EXISTING_182434` — a real
     conflicting item at the original path.
  3. `test_execute_rename_recovery` — recovers `target.txt` with overwrite behavior 'Rename
     recovered item if such item exists'. Real verdict (the original file must be PRESERVED at
     `RENAME_LOCAL_EXISTING_182434`, and a NEW renamed copy must appear alongside it carrying
     `RENAME_BACKED_UP_182434` — the exact rename convention this build uses, e.g. `target
     (1).txt`, is not assumed in advance and is reported as observed) is read via WinRM by the
     agent and reported alongside this test's result.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import FileLevelRecoveryLocators as L

from ._helpers import build_flb_job, extract_item_names, flr_browse, recover_to_source, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-182434")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-182434_rename"
DRILL_TO_PARENT = ["Local Disk (C:)", "RecoverToSource_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "RecoverToSource_ForFLB", "rename_test"]


@allure.title("NJM-182434 phase 1/2 — baseline backup of rename_test\\target.txt")
@pytest.mark.flaky(reruns=0)
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["rename_test"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == {"target.txt"}, f"expected the seeded target.txt, got {names}"


@allure.title("NJM-182434 phase 2/2 — recover to source with 'Rename recovered item if it exists'")
@pytest.mark.flaky(reruns=0)
def test_execute_rename_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    started = recover_to_source(
        page, JOB_NAME, FLR_DRILL_TO_FOLDER, ["target.txt"], L.OVERWRITE_RENAME,
    )
    assert started, "the FLR wizard did not confirm the recover-to-source recovery started"
    flb_job_cleanup(JOB_NAME)
