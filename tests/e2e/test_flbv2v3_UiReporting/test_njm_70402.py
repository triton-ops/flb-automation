r"""NJM-70402 — [FLB v1] Global Search - Verify Initiating Backup Copy from 'Backups' Search
Results.

Searches for the pre-existing, READ-ONLY REFERENCE job `FLB_BlankLine`'s backup (small fileset —
keeps the resulting Backup Copy run's real data-transfer time short), clicks its row's 'Backup
copy' action, confirms this launches the Backup Copy wizard PRE-SELECTED with that backup as
source, then completes the wizard for real — Backup Copy jobs are covered by the AUTO_FLB_*
safety fence per CLAUDE.md Golden Rule 3 (both FLB and Backup Copy live on nbr-84 under that
prefix; the SOURCE being copied is read-only access to a pre-existing job's backup, same as
NJM-70385's FLR browse). Builds its OWN uniquely-named job
(`AUTO_FLB_NJM-70402_gsearch-backupcopy`) so `flb_job_cleanup` can own its lifecycle like every
other TC in this project.

⚠ CALIBRATION NOTE (real finding, live 2026-07-21): this test does NOT use
`AUTO_FLB_GSEARCH_CALIB` (this suite's own reusable Global Search job, see `test_njm_70399.py`)
as the Backup Copy source, despite that being the more obvious choice. Confirmed live: once the
Global Search POM-building agent's own calibration pass ran a Backup Copy job against
AUTO_FLB_GSEARCH_CALIB's backup (creating `AUTO_FLB_GSEARCH_BACKUPCOPY_CALIB`), that backup's own
'Jobs' popover PERMANENTLY switched to showing the Backup Copy job's name instead of
'AUTO_FLB_GSEARCH_CALIB' — even after NJM-70399 reruns that job again. This is the SAME
'Jobs'-popover-shows-most-recent-toucher defect documented in full in
`check_global_search_flr.py`'s module docstring; it means 'AUTO_FLB_GSEARCH_CALIB' can no longer
be found as an owning-job label at all via `find_backup_row_by_job()`.

⚠ SECOND CALIBRATION NOTE (live 2026-07-21): an earlier version of this test used
`FLB_Iso_exe_items` as the source — its real backup data was large enough that the Backup Copy
run took well over 5 minutes (still `Running` after this test's own `wait_for_job_status`
timeout expired, confirmed `Successful` a few minutes later via a separate manual check).
`FLB_BlankLine`'s small fileset avoids that.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.backup_copy_page import BackupCopyPage
from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.global_search_page import GlobalSearchPage

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-70402")]

SOURCE_BACKUP_NAME = "Window11"
OWNING_JOB_NAME = "FLB_BlankLine"
# CALIBRATED live 2026-07-21 (see check_global_search_backup_copy.py): this wizard's Destination
# combo doesn't list every repo from environment.md (NFS_REPO/Wasabi_Repo/CIFS_REPO absent, most
# likely gated by source-backup-type compatibility) — Local-Immutable is present and distinct
# from the source's own Onboard repository.
DESTINATION_REPO = "Local-Immutable"
NEW_JOB_NAME = "AUTO_FLB_NJM-70402_gsearch-backupcopy"


@allure.title("NJM-70402 — initiate Backup Copy from Global Search 'Backups' results")
@pytest.mark.flaky(reruns=0)  # builds a uniquely-named job via Finish & Run — an automatic rerun
# would hit a duplicate-name conflict rather than a clean retry (see this project's documented
# duplicate-job-on-rerun lesson from suites D/F)
def test_backup_copy_from_global_search(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    gs = GlobalSearchPage(page)
    gs.open()
    gs.select_only_filter("Backups")
    gs.search(SOURCE_BACKUP_NAME)

    row_count = gs.result_row_count(SOURCE_BACKUP_NAME, category="Backups")
    assert row_count >= 1, f"expected {SOURCE_BACKUP_NAME!r} to appear under the Backups filter, got {row_count} rows"

    idx = gs.find_backup_row_by_job(SOURCE_BACKUP_NAME, OWNING_JOB_NAME)
    gs.open_backup_copy(SOURCE_BACKUP_NAME, nth=idx)

    bc = BackupCopyPage(page)
    assert "jobType=BACKUP_COPY" in page.url, (
        f"expected 'Backup copy' to navigate to the New Backup Copy Job Wizard, got url={page.url}"
    )
    assert bc.current_step_title() == "1. Backups", (
        f"expected the wizard to open on step '1. Backups', got {bc.current_step_title()!r}"
    )

    pre_selected = bc.pre_selected_backup_names()
    assert any(SOURCE_BACKUP_NAME in name for name in pre_selected), (
        f"expected {SOURCE_BACKUP_NAME!r} to be pre-selected in step 1, got: {pre_selected}"
    )

    bc.click_next()  # Backups -> Destination
    assert bc.current_step_title() == "2. Destination"
    bc.select_repository(DESTINATION_REPO)
    bc.click_next()  # Destination -> Schedule
    assert bc.current_step_title() == "3. Schedule"
    bc.set_run_on_demand()
    bc.click_next()  # Schedule -> Options
    assert bc.current_step_title() == "4. Options"
    bc.set_job_name(NEW_JOB_NAME)
    bc.finish_and_run()
    page.wait_for_timeout(1500)
    try:
        bc.confirm_run()
    except Exception:  # noqa: BLE001 — some wizard entry states auto-run without a confirm dialog
        pass
    page.wait_for_timeout(2000)

    dp = DataProtectionPage(page)
    dp.open()
    page.wait_for_timeout(1500)
    status = dp.wait_for_job_status(NEW_JOB_NAME, timeout_ms=300_000, poll_ms=10_000)
    assert status == "Successful", f"expected the Backup Copy job to complete successfully, got: {status}"

    flb_job_cleanup(NEW_JOB_NAME)
