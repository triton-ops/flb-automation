"""NJM-87527 — FLB - Job Management - Verify Settings Integrity After Merging Backup/Backup Copy Jobs.

⚠ Not yet run: needs a real Backup Copy job to merge with — test_flbv2v3_BackupCopy/ has
zero implemented/calibrated tests yet (all 43 TCs there are newly ported and skip-marked
pending live calibration). This TC can't be exercised until at least one real Backup
Copy job exists to merge against.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-87527")]

SKIP_REASON = (
    "Not yet run: needs a real Backup Copy job to merge with — "
    "test_flbv2v3_BackupCopy/ has zero implemented/calibrated tests yet (all 43 "
    "TCs there are newly ported and skip-marked pending live calibration). This "
    "TC can't be exercised until at least one real Backup Copy job exists to "
    "merge against. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_job_management_verify_settings_integrity_after_merging():
    pass
