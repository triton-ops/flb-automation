"""NJM-177994 — FLB/NAS Share: 48-96h memory-leak & resource-usage soak test (Feature branch / PL).

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182805") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

This TC is a genuine 48-96 hour long-running soak test — architecturally incompatible
with this project's per-TC pytest execution model (a single test run is expected to
complete in minutes, not days) and would need a dedicated, separately-scheduled
long-running harness, not a pytest test function.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.reliability, pytest.mark.jira("NJM-177994")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. This TC is a genuine 48-96 hour "
    "long-running soak test — architecturally incompatible with this project's "
    "per-TC pytest execution model (a single test run is expected to complete in "
    "minutes, not days) and would need a dedicated, separately-scheduled "
    "long-running harness, not a pytest test function. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_nas_share_48_96h_memory_leak_resource():
    pass
