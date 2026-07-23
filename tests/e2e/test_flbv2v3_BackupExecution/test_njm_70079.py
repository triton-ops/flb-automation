"""NJM-70079 — FLB - Scheduling (Migration) - Verify Automatic Update of Legacy Job to New Schedule/Retention.

⚠ BLOCKED: needs a real product version upgrade of the shared nbr-84 appliance mid-test —
irreversible, appliance-wide, affects every other suite for the rest of the session.
Same gap already documented in test_flbv2v3_FLRToSource/test_njm_185031.py.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-70079")]

SKIP_REASON = (
    "BLOCKED: needs a real product version upgrade of the shared nbr-84 appliance "
    "mid-test — irreversible, appliance-wide, affects every other suite for the "
    "rest of the session. Same gap already documented in "
    "test_flbv2v3_FLRToSource/test_njm_185031.py. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_scheduling_migration_verify_automatic_update_of_legacy():
    pass
