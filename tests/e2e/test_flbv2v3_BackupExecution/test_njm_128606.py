r"""NJM-128606 — [FLB v3] FLB - Functional (Retention) - Verify Synthetic Full Creation (No Source
Changes).

⚠ SCOPE REDUCTION: same scope note as test_njm_128607.py (Active-full's sibling TC) — no UI marker
distinguishes a Synthetic-full recovery point from an Active-full one, so this verifies the
setting is accepted and both runs complete with correct, unchanged content — not that the
Synthetic-full mechanism actually executed as configured. That deeper claim remains an open,
documented gap, not a faked pass.

The "with source changes" / "after deletion" sibling TCs have their own two-phase files
(test_njm_128608.py, test_njm_128609.py, test_njm_128614.py, test_njm_128615.py) — this TC is
simpler and self-contained: run the SAME job twice, completely unmodified.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-128606")]

MACHINE = "Window11"
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-128606 — Synthetic-full mode: two unmodified runs both succeed with correct content")
def test_synthetic_full_no_source_changes(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-128606_synthetic-full-nochange")

    build_flb_job(page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"], full_backup_mode="Synthetic full")
    first_status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert first_status == "Successful", f"first (baseline) run did not succeed: {first_status}"

    page.wait_for_timeout(5000)
    second_status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert second_status == "Successful", f"second (full-mode) run did not succeed: {second_status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"expected all 7 MixedTypes files unchanged, got {names}"
