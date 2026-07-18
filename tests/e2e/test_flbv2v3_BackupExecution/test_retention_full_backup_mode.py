r"""NJM-128607 / 128606 — [FLB v3] FLB - Functional (Retention) - Verify Active Full Creation (No
Source Changes); Verify Synthetic Full Creation (No Source Changes).

Covers 2 of the 6 "Active/Synthetic full creation" retention TCs in this execution
(NJM-128606/128607/128608/128609/128614/128615) — the other 4 are honestly DEFERRED, not
written, for the same reason documented in test_flbv2v3_IncludeExclude/test_njm_185023.py:
genuinely mutating source content BETWEEN two job runs (NJM-128608/128609's "with source
changes" pair) or deleting previously-backed-up files between runs (NJM-128614/128615's
"after deletion" pair) requires live WinRM access, which is only available to the agent driving
a session (mcp__remoting__*) — not to Python code executing inside a pytest test process. This
suite already corrected an earlier, wrong attempt to simulate "changed source" by editing a job's
own item SELECTION between runs instead (see ObjectStorage suite's run_full_then_incremental()
docstring for that exact correction) — repeating that same anti-pattern here to force these 4
TCs into "buildable" would reproduce the same mistake. Only the "no source changes" pair is
genuinely self-contained: run the SAME job twice, completely unmodified.

⚠ SECOND, INDEPENDENT SCOPE REDUCTION even for these 2 tests: the calibration pass that added
FlbWizardPage.set_full_backup_mode() (browser/pom/common/locators.py's OptionsLocators
docstring, recipes/file-backup-recipes.md's R4f section) found NO UI surface that distinguishes
an Active-full recovery point from a Synthetic-full one — the repository's Backups grid 'Type'
column reads plain 'Full' for both. So these tests verify what's actually checkable: the Full
Backup Settings mode + 'Job runs #'-every-run frequency are ACCEPTED, both runs complete
successfully, and recovered content is correct and unchanged across both runs — NOT that the
specific Active-full/Synthetic-full mechanism actually executed as configured. That deeper claim
remains an open, documented gap, not a faked pass.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution]

MACHINE = "Window11"
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-128607 — Active-full mode: two unmodified runs both succeed with correct content")
@pytest.mark.jira("NJM-128607")
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


@allure.title("NJM-128606 — Synthetic-full mode: two unmodified runs both succeed with correct content")
@pytest.mark.jira("NJM-128606")
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
