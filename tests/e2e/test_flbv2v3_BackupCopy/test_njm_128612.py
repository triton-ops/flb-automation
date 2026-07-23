"""NJM-128612 — Verify Synthetic Full Creation (With Source Changes).

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182723") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

BackupCopyPage exists but has zero test coverage today. Mirrors the already-solved FLB
retention TCs (see test_flbv2v3_BackupExecution/test_njm_128607.py and siblings) but for
a Backup Copy Job specifically — needs live calibration of BCJ's own
Full-Backup-Settings-equivalent controls.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupcopy, pytest.mark.jira("NJM-128612")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. BackupCopyPage exists but has "
    "zero test coverage today. Mirrors the already-solved FLB retention TCs (see "
    "test_flbv2v3_BackupExecution/test_njm_128607.py and siblings) but for a "
    "Backup Copy Job specifically — needs live calibration of BCJ's own "
    "Full-Backup-Settings-equivalent controls. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_verify_synthetic_full_creation_with_source_changes():
    pass
