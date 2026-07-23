"""NJM-70376 — FLR from FLB - Functional - Verify Recovery from an Immutable Backup.

⚠ Not yet run: buildable today, reusing Local-Immutable (test-data/environment.md) the
same way test_flbv2v3_ObjectStorage/test_njm_123133.py already proved a genuinely
immutable savepoint on this repo — this TC is the older, repository-agnostic precursor
to the per-repository NJM-123176..123192 set; not yet given its own implementation.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-70376")]

SKIP_REASON = (
    "Not yet run: buildable today, reusing Local-Immutable "
    "(test-data/environment.md) the same way "
    "test_flbv2v3_ObjectStorage/test_njm_123133.py already proved a genuinely "
    "immutable savepoint on this repo — this TC is the older, repository-agnostic "
    "precursor to the per-repository NJM-123176..123192 set; not yet given its "
    "own implementation. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_recovery_from_an_generic_immutable():
    pass
