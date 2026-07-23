"""NJM-70121 — BCJ to Tape - Verify Tape is a Supported Destination.

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182723") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

No tape hardware/POM support exists in this project at all — no tape library, VTL, or
standalone tape drive is documented in test-data/environment.md, and there is no
tape-specific Page Object anywhere under browser/pom/. This is a hardware-dependent
capability this project's current environment doesn't have, not a coding gap.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupcopy, pytest.mark.jira("NJM-70121")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. No tape hardware/POM support "
    "exists in this project at all — no tape library, VTL, or standalone tape "
    "drive is documented in test-data/environment.md, and there is no "
    "tape-specific Page Object anywhere under browser/pom/. This is a "
    "hardware-dependent capability this project's current environment doesn't "
    "have, not a coding gap. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_bcj_to_tape_verify_tape_is_a_supported():
    pass
