"""NJM-70107 — BCJ for FLB - Source Step - Verify Selection of FLB Jobs and RPs.

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182723") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

BackupCopyPage exists but has zero test coverage today. Needs live calibration of the
Source step's FLB-job/recovery-point selection UI for a Backup Copy job.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupcopy, pytest.mark.jira("NJM-70107")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. BackupCopyPage exists but has "
    "zero test coverage today. Needs live calibration of the Source step's "
    "FLB-job/recovery-point selection UI for a Backup Copy job. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_bcj_for_flb_source_step_verify_selection_of():
    pass
