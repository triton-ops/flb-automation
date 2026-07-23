r"""NJM-70019 — [FLB v1/v2] FLB - Functional - Verify Use Case: Create and Run a Basic
File/Folder Backup Job (UC1 & UC2).

Uses the MixedTypes fixture (test-data/test-data.md — 7 deterministic files:
sample.pdf/xml/json/docx/sys/jpg/mp4) on Window11 (C:\TestData_ForFLB\MixedTypes): select the
whole MixedTypes FOLDER — basic file/folder backup.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-70019")]

MACHINE = "Window11"
# Wizard item-picker drill path (build_flb_job) vs FLR Files-step tree drill path (flr_browse) use
# DIFFERENT root-node naming for the same C: drive ('Local Disk (C:)' vs plain 'C:') — the same
# conflation bug already found+fixed once in test_repo_backup_matrix.py (see
# tests/e2e/test_flbv2v3_ObjectStorage's own flr_parent column) and re-found live here via a real
# test failure (flr_browse timed out drilling 'Local Disk (C:)' in the FLR tree, which doesn't use
# that label) before this fix — two separate FLR-facing constants, never share one.
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-70019 — basic file/folder backup job (UC1 & UC2)")
def test_basic_file_folder_backup(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70019_basic")

    build_flb_job(page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"expected all 7 MixedTypes files, got {names}"
