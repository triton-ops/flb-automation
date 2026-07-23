"""NJM-69179 — FLB - Dashboard - Verify Content and Accuracy of 'Job Contents' Widget.

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182727") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

No Dashboard-widget Page Object exists yet under browser/pom/ — the 'Job Contents'
widget's locators, layout, and data-accuracy checks all need live calibration from
scratch before this TC can be implemented.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.dashboard, pytest.mark.jira("NJM-69179")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. No Dashboard-widget Page Object "
    "exists yet under browser/pom/ — the 'Job Contents' widget's locators, "
    "layout, and data-accuracy checks all need live calibration from scratch "
    "before this TC can be implemented. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_dashboard_verify_content_and_accuracy_of_job():
    pass
