r"""NJM-85758 — [FLB v1] FLB - Reporting - Verify FLB Jobs are Included in NBR Usage Data.

BLOCKED — Product/Environment: no "Usage Data" / "Send Usage Data" feature exists anywhere in
this NBR 11.2.1 (build 106315) Director UI. Confirmed live 2026-07-21 by logging in and reading
the full text of every Settings page that could plausibly host it — Licensing, Notifications &
Reports, General — none contain the word "usage" at all (checked case-insensitively). The
Settings left-nav's full item list is: General, Email Settings, Notifications & Reports, Users &
Roles, Self-Backup, Database Options, System Settings, Bandwidth Throttling, Branding, Events,
Software Update, MSP, Licensing, Inventory, Nodes, Repositories, Tape — no "Usage Data" entry.

This isn't a POM gap (nothing to calibrate against — there is no such page), and it isn't
something buildable within the AUTO_FLB_* safety fence (there's no UI surface to interact with at
all). If this feature exists under a different name/location in a later build, re-check before
assuming it's permanently absent.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-85758")]


@pytest.mark.skip(
    reason="BLOCKED (Product/Environment): no 'Usage Data'/'Send Usage Data' feature exists "
    "anywhere in this NBR 11.2.1 build's Director UI — confirmed live by reading the full text "
    "of Licensing, Notifications & Reports, and General settings pages (none mention 'usage'). "
    "See module docstring."
)
def test_flb_jobs_in_usage_data():
    pass
