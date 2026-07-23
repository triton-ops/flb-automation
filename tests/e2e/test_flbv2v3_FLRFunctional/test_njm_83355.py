"""NJM-83355 — FLR from FLB - Functional - Verify Recovery from an Amazon EC2 Repository.

⚠ BLOCKED: no Amazon EC2-based repository exists in this project's environment —
test-data/environment.md's FLB target repositories table has no such entry. This is a
hardware/service-dependent capability this project's environment doesn't have, not a
coding gap.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-83355")]

SKIP_REASON = (
    "BLOCKED: no Amazon EC2-based repository exists in this project's environment "
    "— test-data/environment.md's FLB target repositories table has no such "
    "entry. This is a hardware/service-dependent capability this project's "
    "environment doesn't have, not a coding gap. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_recovery_from_an_ec2_repo():
    pass
