"""NJM-123191 — FLR from FLB - Functional - Verify Recovery from an Immutable HPE StoreOnce Backup.

⚠ Not yet run: HPE_Repo exists and is reachable (test-data/environment.md), but its
immutability capability has never been confirmed live — needs investigation (does
setting 'Immutable for N days' on a job targeting HPE_Repo actually produce an
'Immutable until' marker, the same way it was proven for Local-Immutable in
test_flbv2v3_ObjectStorage/test_njm_123133.py?) before this TC can be written for real.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-123191")]

SKIP_REASON = (
    "Not yet run: HPE_Repo exists and is reachable (test-data/environment.md), "
    "but its immutability capability has never been confirmed live — needs "
    "investigation (does setting 'Immutable for N days' on a job targeting "
    "HPE_Repo actually produce an 'Immutable until' marker, the same way it was "
    "proven for Local-Immutable in "
    "test_flbv2v3_ObjectStorage/test_njm_123133.py?) before this TC can be "
    "written for real. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_recovery_from_an_hpe_storeonce_immutable():
    pass
