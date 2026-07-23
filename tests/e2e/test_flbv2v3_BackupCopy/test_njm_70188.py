"""NJM-70188 — Verify Job Behavior After Deleting Source Recovery Points.

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182723") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

BackupCopyPage exists but has zero test coverage today. Needs live calibration plus a
two-phase test design (build the BCJ, delete a source recovery point via Manage, verify
BCJ behavior) similar to this project's other two-phase tests — see
test_flbv2v3_BackupExecution/test_njm_128608.py's module docstring for the established
pattern.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupcopy, pytest.mark.jira("NJM-70188")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. BackupCopyPage exists but has "
    "zero test coverage today. Needs live calibration plus a two-phase test "
    "design (build the BCJ, delete a source recovery point via Manage, verify BCJ "
    "behavior) similar to this project's other two-phase tests — see "
    "test_flbv2v3_BackupExecution/test_njm_128608.py's module docstring for the "
    "established pattern. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_verify_job_behavior_after_deleting_source_recovery_points():
    pass
