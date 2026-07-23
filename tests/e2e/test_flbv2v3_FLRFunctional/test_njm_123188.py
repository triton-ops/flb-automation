"""NJM-123188 — FLR from FLB - Functional - Verify Recovery from an Immutable Seagate Lyve Cloud Backup.

⚠ BLOCKED: no Seagate Lyve Cloud repository exists in this project's environment —
test-data/environment.md's FLB target repositories table has no such entry. This is a
hardware/service-dependent capability this project's environment doesn't have, not a
coding gap.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-123188")]

SKIP_REASON = (
    "BLOCKED: no Seagate Lyve Cloud repository exists in this project's "
    "environment — test-data/environment.md's FLB target repositories table has "
    "no such entry. This is a hardware/service-dependent capability this "
    "project's environment doesn't have, not a coding gap. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_recovery_from_an_seagate_lyve_immutable():
    pass
