r"""NJM-70314 — [FLB v1] FLR from FLB - Options Step - Verify All Recovery Destinations and
Overwrite Settings.

SAFE, BROWSE-ONLY TEST — never selects/executes 'Recovery to original location', only confirms
each Recovery-type option is selectable and reveals its own expected sub-fields. No authorization
needed (unlike every other test in this suite), since nothing here ever writes to the source or
any external target — the wizard is cancelled out of before Finish/Recover on every path.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.backup_types.file_level_recovery_page import FileLevelRecoveryPage
from browser.pom.common.locators import FileLevelRecoveryLocators as L

from ._helpers import build_flb_job, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrtosource, pytest.mark.jira("NJM-70314")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-70314_options"
DRILL_TO_PARENT = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_FOLDER = ["C:", "TestData_ForFLB", "MixedTypes"]


@allure.title("NJM-70314 — Options step exposes all 4 recovery destinations + overwrite settings")
def test_all_recovery_destinations_and_overwrite_settings(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup(JOB_NAME)

    build_flb_job(page, job_name, MACHINE, DRILL_TO_PARENT, ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    flr = FileLevelRecoveryPage(page)
    flr.recover_file_level(job_name)
    page.wait_for_timeout(2000)
    flr.click_next()
    page.wait_for_timeout(2000)
    flr.wait_files_ready(timeout=180_000)
    flr.drill_to(FLR_DRILL_TO_FOLDER)
    flr.select_file_in_current_folder("sample.pdf")
    flr.click_next()  # Options

    # 'Recovery to original location' — the default — reveals 'Overwrite behavior'.
    assert flr.has_overwrite_behavior(), "expected 'Overwrite behavior' visible for 'original'"

    # 'Recover to custom location (CIFS/NFS)' — reveals Share type / Path to the share, and
    # hides 'Overwrite behavior' (that field is original-location-only).
    flr.choose_recovery_type("custom")
    assert not flr.has_overwrite_behavior(), "'Overwrite behavior' should be hidden for 'custom'"
    assert flr.is_visible(L.SHARE_TYPE_LABEL), "expected 'Share type:' visible for 'custom'"
    assert flr.is_visible(L.PATH_TO_SHARE_LABEL), "expected 'Path to the share:' visible for 'custom'"

    # 'Download' — no share/overwrite fields.
    flr.choose_recovery_type("download")
    assert not flr.has_overwrite_behavior(), "'Overwrite behavior' should be hidden for 'download'"

    # 'Forward via email' — no share/overwrite fields.
    flr.choose_recovery_type("email")
    assert not flr.has_overwrite_behavior(), "'Overwrite behavior' should be hidden for 'email'"

    flr.click_cancel()
