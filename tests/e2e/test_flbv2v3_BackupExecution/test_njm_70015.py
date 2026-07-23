"""NJM-70015 — FLB - Functional - Verify User Story: Recover Files/Folders from Backup (US3).

⚠ Out of scope for this suite: recovering to the ORIGINAL location is an
execute-not-just-browse action gated by this project's safety rules (see CLAUDE.md and
suite F's own NJM-182724) — suite F (test_flbv2v3_FLRToSource/) already owns this exact
scenario under explicit per-session authorization. Not duplicated here; see
test_njm_70018.py's own docstring for this same reasoning.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution, pytest.mark.jira("NJM-70015")]

SKIP_REASON = (
    "Out of scope for this suite: recovering to the ORIGINAL location is an "
    "execute-not-just-browse action gated by this project's safety rules (see "
    "CLAUDE.md and suite F's own NJM-182724) — suite F "
    "(test_flbv2v3_FLRToSource/) already owns this exact scenario under explicit "
    "per-session authorization. Not duplicated here; see test_njm_70018.py's own "
    "docstring for this same reasoning. "
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_flb_functional_verify_user_story_recover_files_folders():
    pass
