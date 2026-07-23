"""NJM-123510 — FLR from FLB - Functional - Verify Recovery from an Encrypted Backup.

⚠ Not yet run: buildable today — the encryption-password dialog gap this TC's own summary
names (set_encryption_password() failing to configure a password, leaving Finish
unsubmittable) was root-caused and fixed 2026-07-22/23 (see
FlbWizardPage.set_encryption_password() and _dismiss_kms_warning_if_present(), and
test_flbv2v3_ObjectStorage/test_njm_123509.py's own confirmed pass). This TC itself —
recovering FROM an encrypted backup via FLR, not just building one — hasn't been written
yet.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-123510")]

SKIP_REASON = (
    "Not yet run: buildable today — the encryption-password dialog gap this TC's "
    "own summary names (set_encryption_password() failing to configure a "
    "password, leaving Finish unsubmittable) was root-caused and fixed "
    "2026-07-22/23 (see FlbWizardPage.set_encryption_password() and "
    "_dismiss_kms_warning_if_present(), and "
    "test_flbv2v3_ObjectStorage/test_njm_123509.py's own confirmed pass). This TC "
    "itself — recovering FROM an encrypted backup via FLR, not just building one "
    "— hasn't been written yet. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flr_from_flb_functional_verify_recovery_from_an_encrypted_backup():
    pass
