"""NJM-123185 — FLR from FLB - Functional - Verify Recovery from an Immutable Ceph S3 Backup.

⚠ Not yet run: buildable today — Ceph_S3 itself was removed (test-data/environment.md),
but that same doc explicitly names Cloudian-immutable as the documented substitute for
any Ceph_S3-immutable TC, this one included by name. Just not implemented yet.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-123185")]

SKIP_REASON = (
    "Not yet run: buildable today — Ceph_S3 itself was removed "
    "(test-data/environment.md), but that same doc explicitly names "
    "Cloudian-immutable as the documented substitute for any Ceph_S3-immutable "
    "TC, this one included by name. Just not implemented yet. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_recovery_from_an_ceph_s3_immutable():
    pass
