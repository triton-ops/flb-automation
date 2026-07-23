"""NJM-70132 — BCJ for FLB - Options Step - Verify All Job Options are Functional.

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182723") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

BackupCopyPage exists but has zero test coverage today. Needs live calibration of the
Options step's full control set for a Backup Copy job.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupcopy, pytest.mark.jira("NJM-70132")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. BackupCopyPage exists but has "
    "zero test coverage today. Needs live calibration of the Options step's full "
    "control set for a Backup Copy job. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_bcj_for_flb_options_step_verify_all_job():
    pass
