r"""NJM-85746 — [FLB v1] Verify Backup to Amazon EC2 Repository.

BLOCKED: no EC2-based repository configured on nbr-84. Per test-data/environment.md's "FLB target
repositories (nbr-84)" table, there is no partial fixture here at all — no repo of this type is
configured, so there is nothing for even a "written but skipped" executable body to point at.
Left as an explicit, individually-tracked skip (not silently dropped) so the suite's TC coverage
stays honestly reportable. Provisioning an EC2-based repository is an environment/infrastructure
decision outside this automation's scope; unskip once one exists and is documented in
environment.md.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-85746")]


@pytest.mark.skip(reason="NJM-85746 BLOCKED — no EC2-based repository configured on nbr-84.")
def test_backup_to_ec2_repository():
    pass
