"""NJM-70137 — Verify Backup Copy of Backups from All Supported Linux OS.

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182723") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

BackupCopyPage exists but has zero test coverage today. Needs live calibration of the
wizard's Source-step 'select FLB jobs/recovery points to copy' flow across this OS set.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupcopy, pytest.mark.jira("NJM-70137")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. BackupCopyPage exists but has "
    "zero test coverage today. Needs live calibration of the wizard's Source-step "
    "'select FLB jobs/recovery points to copy' flow across this OS set. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_verify_backup_copy_of_backups_from_all_supported_linux_os():
    pass
