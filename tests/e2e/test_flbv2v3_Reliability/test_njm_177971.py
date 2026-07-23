"""NJM-177971 — Symbolic links among selected folders/volumes are skipped.

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182805") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

This TC describes an FLB behavior (skip semantics, fallback behavior, immutability
enforcement) that doesn't yet have a POM/fixture path calibrated for exercising it live
— needs its own live-calibration pass before implementing.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.reliability, pytest.mark.jira("NJM-177971")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. This TC describes an FLB "
    "behavior (skip semantics, fallback behavior, immutability enforcement) that "
    "doesn't yet have a POM/fixture path calibrated for exercising it live — "
    "needs its own live-calibration pass before implementing. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_symbolic_links_among_selected_folders_volumes_are_skipped():
    pass
