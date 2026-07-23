"""NJM-177964 — Partial-failure job success when some items are skipped.

⚠ NOT YET RUN — this suite was newly ported 2026-07-23 via Jira's own
testExecutionTests("NJM-182805") JQL query (fetches every TC actually linked to this
Xray Test Execution, rather than guessing from the summary text alone). This TC is
tracked here with its real Jira summary and jira marker, but is not yet implemented
against the live appliance.

This TC needs a genuine mid-job fault injection (killing a transporter connection,
renaming/deleting a folder while a job is actively reading it, filling a repository to
capacity) that this project's UI-only Playwright automation cannot trigger by itself —
it would need coordinated WinRM/SSH scripting against the source/repository host timed
against a live job run, which is a substantially different test architecture from every
other suite in this project (build via UI -> run -> verify via UI).
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.reliability, pytest.mark.jira("NJM-177964")]

SKIP_REASON = (
    "Not yet run — suite newly ported 2026-07-23. This TC needs a genuine mid-job "
    "fault injection (killing a transporter connection, renaming/deleting a "
    "folder while a job is actively reading it, filling a repository to capacity) "
    "that this project's UI-only Playwright automation cannot trigger by itself — "
    "it would need coordinated WinRM/SSH scripting against the source/repository "
    "host timed against a live job run, which is a substantially different test "
    "architecture from every other suite in this project (build via UI -> run -> "
    "verify via UI). "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_partial_failure_job_success_when_some_items_are():
    pass
