r"""NJM-70005 — [FLB v1] FLB - Alarms - Verify Alarm "ict45" (Root Folder Not Found).

TWO-PHASE COMBINATION TEST (same rationale as every other suite's — a live WinRM rename between
two pytest invocations can only be driven by the session's own agent, not pytest code):
  1. `pytest test_njm_70005.py::test_baseline_backup` — builds+runs a job whose ENTIRE source
     selection is the root-level folder `C:\AlarmTest45_ForFLB` itself (not a file within it).
     No cleanup call — job survives into phase 2.
  2. Agent renames `AlarmTest45_ForFLB` away via WinRM (e.g. to `AlarmTest45_ForFLB_RENAMED_AWAY`)
     so the job's configured root folder no longer exists at its path.
  3. `pytest test_njm_70005.py::test_rerun_shows_ict45_alarm` — reruns the SAME job (which must
     now fail — no such path exists to back up) and asserts the resulting Issues-panel alarm
     message names the missing folder. No alarm CODE ('ict45') is ever shown literally anywhere
     in the UI — only this human-readable message — so the assertion checks the message content,
     not an assumed code string (calibrated live 2026-07-21, see AlarmsPage's own docstring).

⚠ If phase 2 (the rename) is never applied, phase 3 will just pass as a normal successful rerun
and silently fail to exercise the alarm at all — check the source folder's real name if this TC
needs re-running from scratch.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, read_job_alarm_text, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.jira("NJM-70005")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-70005_root-not-found"


@allure.title("NJM-70005 phase 1/2 — baseline backup with AlarmTest45_ForFLB as the job's root")
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(page, JOB_NAME, MACHINE, ["Local Disk (C:)"], ["AlarmTest45_ForFLB"])
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"


@allure.title("NJM-70005 phase 2/2 — rerun after the root folder is renamed away shows the "
               "Root-Folder-Not-Found alarm")
@pytest.mark.flaky(reruns=0)
def test_rerun_shows_ict45_alarm(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=180_000)
    assert status == "Failed", (
        f"expected the rerun to fail (its root folder was renamed away), got: {status}"
    )

    alarm_text = read_job_alarm_text(page, JOB_NAME)
    assert "AlarmTest45_ForFLB" in alarm_text, (
        f"expected the Issues panel to name the missing AlarmTest45_ForFLB folder, "
        f"got panel text: {alarm_text!r}"
    )
    assert "cannot be found" in alarm_text, (
        f"expected the alarm's own 'cannot be found' wording, got: {alarm_text!r}"
    )

    flb_job_cleanup(JOB_NAME)
