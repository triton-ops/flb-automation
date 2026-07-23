"""NJM-105298 — FLR from FLB - Functional - Verify Recovery from Dell EMC Data Domain Repository.

⚠ BLOCKED: no Dell EMC Data Domain repository exists in this project's environment —
test-data/environment.md's FLB target repositories table has no such entry. This is a
hardware/service-dependent capability this project's environment doesn't have, not a
coding gap.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-105298")]

SKIP_REASON = (
    "BLOCKED: no Dell EMC Data Domain repository exists in this project's "
    "environment — test-data/environment.md's FLB target repositories table has "
    "no such entry. This is a hardware/service-dependent capability this "
    "project's environment doesn't have, not a coding gap. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_recovery_from_dell():
    pass
