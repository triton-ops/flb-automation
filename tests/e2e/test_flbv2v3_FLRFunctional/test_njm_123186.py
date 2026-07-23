"""NJM-123186 — FLR from FLB - Functional - Verify Recovery from an Immutable Cloudian S3 Backup.

⚠ Not yet run: buildable today — Cloudian-immutable already exists and is reachable
(test-data/environment.md), and this suite's existing recover_to_share()/build_flb_job()
helpers already support it. Just not implemented yet.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-123186")]

SKIP_REASON = (
    "Not yet run: buildable today — Cloudian-immutable already exists and is "
    "reachable (test-data/environment.md), and this suite's existing "
    "recover_to_share()/build_flb_job() helpers already support it. Just not "
    "implemented yet. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_recovery_from_an_cloudian_s3_immutable():
    pass
