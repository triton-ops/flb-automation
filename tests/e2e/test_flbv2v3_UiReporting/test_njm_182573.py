r"""NJM-182573 — [FLB v1] FLB - Skipped items report - Verify the per-object Skipped items report
link is added to the Last Run section / Job contents widget.

Fixture: `C:\SkipTest_ForFLB` on win11 (`Window11`) contains two normal files plus one dangling
symlink (`broken_link.txt`, created via `mklink` to a non-existent target) — see _helpers.py's
module docstring for why this (not an ACL deny, not a file lock) is the fixture that actually
produces a skipped item on this build.

Steps 1-4 of the TC (machine with skippable items; job build+run; Last Run / Job contents widget
visible; per-object report link present) all PASS — confirmed live. Step 5 (click the link,
verify it opens the correct per-object report) FAILS: this is a genuine, reproducible PRODUCT
DEFECT, not a POM/locator bug — see _helpers.py's module docstring for the six independent click
strategies tried (including `--disable-popup-blocking`, which revealed the link's `window.open()`
call has no real report URL and just opens a blank duplicate of the whole app).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, report_link_attrs, run_and_wait_flb_job, skipped_items_count

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-182573")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-182573_skip-report-link"


@allure.title("NJM-182573 — per-object skipped items report link is present but does not open a report")
@pytest.mark.flaky(reruns=0)  # deterministic product-defect FAIL, not flakiness — a rerun just
# wastes ~5min and risks building a second same-named AUTO_FLB_* job (see suite F/D's documented
# duplicate-job-on-rerun lesson)
def test_skipped_items_report_link(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    build_flb_job(page, JOB_NAME, MACHINE, ["Local Disk (C:)"], ["SkipTest_ForFLB"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"expected the job to complete despite the skip, got: {status}"

    count = skipped_items_count(page, JOB_NAME)
    assert count == 1, f"expected exactly 1 skipped item (the dangling symlink), got: {count}"

    attrs = report_link_attrs(page, JOB_NAME)
    assert attrs.get("action") == "report", (
        f"expected a per-object skipped-items report link (data-action='report') in the Job "
        f"Info / Events widget, got: {attrs!r}"
    )
    assert attrs.get("eventCode") == "error346", f"expected event code error346, got: {attrs!r}"

    # Step 5: click the link and verify it opens the correct per-object report.
    link = page.locator("//a[@data-action='report']").locator("visible=true")
    before_url = page.url
    before_pages = len(page.context.pages)
    link.first.click()
    page.wait_for_timeout(2500)

    opened_new_page = len(page.context.pages) > before_pages
    navigated_same_page = page.url != before_url
    assert opened_new_page or navigated_same_page, (
        "PRODUCT DEFECT: clicking the per-object skipped-items report link ('View details', "
        f"data-vid={attrs.get('vid')}) does nothing — no new tab opened and the current page "
        f"stayed at {before_url}. See _helpers.py module docstring for the full investigation "
        "(6 click strategies tried, including --disable-popup-blocking which showed the link's "
        "window.open() call has no real report URL)."
    )

    flb_job_cleanup(JOB_NAME)
