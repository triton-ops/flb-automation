r"""NJM-182435 — [FLB v3] FLB - Recover to Source - Preserve original directory structure.

TWO-PHASE, SAFETY-GATED TEST — see this suite's `_helpers.py` for the authorization scope.
  1. `test_baseline_backup` — builds+runs a job over the whole `nested_structure\a\b\c\` tree
     (seeded `deepfile.txt` = `NESTED_182435`, 3 levels deep). No cleanup call.
  2. Agent (via WinRM): DELETES the entire `nested_structure` tree from the source (parent
     folders and all), so recovery must recreate the full nested path from scratch.
  3. `test_execute_nested_recovery` — recovers `deepfile.txt` to its original location.
     Overwrite behavior doesn't matter here (nothing exists to conflict with), so 'Overwrite the
     original item' is used for consistency with the other happy-path recoveries in this suite.
     Real verdict (the full `a\b\c\deepfile.txt` path must be recreated, with matching content)
     is read via WinRM by the agent and reported alongside this test's result.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import FileLevelRecoveryLocators as L

from ._helpers import build_flb_job, extract_item_names, flr_browse, recover_to_source, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-182435")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-182435_nested"
DRILL_TO_PARENT = ["Local Disk (C:)", "RecoverToSource_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "RecoverToSource_ForFLB", "nested_structure", "a", "b", "c"]


@allure.title("NJM-182435 phase 1/2 — baseline backup of nested_structure\\a\\b\\c\\deepfile.txt")
@pytest.mark.flaky(reruns=0)
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["nested_structure"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == {"deepfile.txt"}, f"expected the seeded deepfile.txt, got {names}"


@allure.title("NJM-182435 phase 2/2 — recover to source preserves the original nested path")
@pytest.mark.flaky(reruns=0)
def test_execute_nested_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    started = recover_to_source(
        page, JOB_NAME, FLR_DRILL_TO_FOLDER, ["deepfile.txt"], L.OVERWRITE_OVERWRITE,
    )
    assert started, "the FLR wizard did not confirm the recover-to-source recovery started"
    flb_job_cleanup(JOB_NAME)
