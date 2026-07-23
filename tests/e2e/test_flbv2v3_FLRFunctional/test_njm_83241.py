"""NJM-83241 — FLB - OS Support - Verify End-to-End Workflow on Ubuntu 22.04 LTS.

⚠ BLOCKED: no non-Desktop Ubuntu 22.04 LTS source machine exists — only the Desktop
variant (ubuntu22-desktop-src, test-data/environment.md, already covered by NJM-83255)
is discovered. This TC wants the server/non-Desktop edition specifically.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-83241")]

SKIP_REASON = (
    "BLOCKED: no non-Desktop Ubuntu 22.04 LTS source machine exists — only the "
    "Desktop variant (ubuntu22-desktop-src, test-data/environment.md, already "
    "covered by NJM-83255) is discovered. This TC wants the server/non-Desktop "
    "edition specifically. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_os_support_verify_end_to_end_workflow_ubuntu_2204_lts():
    pass
