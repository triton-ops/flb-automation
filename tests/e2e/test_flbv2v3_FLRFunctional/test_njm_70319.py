"""NJM-70319 — [FLB v1] FLR from FLB - Functional - Verify Recovery from Source with a Large
Number of Subfolders. Original status: never executed under the old RPC workflow (no
cases/*.md runbook exists).

Per the TC's own Xray steps: confirm a valid FLB recovery point exists for a source with a large
number of subfolders; open Recover > Individual files; on the Files step, select the ROOT folder
containing all subfolders (not individual items) so the whole subtree is added to the recovery
list; on the Options step choose Recover to CIFS Share, finish and run; on the destination share,
verify all subfolders and their files are present with matching content.

FIXTURE: `Subfolder_200Folders/` under `C:\\TestData_ForFLB` on Window11 — 218 files across 4
top-level dirs, including nested Folder1/Folder2 and ~200 flat Item_NNN.txt-style leaf files (see
test-data/test-data.md §1) — the project's dedicated deep-nesting/large-item-count fixture.

SCOPE NOTE (same convention as NJM-70307/70327/70328): pytest asserts only on what the browser can
observe — the wizard's own recovery-started confirmation and the FLB job's Successful status.
Destination-content verification (all subfolders/files present with matching content, TC step 5)
is done separately by the agent driving WinRM against win-fs3 and reported alongside this test's
result — pytest itself cannot call the remoting tools this project uses for that.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70319")]

MACHINE = "Window11"


@allure.title("NJM-70319 — Recover a large-subfolder-count source (root selection) to CIFS share")
def test_recover_large_subfolder_source_to_cifs(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-70319")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    # TC step 3: select the ROOT folder containing all subfolders — this means ticking
    # 'Subfolder_200Folders' ITSELF from its PARENT (TestData_ForFLB) listing so the whole
    # nested tree recovers, NOT drilling into it first and calling select_root() there (which
    # would only tick whichever child happens to render first within it, e.g. an empty
    # 'Folder1/' — confirmed live via WinRM destination inspection on win-fs3: an earlier version
    # of this test that drilled one level too deep recovered a zip containing only a single
    # empty 'Folder1/' entry, not the fixture's real 218 files. This is what path_segments
    # (stopping at TestData_ForFLB) + filenames=['Subfolder_200Folders'] achieves.
    started = recover_to_share(
        page, job_name, ["C:", "TestData_ForFLB"], ["Subfolder_200Folders"], "cifs"
    )
    assert started, "the FLR wizard did not confirm the recovery started"
