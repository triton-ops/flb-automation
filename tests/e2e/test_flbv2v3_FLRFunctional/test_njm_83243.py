"""NJM-83243 — FLB - OS Support - Verify End-to-End Workflow on RHEL 8.

⚠ BLOCKED: no RHEL 8 source machine exists in this project's environment —
test-data/environment.md documents no such host. This is a fixture gap, not a coding
gap.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-83243")]

SKIP_REASON = (
    "BLOCKED: no RHEL 8 source machine exists in this project's environment — "
    "test-data/environment.md documents no such host. This is a fixture gap, not "
    "a coding gap. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_os_support_verify_end_to_end_workflow():
    pass
