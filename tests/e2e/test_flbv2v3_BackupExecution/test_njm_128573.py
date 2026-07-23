"""NJM-128573 — FLB - Platform - Verify End-to-End Workflow on QNAP (x86_64) NAS.

⚠ BLOCKED: no QNAP (x86_64) NAS device exists in this project's environment —
test-data/environment.md documents only the nbr-84 (FLB) / nbr-5 (FSB) lab appliances
and their discovered source machines, no NAS hardware of this kind. This is a
hardware-dependent capability this project's environment doesn't have, not a coding gap.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-128573")]

SKIP_REASON = (
    "BLOCKED: no QNAP (x86_64) NAS device exists in this project's environment — "
    "test-data/environment.md documents only the nbr-84 (FLB) / nbr-5 (FSB) lab "
    "appliances and their discovered source machines, no NAS hardware of this "
    "kind. This is a hardware-dependent capability this project's environment "
    "doesn't have, not a coding gap. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_platform_verify_end_to_end_workflow_on_qnap_x86_64():
    pass
