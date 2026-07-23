r"""NJM-85749 — [FLB v1] Verify Backup Using an Amazon EC2-based Transporter.

BLOCKED: no EC2-based transporter configured on nbr-84 (only Onboard transporter and
Linux_Tranporter_15.62 exist — see test-data/environment.md's Transporters section). There is no
partial fixture here at all — nothing for even a "written but skipped" executable body to point
at. Left as an explicit, individually-tracked skip (not silently dropped) so the suite's TC
coverage stays honestly reportable. Provisioning an EC2-based transporter is an environment/
infrastructure decision outside this automation's scope; unskip once one exists and is documented
in environment.md.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-85749")]


@pytest.mark.skip(reason="NJM-85749 BLOCKED — no EC2-based transporter configured on nbr-84.")
def test_backup_using_ec2_transporter():
    pass
