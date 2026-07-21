r"""NJM-182545 — [FLB v1] FLB - Skipped items report - Verify column "Location" shows full path
(Windows C:\... and Linux /home/...).

The TC's literal precondition is ONE job with BOTH a Windows and a Linux source folder containing
skippable items. That single-job combination hit a reproducible item-picker bug live (see
_helpers.py's module docstring: adding a SECOND source machine's item via open_item_picker()
times out finding a folder that IS present at that machine's own picker root when it's the ONLY
source — confirmed both directions). This test instead builds TWO separate single-source jobs
(Windows-only, Linux-only) using the same dangling-symlink skip fixture on each OS, confirming
the skip precondition independently holds on both — then hits the SAME already-documented
report-open defect (NJM-182573) for the actual Location-column check, on both jobs.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, report_link_attrs, run_and_wait_flb_job, skipped_items_count

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-182545")]

WIN_JOB = "AUTO_FLB_NJM-182545_win-location"
LINUX_JOB = "AUTO_FLB_NJM-182545_linux-location"


@allure.title("NJM-182545 — skipped items report 'Location' column, Windows + Linux (blocked: report never opens)")
@pytest.mark.flaky(reruns=0)  # deterministic product-defect FAIL — see NJM-182573's same note
def test_location_column_windows_and_linux(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    # --- Windows side ---
    build_flb_job(page, WIN_JOB, "Window11", ["Local Disk (C:)"], ["SkipTest_ForFLB"])
    win_status = run_and_wait_flb_job(page, WIN_JOB, timeout_ms=300_000)
    assert win_status == "Successful", f"Windows job did not complete: {win_status}"
    win_count = skipped_items_count(page, WIN_JOB)
    assert win_count >= 1, f"expected a Windows-side skip, got: {win_count}"
    win_attrs = report_link_attrs(page, WIN_JOB)
    assert win_attrs.get("action") == "report", f"expected a Windows report link, got: {win_attrs!r}"

    # --- Linux side ---
    build_flb_job(page, LINUX_JOB, "Linux_16.84", [], ["SkipTest_ForFLB"], is_linux=True)
    linux_status = run_and_wait_flb_job(page, LINUX_JOB, timeout_ms=300_000)
    assert linux_status == "Successful", f"Linux job did not complete: {linux_status}"
    linux_count = skipped_items_count(page, LINUX_JOB)
    assert linux_count >= 1, f"expected a Linux-side skip, got: {linux_count}"
    linux_attrs = report_link_attrs(page, LINUX_JOB)
    assert linux_attrs.get("action") == "report", f"expected a Linux report link, got: {linux_attrs!r}"

    # --- Attempt to open each report and read the Location column (both expected to fail the
    # same way as NJM-182573) ---
    for job_name, os_label in ((WIN_JOB, "Windows"), (LINUX_JOB, "Linux")):
        from browser.pom.common.data_protection_page import DataProtectionPage
        DataProtectionPage(page).select_job_row(job_name)
        page.wait_for_timeout(1000)
        link = page.locator("//a[@data-action='report']").locator("visible=true")
        before_pages = len(page.context.pages)
        before_url = page.url
        link.first.click()
        page.wait_for_timeout(2500)
        report_reached = len(page.context.pages) > before_pages or page.url != before_url
        assert report_reached, (
            f"PRODUCT DEFECT (same root cause as NJM-182573): the {os_label} job's skipped-items "
            "report never opens, so the 'Location' column cannot be checked."
        )

    flb_job_cleanup(WIN_JOB)
    flb_job_cleanup(LINUX_JOB)
