r"""NJM-123129 / 123130 / 85746 / 85749 / 67682 / 67549 — BLOCKED: no fixture exists on nbr-84 for
any of these TCs' required repository/transporter type.

Per test-data/environment.md's "FLB target repositories (nbr-84)" table and the Transporters
section: nbr-84 has NO Synology C2 Object Storage repository (NJM-123129/123130 need one, with
and without immutability) and NO Amazon EC2-based repository or transporter (NJM-85746, 85749,
67682, 67549 all need one). Unlike suite A's documented gaps (which had a real fixture with one
missing detail), there is no partial fixture here at all — no repo/transporter of either type is
configured, so there is nothing for even a "written but skipped" executable body to point at.

These are left as explicit, individually-tracked skips (not silently dropped) so the suite's TC
coverage stays honestly reportable — each references the real, live-checked absence rather than a
fabricated repo name. Provisioning a Synology C2 account or an EC2-based transporter/repository is
an environment/infrastructure decision outside this automation's scope; unskip once either exists
and is documented in environment.md.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage]

BLOCKED_NO_FIXTURE = [
    pytest.param(
        "NJM-123129", "Verify Backup to Synology C2 Object Storage (Windows & Linux Sources)",
        "no Synology C2 repository configured on nbr-84",
        marks=pytest.mark.jira("NJM-123129"), id="NJM-123129-synology-c2",
    ),
    pytest.param(
        "NJM-123130", "Verify Backup to Immutable Synology C2 Object Storage (Windows & Linux Sources)",
        "no Synology C2 repository configured on nbr-84",
        marks=pytest.mark.jira("NJM-123130"), id="NJM-123130-synology-c2-immutable",
    ),
    pytest.param(
        "NJM-85746", "Verify Backup to Amazon EC2 Repository",
        "no EC2-based repository configured on nbr-84",
        marks=pytest.mark.jira("NJM-85746"), id="NJM-85746-ec2-repo",
    ),
    pytest.param(
        "NJM-85749", "Verify Backup Using an Amazon EC2-based Transporter",
        "no EC2-based transporter configured on nbr-84 (only Onboard transporter + Linux_Tranporter_15.62 exist)",
        marks=pytest.mark.jira("NJM-85749"), id="NJM-85749-ec2-transporter",
    ),
    pytest.param(
        "NJM-67682", "Verify Backup to an Amazon EC2 Repository",
        "no EC2-based repository configured on nbr-84 (older/duplicate TC of NJM-85746)",
        marks=pytest.mark.jira("NJM-67682"), id="NJM-67682-ec2-repo",
    ),
    pytest.param(
        "NJM-67549", "FLB Job Wizard - Destination Step - Verify Amazon EC2 Repository is a Supported Target",
        "no EC2-based repository configured on nbr-84 to select as a destination target",
        marks=pytest.mark.jira("NJM-67549"), id="NJM-67549-ec2-supported-target",
    ),
]


@pytest.mark.parametrize("jira_id,summary,reason", BLOCKED_NO_FIXTURE)
def test_blocked_missing_repository_fixture(jira_id, summary, reason):
    pytest.skip(f"{jira_id} BLOCKED — {summary}: {reason}.")
