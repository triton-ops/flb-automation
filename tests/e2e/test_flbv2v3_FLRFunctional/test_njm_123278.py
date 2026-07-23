"""NJM-123278 — [FLB v1] FLR from FLB - Functional - Verify Recovery to Various Supported File
Systems (NTFS, XFS, EXT4, etc.).

⚠ BLOCKED — two independent, real gaps, assessed 2026-07-23:

1. **No non-NTFS recovery DESTINATION fixture exists.** This TC's own point is that FLR recovery
   succeeds regardless of the destination filesystem type (NTFS/XFS/EXT4/etc.). This suite's only
   established, documented FLR recovery destination is win-fs3 (test-data/environment.md,
   `_helpers.py`'s own module docstring) — a Windows host serving CIFS/NFS exports, which is
   NTFS-backed. `test-data/environment.md` and `test-data/test-data.md` do document XFS/ext4
   *source* fixtures (`ubuntu22-xfs-vol` at `/mnt/xfs_testdata`, several ext4-root Linux sources —
   see NJM-68933/68934), but none of those hosts are configured as an FLR recovery *destination*
   (no NFS/CIFS export is set up on them for this purpose). Recovering TO an XFS/ext4-formatted
   target would need a new destination fixture this project doesn't have yet — the NTFS case is
   already covered by every other recover_to_share()-based test in this suite (e.g. NJM-70327/
   NJM-70328), so this TC would only add net-new coverage for the XFS/ext4 destination cases,
   which aren't buildable today.
2. **The TC's own precondition — a second, concurrent NBR backup job actively running during the
   FLR recovery — isn't something this suite's helpers currently orchestrate.** It's technically
   feasible in principle (NBR's backend runs jobs independently of what the Director UI happens to
   be displaying, so a fire-and-forget Run on an unrelated job, followed by driving a second job's
   FLR flow to completion in the same browser session, could simulate it without needing real
   parallel test execution/xdist) — but building and calibrating that two-job choreography live is
   a separate, non-trivial task of its own, not yet done.

Either gap alone would block this TC's full scope; both apply. Write and calibrate against a real
non-NTFS destination fixture (gap 1) before attempting the concurrent-job orchestration (gap 2) —
gap 1 is the more fundamental blocker of the TC's own stated point.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional, pytest.mark.jira("NJM-123278")]

SKIP_REASON = (
    "BLOCKED: (1) no XFS/ext4-formatted FLR recovery DESTINATION fixture exists in this "
    "environment — only the NTFS-backed win-fs3 CIFS/NFS export, already covered by every other "
    "recover_to_share() test in this suite; (2) this suite's helpers don't yet orchestrate a "
    "genuinely concurrent second backup job during an FLR recovery, the TC's own stated "
    "precondition. See this module's own docstring for the full assessment."
)


@pytest.mark.skip(reason=SKIP_REASON)
def test_recovery_to_various_supported_filesystems():
    pass
