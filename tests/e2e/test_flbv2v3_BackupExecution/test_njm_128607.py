r"""NJM-128607 — [FLB v3] FLB - Functional (Retention) - Verify Active Full Creation (No Source
Changes).

⚠ SCOPE REDUCTION: the calibration pass that added FlbWizardPage.set_full_backup_mode()
(browser/pom/common/locators.py's OptionsLocators docstring, recipes/file-backup-recipes.md's
R4f section) found NO UI surface that distinguishes an Active-full recovery point from a
Synthetic-full one — the repository's Backups grid 'Type' column reads plain 'Full' for both. So
this test verifies what's actually checkable: the Full Backup Settings mode + 'Job runs #'-every-
run frequency are ACCEPTED, both runs complete successfully, and recovered content is correct and
unchanged across both runs — NOT that the Active-full mechanism actually executed as configured.
That deeper claim remains an open, documented gap, not a faked pass.

The other "with source changes" / "after deletion" retention TCs in this Xray execution have their
own files (test_njm_128608.py, test_njm_128609.py, test_njm_128614.py, test_njm_128615.py) — those
genuinely mutate source content or delete previously-backed-up files BETWEEN two job runs, which
needs live WinRM access, so they're written as two-phase tests (see test_njm_185029.py's module
docstring for the full procedure). This TC is simpler and self-contained: run the SAME job twice,
completely unmodified.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-128607")]

MACHINE = "Window11"
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-128607 — Active-full mode: two unmodified runs both succeed with correct content")
def test_active_full_no_source_changes(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-128607_active-full-nochange")

    build_flb_job(page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"], full_backup_mode="Active full")
    first_status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert first_status == "Successful", f"first (baseline) run did not succeed: {first_status}"

    page.wait_for_timeout(5000)
    second_status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert second_status == "Successful", f"second (full-mode) run did not succeed: {second_status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"expected all 7 MixedTypes files unchanged, got {names}"
