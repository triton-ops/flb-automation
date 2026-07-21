r"""NJM-182433 — [FLB v3] FLB - Recover to Source - Skip if item exists.

TWO-PHASE, SAFETY-GATED TEST — see this suite's `_helpers.py` for the authorization scope.
  1. `test_baseline_backup` — builds+runs a job over `skip_test\{existing.txt,missing.txt}`
     (seeded `EXISTING_ORIGINAL_182433` / `MISSING_BACKED_UP_182433`). No cleanup call.
  2. Agent (via WinRM): modifies `existing.txt` locally to `EXISTING_MODIFIED_182433` (still
     present, different content — a real conflict) and DELETES `missing.txt` entirely (so it's
     genuinely absent at recovery time, not just different).
  3. `test_execute_skip_recovery` — recovers BOTH files with overwrite behavior 'Skip recovered
     item if such item exists'. Real verdict (existing.txt must stay at
     `EXISTING_MODIFIED_182433` — skipped, untouched; missing.txt must reappear with
     `MISSING_BACKED_UP_182433` — restored, since it didn't conflict) is read via WinRM by the
     agent and reported alongside this test's result.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import FileLevelRecoveryLocators as L

from ._helpers import build_flb_job, extract_item_names, flr_browse, recover_to_source, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-182433")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-182433_skip"
DRILL_TO_PARENT = ["Local Disk (C:)", "RecoverToSource_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "RecoverToSource_ForFLB", "skip_test"]


@allure.title("NJM-182433 phase 1/2 — baseline backup of skip_test\\{existing,missing}.txt")
@pytest.mark.flaky(reruns=0)
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, DRILL_TO_PARENT, ["skip_test"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, JOB_NAME, FLR_DRILL_TO_FOLDER)))
    assert names == {"existing.txt", "missing.txt"}, f"expected both seeded files, got {names}"


@allure.title("NJM-182433 phase 2/2 — recover to source with 'Skip if item exists'")
@pytest.mark.flaky(reruns=0)
def test_execute_skip_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    started = recover_to_source(
        page, JOB_NAME, FLR_DRILL_TO_FOLDER, ["existing.txt", "missing.txt"], L.OVERWRITE_SKIP,
    )
    assert started, "the FLR wizard did not confirm the recover-to-source recovery started"
    flb_job_cleanup(JOB_NAME)
