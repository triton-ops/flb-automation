r"""NJM-182538 — [FLB v1] FLB - Skipped items report - Verify download skipped items report.

Same fixture and same blocking product defect as NJM-182573 (see that test and _helpers.py's
module docstring): the report's own entry point ('View details') never opens, so there is no
report page to find a Download button on. This test independently reproduces the job-completes-
with-skips precondition and fails at the same "report opens" gate, this time framed around the
TC's actual ask (download the report), rather than duplicating 182573's assertion — if the
underlying defect is ever fixed, this test's later steps (Download button, file content) still
need writing, but the failure point today is identical and equally real.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, report_link_attrs, run_and_wait_flb_job, skipped_items_count

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-182538")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-182538_skip-report-download"


@allure.title("NJM-182538 — download skipped items report (blocked: report never opens)")
@pytest.mark.flaky(reruns=0)  # deterministic product-defect FAIL — see NJM-182573's same note
def test_download_skipped_items_report(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    build_flb_job(page, JOB_NAME, MACHINE, ["Local Disk (C:)"], ["SkipTest_ForFLB"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"expected 'Completed with warnings'-style success, got: {status}"

    count = skipped_items_count(page, JOB_NAME)
    assert count >= 1, f"expected at least one skipped item, got: {count}"

    attrs = report_link_attrs(page, JOB_NAME)
    assert attrs.get("action") == "report", f"expected the report link to be present, got: {attrs!r}"

    link = page.locator("//a[@data-action='report']").locator("visible=true")
    before_pages = len(page.context.pages)
    before_url = page.url
    link.first.click()
    page.wait_for_timeout(2500)

    report_reached = len(page.context.pages) > before_pages or page.url != before_url
    assert report_reached, (
        "PRODUCT DEFECT (same root cause as NJM-182573): the skipped-items report never opens, "
        "so there is no Download control reachable to exercise this TC's actual ask."
    )
    # Not reached today — left in place for when the report-open defect is fixed upstream.
    download_button = page.locator("//button[contains(translate(normalize-space(.), "
                                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), "
                                    "'download')]").locator("visible=true")
    assert download_button.count() > 0, "expected a Download control on the opened report page"

    flb_job_cleanup(JOB_NAME)
