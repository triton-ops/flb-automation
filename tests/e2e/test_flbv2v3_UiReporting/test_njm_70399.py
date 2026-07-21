r"""NJM-70399 — [FLB v1] Global Search - Verify Running an FLB Job from 'Jobs' Search Results.

Uses the pre-existing `AUTO_FLB_GSEARCH_CALIB` job (built once during this suite's Global Search
POM calibration — see `browser/checks/check_global_search_run_job.py`'s module docstring — and
intentionally left in place for reuse, same pattern as `health_check.py`'s `AUTO_FLB_HEALTHCHECK`
sentinel). This test only ever RUNS that job (never Edit/Manage/Delete) — it is within the
AUTO_FLB_* safety fence, and re-running it repeatedly is the whole point of a reusable
calibration job. No `flb_job_cleanup` call: this test doesn't own the job's lifecycle.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.global_search_page import GlobalSearchPage

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-70399")]

JOB_NAME = "AUTO_FLB_GSEARCH_CALIB"


@allure.title("NJM-70399 — run an FLB job from Global Search 'Jobs & Groups' results")
def test_run_job_from_global_search(logged_in_page):
    page = logged_in_page

    gs = GlobalSearchPage(page)
    gs.open()
    gs.select_only_filter("Jobs & Groups")
    gs.search(JOB_NAME)

    row_count = gs.result_row_count(JOB_NAME, category="Jobs & Groups")
    assert row_count >= 1, f"expected {JOB_NAME!r} to appear under the Jobs & Groups filter, got {row_count} rows"

    category = gs.result_category(JOB_NAME)
    assert category == "Jobs & Groups", f"expected the result row's Category to read 'Jobs & Groups', got {category!r}"

    gs.run_job(JOB_NAME)

    dp = DataProtectionPage(page)
    dp.open()
    status = dp.wait_for_job_status(JOB_NAME, timeout_ms=300_000, poll_ms=10_000)
    assert status == "Successful", f"expected the Global-Search-triggered run to succeed, got: {status}"
