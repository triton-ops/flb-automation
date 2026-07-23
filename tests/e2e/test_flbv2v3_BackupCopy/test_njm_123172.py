"""NJM-123172 — Verify Copy to Immutable Amazon S3 Repository.

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182723") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

BackupCopyPage exists (browser/pom/backup_types/backup_copy_page.py) but has zero test
coverage today. Needs live calibration of the Backup Copy wizard's Destination-step repo
picker (and retention options, where relevant) for this specific repository/scenario
before implementing.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupcopy, pytest.mark.jira("NJM-123172")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. BackupCopyPage exists "
    "(browser/pom/backup_types/backup_copy_page.py) but has zero test coverage "
    "today. Needs live calibration of the Backup Copy wizard's Destination-step "
    "repo picker (and retention options, where relevant) for this specific "
    "repository/scenario before implementing. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_verify_copy_to_immutable_amazon_s3_repository():
    pass
