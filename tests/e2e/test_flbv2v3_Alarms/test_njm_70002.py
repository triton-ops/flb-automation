r"""NJM-70002 — [FLB v1] FLB - Alarms - Verify Alarm "ict1" (No Source Items Found).

TWO-PHASE COMBINATION TEST — same rationale as NJM-70005 in this suite. The distinction from
ict45 (whose job's ENTIRE source is the missing root folder itself): here the job selects a
SPECIFIC FILE (`subitem.txt`) inside a folder that keeps existing (`keep_parent_alive.txt` stays
in place) — the job's root/parent is fine, only the selected item itself is gone.
  1. `test_baseline_backup` — builds+runs a job selecting `C:\AlarmTest1_ForFLB\subitem.txt`
     specifically (not the whole folder). No cleanup call.
  2. Agent deletes `subitem.txt` via WinRM, leaving `AlarmTest1_ForFLB` itself (and
     `keep_parent_alive.txt`) in place.
  3. `test_rerun_shows_ict1_alarm` — reruns the SAME job (must fail — its one selected item no
     longer exists) and asserts the Issues-panel alarm names the missing item.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, read_job_alarm_text, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.jira("NJM-70002")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-70002_no-items-found"


@allure.title("NJM-70002 phase 1/2 — baseline backup selecting AlarmTest1_ForFLB\\subitem.txt")
def test_baseline_backup(logged_in_page):
    page = logged_in_page
    build_flb_job(
        page, JOB_NAME, MACHINE, ["Local Disk (C:)", "AlarmTest1_ForFLB"], ["subitem.txt"],
    )
    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=300_000)
    assert status == "Successful", f"baseline backup did not succeed: {status}"


@allure.title("NJM-70002 phase 2/2 — rerun after the selected item is deleted shows the "
               "No-Source-Items-Found alarm")
@pytest.mark.flaky(reruns=0)
def test_rerun_shows_ict1_alarm(logged_in_page, flb_job_cleanup):
    page = logged_in_page

    status = run_and_wait_flb_job(page, JOB_NAME, timeout_ms=180_000)
    assert status == "Failed", (
        f"expected the rerun to fail (its only selected item was deleted), got: {status}"
    )

    alarm_text = read_job_alarm_text(page, JOB_NAME)
    assert "subitem.txt" in alarm_text or "AlarmTest1_ForFLB" in alarm_text, (
        f"expected the Issues panel to name the missing item/path, got panel text: {alarm_text!r}"
    )

    flb_job_cleanup(JOB_NAME)
