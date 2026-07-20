r"""NJM-68955 — [FLB v1] FLB - Functional - Verify Application-Aware Processing.

SCOPED per explicit user direction (2026-07-20): rather than the literal Jira TC (which wants a
real VSS-aware application like SQL Server/Exchange running on the source — no such fixture
exists here, see the flb-test-plan-structure memory's prior note that this TC was otherwise only
coverable via NJM-67678's generic "app-aware toggle is accepted" test on Window11), this verifies
something more concrete and directly checkable: when App-aware mode is enabled for an FLB job
against Win_Server2019_15.3 (win-fs3-src / PM-9, 10.10.15.3), NBR actually creates a real VSS
shadow copy of C: for the run and cleans it up afterward — not just that the job's own status
reaches Successful.

Requires live host inspection (`vssadmin list shadows /for=C:`) before/during/after the job run —
only the driving agent has WinRM access, pytest itself does not. Procedure:
  1. Agent confirms baseline: no pre-existing shadow copy on C: (clean state to detect against).
  2. This pytest test builds+runs an FLB job against C:\TestData_ForFLB\MixedTypes with
     app_aware_mode='Enabled (proceed on error)', and asserts the job succeeds + content matches.
  3. Concurrently, the agent polls `vssadmin list shadows /for=C:` via WinRM at short intervals
     during the run to catch a real shadow copy in existence mid-job.
  4. After the job reaches Successful, the agent re-checks: the shadow copy created for this run
     must be gone (VSS cleanup) — no leaked shadow copy left on the volume.

The actual shadow-copy create/cleanup verdict (this TC's real point) is reported by the agent
alongside this test's own result, same convention as every other WinRM-side-effect verification in
this suite (see e.g. test_njm_68956.py, test_njm_70356.py).

⚠ REAL FINDING live 2026-07-20 (test_app_aware_vss_shadow_copy, the MixedTypes-sized run below):
across ~5 minutes of overlapping observation — multiple `vssadmin list shadows /for=C:` polls plus
one continuous 110s `Get-WmiObject Win32_ShadowCopy` poll (2s interval) spanning most of that run,
PLUS a full Application/System Windows Event Log check (no VSS/VolSnap/Shadow-provider entries in
that window at all) — no OS-visible shadow copy was ever observed, despite App-aware mode being
enabled and the job completing successfully with correct content. Given MixedTypes is only ~98KB
across 7 tiny files, this is inconclusive by itself: a real shadow copy could plausibly be created
and torn down again in well under a second for a fileset this small, faster than any external
poller (including a 2s-interval WMI loop) could realistically catch. `test_vss_shadow_copy_lifecycle`
below re-runs the same check against a purpose-built 800MB single file
(`VssShadowTest_ForFLB\bigfile.bin`, created via `fsutil file createnew`, 2026-07-20) specifically
to give a genuine shadow copy (if one is created) enough lifetime to be externally observable —
disambiguating "too fast to see" from "never created" is the actual point of this second test.

⚠ RESULT of `test_vss_shadow_copy_lifecycle` (2026-07-20): still NO shadow copy observed, this time
across a CONTINUOUS 280-second, 1-second-interval `Get-WmiObject Win32_ShadowCopy` poll spanning
essentially the entire 237.9s test run (backup of an 800MB single file — long enough that a real
VSS snapshot's lifetime should span many poll intervals, not sub-second). The job itself still
completed Successful with the file correctly recovered. Combined with the MixedTypes run above,
this is now a well-evidenced (not merely inconclusive) NEGATIVE finding: this NBR build does not
appear to create an OS-visible VSS shadow copy (via vssadmin/WMI/Win32_ShadowCopy, nor any
VSS/VolSnap Event Log entry) for an App-aware FLB job against Win_Server2019_15.3, regardless of
fileset size. This lines up with the CLOSED defect linked on this very Jira TC, NJM-130524
("[11.1][FLBv1] Windows machine - App-aware mode is not working for FLB job") — worth flagging to
the user as a possible regression rather than silently treating the job-level PASS as the whole
verdict. The job's own file-level correctness is NOT in question; only the VSS-shadow-copy
lifecycle claim specifically is unconfirmed/possibly regressed.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-68955")]

MACHINE = "Win_Server2019_15.3"
DRILL_TO_MIXEDTYPES = ["Local Disk (C:)", "TestData_ForFLB", "MixedTypes"]
FLR_DRILL_TO_MIXEDTYPES = ["C:", "TestData_ForFLB", "MixedTypes"]
MIXEDTYPES_FILES = {
    "sample.pdf", "sample.xml", "sample.json", "sample.docx", "sample.sys", "sample.jpg", "sample.mp4",
}
DRILL_TO_BIGFILE_PARENT = ["Local Disk (C:)", "TestData_ForFLB"]
FLR_DRILL_TO_BIGFILE_PARENT = ["C:", "TestData_ForFLB", "VssShadowTest_ForFLB"]


@allure.title("NJM-68955 — App-aware FLB job on Windows Server 2019 triggers a real VSS shadow copy")
def test_app_aware_vss_shadow_copy(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68955_app-aware-vss")

    build_flb_job(
        page, job_name, MACHINE, DRILL_TO_MIXEDTYPES[:-1], [DRILL_TO_MIXEDTYPES[-1]],
        app_aware_mode="Enabled (proceed on error)",
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"app-aware job did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_MIXEDTYPES)))
    assert names == MIXEDTYPES_FILES, f"expected the standard MixedTypes fileset, got {names}"


@allure.title("NJM-68955b — App-aware FLB job against an 800MB file, to give a real VSS shadow "
               "copy (if created) enough lifetime to be externally observable")
def test_vss_shadow_copy_lifecycle(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68955_vss-lifecycle")

    build_flb_job(
        page, job_name, MACHINE, DRILL_TO_BIGFILE_PARENT, ["VssShadowTest_ForFLB"],
        app_aware_mode="Enabled (proceed on error)",
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"app-aware job over the 800MB fixture did not succeed: {status}"

    names = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_BIGFILE_PARENT)))
    assert names == {"bigfile.bin"}, f"expected the 800MB fixture file, got {names}"
