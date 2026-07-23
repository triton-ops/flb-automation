"""NJM-83354 — FLR from FLB - Functional - Verify Recovery from a CIFS Share Repository.

⚠ BLOCKED: CIFS_REPO (test-data/environment.md, id 3) is documented INACCESSIBLE — do not
use. No other CIFS-Share-type repository exists on nbr-84.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-83354")]

SKIP_REASON = (
    "BLOCKED: CIFS_REPO (test-data/environment.md, id 3) is documented "
    "INACCESSIBLE — do not use. No other CIFS-Share-type repository exists on "
    "nbr-84. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_recovery_from_a():
    pass
