"""NJM-70326 — FLR from FLB - Functional - Verify 'Forward via Email' Recovery Option.

⚠ BLOCKED: no SMTP/email server is configured anywhere in this project's environment —
test-data/environment.md documents no mail relay, and this recovery option needs one to
verify delivery. Fixture gap, not a coding gap.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70326")]

SKIP_REASON = (
    "BLOCKED: no SMTP/email server is configured anywhere in this project's "
    "environment — test-data/environment.md documents no mail relay, and this "
    "recovery option needs one to verify delivery. Fixture gap, not a coding gap. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_forward_via_email():
    pass
