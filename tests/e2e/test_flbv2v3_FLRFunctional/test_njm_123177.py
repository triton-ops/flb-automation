"""NJM-123177 — FLR from FLB - Functional - Verify Recovery from an Immutable S3 Backup Copy.

⚠ Not yet run: needs a real Backup Copy job on an immutable Amazon S3 repository to
recover from — test_flbv2v3_BackupCopy/ has zero implemented/calibrated tests yet (all
43 TCs there are newly ported and skip-marked pending live calibration). Can't be
exercised until at least one real Backup Copy job exists on this repository.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-123177")]

SKIP_REASON = (
    "Not yet run: needs a real Backup Copy job on an immutable Amazon S3 "
    "repository to recover from — test_flbv2v3_BackupCopy/ has zero "
    "implemented/calibrated tests yet (all 43 TCs there are newly ported and "
    "skip-marked pending live calibration). Can't be exercised until at least one "
    "real Backup Copy job exists on this repository. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_recovery_from_an_s3_backup_copy_immutable():
    pass
