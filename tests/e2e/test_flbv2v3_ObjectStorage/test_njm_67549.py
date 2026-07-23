r"""NJM-67549 — [FLB v1] FLB Job Wizard - Destination Step - Verify Amazon EC2 Repository is a
Supported Target.

BLOCKED: no EC2-based repository configured on nbr-84 to select as a destination target. There is
no partial fixture here at all — nothing for even a "written but skipped" executable body to
point at. Left as an explicit, individually-tracked skip (not silently dropped) so the suite's TC
coverage stays honestly reportable. Provisioning an EC2-based repository is an environment/
infrastructure decision outside this automation's scope; unskip once one exists and is documented
in environment.md.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-67549")]


@pytest.mark.skip(reason="NJM-67549 BLOCKED — no EC2-based repository configured on nbr-84 to select as a target.")
def test_ec2_is_supported_target():
    pass
