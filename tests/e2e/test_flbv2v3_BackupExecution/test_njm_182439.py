r"""NJM-182439 — [FLB v1/v3] FLB Job Wizard - Options - Back up folder and file permissions (ACL).

See test_njm_185052.py's module docstring for the shared scope-reduction note (folder-vs-file
ACL-fidelity is UNVERIFIED here — this test verifies the Options step's ACL combo accepts this
value and the job completes with content intact, not a genuine folder-vs-file permission diff).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-182439")]

MACHINE = "Window11"
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-182439 — ACL set to 'Back up folder and file permissions'")
def test_acl_folder_and_file_permissions(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-182439_acl-folder-and-file")

    build_flb_job(
        page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"],
        acl_mode="Back up folder and file permissions",
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"expected all 7 MixedTypes files, got {names}"
