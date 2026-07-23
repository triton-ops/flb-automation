"""NJM-85771 — FLB - Reliability - Verify Job State After Source Agent Service is Stopped Mid-Job.

⚠ BLOCKED: needs a genuine mid-job service disruption (stopping the source agent service)
triggered during an active job run — this project's UI-only Playwright automation can't
trigger this itself. It would need WinRM/SSH-coordinated fault injection against a live
job run, the same architectural gap already documented for suite M's Reliability TCs
(see test_flbv2v3_Reliability/test_njm_177969.py and its siblings).
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-85771")]

SKIP_REASON = (
    "BLOCKED: needs a genuine mid-job service disruption (stopping the source "
    "agent service) triggered during an active job run — this project's UI-only "
    "Playwright automation can't trigger this itself. It would need "
    "WinRM/SSH-coordinated fault injection against a live job run, the same "
    "architectural gap already documented for suite M's Reliability TCs (see "
    "test_flbv2v3_Reliability/test_njm_177969.py and its siblings). "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_reliability_verify_job_state_after_source_agent():
    pass
