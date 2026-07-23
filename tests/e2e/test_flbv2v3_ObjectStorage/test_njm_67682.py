r"""NJM-67682 — [FLB v1] Verify Backup to an Amazon EC2 Repository.

BLOCKED: no EC2-based repository configured on nbr-84 (older/duplicate TC of NJM-85746 — same
underlying gap). There is no partial fixture here at all — nothing for even a "written but
skipped" executable body to point at. Left as an explicit, individually-tracked skip (not
silently dropped) so the suite's TC coverage stays honestly reportable. Provisioning an EC2-based
repository is an environment/infrastructure decision outside this automation's scope; unskip
once one exists and is documented in environment.md.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage, pytest.mark.jira("NJM-67682")]


@pytest.mark.skip(reason="NJM-67682 BLOCKED — no EC2-based repository configured on nbr-84 (duplicate of NJM-85746).")
def test_backup_to_ec2_repository_duplicate():
    pass
