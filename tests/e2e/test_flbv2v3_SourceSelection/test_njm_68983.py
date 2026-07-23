r"""NJM-68983 — [FLB v2] FLB - Functional - Verify Backup/Recovery of Dotfiles: .hidden_config,
.env.sample.

Backs up the whole Windows folder containing the special file(s) (so the picker's own display
never has to type/round-trip the dotfile name), runs the job, opens FLR, selects the target
file(s), and recovers them to a CIFS share.

FIXTURE (seeded 2026-07-18, registered in test-data/test-data.md §7): C:\SpecialFiles_ForFLB on
Window11 (win11 / 10.10.16.157), a single flat folder holding all 13 probe files for this matrix.
Source SHA-256 oracle: test-data/manifests/manifest-win11-specialfiles.sha256. Re-seed with the
idempotent WinRM PowerShell in that manifest's test-data.md §7 entry.

SCOPE NOTE (same convention as the whole FLRFunctional suite): pytest asserts the job reached
Successful and the FLR wizard confirmed the recovery started. The TC's verdict-carrying step
("recovered filenames/content match the originals") is the agent-driven destination check —
comparing the landed Recovered-items-*.zip's entries on win-fs3 against the manifest above — and
is reported alongside this test's result, not as a pytest assertion (pytest can't call the
remoting tools).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-68983"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"
FIXTURE_FOLDER = "SpecialFiles_ForFLB"


@allure.title("NJM-68983 — backup/recovery of dotfiles (Windows), recover to CIFS")
def test_special_file_backup_recovery(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68983")

    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], [FIXTURE_FOLDER])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    started = recover_to_share(
        page, job_name, ["C:", FIXTURE_FOLDER], [".hidden_config", ".env.sample"], "cifs"
    )
    assert started, "the FLR wizard did not confirm the recovery started"
