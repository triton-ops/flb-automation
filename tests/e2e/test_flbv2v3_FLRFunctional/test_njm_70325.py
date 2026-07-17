"""NJM-70325 — [FLB v1] FLR from FLB - Functional - Verify 'Download to Browser' Recovery Option.

Per the TC's own Xray steps: confirm a valid FLB recovery point, open Recover > Individual files,
select a mix of files/folders on the Files step, choose 'Download to browser' on the Options
step, finish and run — a download prompt/zip should appear, and the downloaded zip's contents
must match the selected files and folders.

Reuses FileLevelRecoveryPage.download_selected() (already calibrated in this POM for the
Inventory suite's checksum verification) — this TC additionally exercises a MIX of one file and
one folder selected together, and asserts the zip contains entries from both.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import allure
import pytest

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage

from ._helpers import build_flb_job, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70325")]

MACHINE = "Window11"
DOWNLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "results" / "test-results" / "_downloads"


@allure.title("NJM-70325 — Download to browser recovery option (mixed file + folder)")
def test_download_to_browser_mixed_selection(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70325")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name)
    page.wait_for_timeout(2000)
    flr.click_next()
    page.wait_for_timeout(2000)
    flr.wait_files_ready(timeout=180_000)
    flr.drill_to(["C:", "TestData_ForFLB"])
    flr.select_file_in_current_folder("atest1.txt")
    flr.select_file_in_current_folder("Folder_test2")

    zip_path = flr.download_selected(DOWNLOAD_DIR)
    assert zip_path.exists(), f"downloaded zip not found at {zip_path}"

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        assert any(Path(n).name == "atest1.txt" for n in names), (
            f"selected file 'atest1.txt' missing from downloaded zip (entries: {names})"
        )
        assert any("Folder_test2" in n for n in names), (
            f"selected folder 'Folder_test2' missing from downloaded zip (entries: {names})"
        )
