r"""NJM-70385 — [FLB v1] Global Search - Verify Initiating FLR from 'Backups' Search Results.

Browse-only: ticks the root node to reach the Files step and satisfy its selection gate, but
NEVER clicks the final 'Recover' action — cancels out via `click_cancel()` instead (this
project's established "browse != execute" distinction, e.g. `check_overwrite_behavior_combo.py`).

Targets the pre-existing, READ-ONLY REFERENCE job `FLB_Win11`'s own backup (never Run/Edit/
Manage/Delete — only ever browsed here, which the safety fence in CLAUDE.md permits) rather than
this suite's own `AUTO_FLB_GSEARCH_CALIB` job, deliberately: once a Backup Copy job has run
against a backup (as NJM-70402's test does, against AUTO_FLB_GSEARCH_CALIB's backup), Global
Search's own 'Jobs' popover for that SAME backup switches its displayed owning-job link to the
Backup Copy job's name instead of the original — a genuine, live-confirmed product finding (see
`browser/checks/check_global_search_flr.py`'s module docstring for the full writeup), not a POM
bug. Targeting FLB_Win11 (never touched by any Backup Copy job) keeps this test's disambiguation
by owning-job name stable across repeat runs.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from browser.pom.common.global_search_page import GlobalSearchPage
from browser.pom.common.locators import GlobalSearchLocators

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-70385")]

SOURCE_BACKUP_NAME = "Window11"
OWNING_JOB_NAME = "FLB_Win11"


@allure.title("NJM-70385 — initiate File Level Recovery from Global Search 'Backups' results")
def test_flr_from_global_search(logged_in_page):
    page = logged_in_page

    gs = GlobalSearchPage(page)
    gs.open()
    gs.select_only_filter("Backups")
    gs.search(SOURCE_BACKUP_NAME)

    row_count = gs.result_row_count(SOURCE_BACKUP_NAME, category="Backups")
    assert row_count >= 1, f"expected {SOURCE_BACKUP_NAME!r} to appear under the Backups filter, got {row_count} rows"

    idx = gs.find_backup_row_by_job(SOURCE_BACKUP_NAME, OWNING_JOB_NAME)
    gs.open_file_level_recovery(SOURCE_BACKUP_NAME, nth=idx)

    flr = FileLevelRecoveryPage(page)
    assert "jobType=FILE_LEVEL_RECOVERY" in page.url, (
        f"expected 'File level recovery' to navigate to the FLR wizard, got url={page.url}"
    )
    assert flr.current_step_title() == "1. Backup", (
        f"expected the wizard to open on step '1. Backup', got {flr.current_step_title()!r}"
    )

    points = flr.list_recovery_points()
    assert len(points) >= 1, f"expected the recovery-point picker to be pre-populated, got: {points}"
    assert any(p["selected"] for p in points), f"expected one recovery point pre-selected, got: {points}"

    flr.click_next()  # Backup -> Files
    page.wait_for_timeout(1000)
    assert flr.current_step_title() == "2. Files", f"expected step 'Files', got {flr.current_step_title()!r}"

    flr.wait_files_ready(timeout=180_000)
    assert flr.files_ready(), "expected the recovery point to finish mounting"

    flr.select_root()  # satisfy the Files-step selection gate — browse-only, never downloads

    flr.click_cancel()  # never executes a recovery
    page.wait_for_timeout(1000)
    assert "jobType=FILE_LEVEL_RECOVERY" not in page.url, "expected the wizard to close cleanly via Cancel"

    nav_reachable = page.locator(GlobalSearchLocators.NAV_SEARCH).locator("visible=true").count() > 0
    assert nav_reachable, "expected the left-nav 'Search' item to be reachable again after Cancel"
