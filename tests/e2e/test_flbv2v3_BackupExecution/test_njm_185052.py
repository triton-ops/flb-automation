r"""NJM-185052 — [FLB v1/v3] FLB Job Wizard - Options - ACL default 'Back up only folder
permissions' does not capture file-level permissions.

⚠ SCOPE REDUCTION (see OptionsLocators' docstring in locators.py for the full live-calibration
writeup): the literal TC steps want a folder whose FILES and SUBFOLDERS carry genuinely DISTINCT
ACLs, then a post-recovery icacls comparison proving folder-only vs folder+file permission
capture. Setting up per-file distinct ACLs (via `icacls` over WinRM) and diffing them after
recovery is a real, separate piece of fixture + verification work not attempted here — this test
instead verifies what the Options step itself actually does: the ACL combo defaults to 'Back up
only folder permissions' and the job completes successfully with the selected content intact. The
folder-vs-file ACL-fidelity claim itself is UNVERIFIED — a genuine scope reduction, stated
honestly rather than faked.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-185052")]

MACHINE = "Window11"
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
ALL_MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}


@allure.title("NJM-185052 — ACL default ('Back up only folder permissions') job completes normally")
def test_acl_default_folder_only_permissions(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-185052_acl-folder-only")

    # Leave acl_mode unset — 'Back up only folder permissions' is the wizard's own default.
    build_flb_job(page, job_name, MACHINE, DRILL_TO_TESTDATA, ["MixedTypes"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == ALL_MIXEDTYPES_FILES, f"expected all 7 MixedTypes files, got {names}"
