"""NJM-68980 — [FLB v2] FLB - Functional - Verify Handling of Symbolic and Hard Links (Linux).

Per the TC's Xray steps: on a Linux source create a folder with a symbolic link (→ target file)
and a pair of hard-linked files (same inode), back it up, observe from the job log / FLR wizard how
symlinks and hard links are handled, recover the link-type items, and confirm the recovered items
reflect the documented behavior with no corruption/missing files.

This is a BEHAVIOR-OBSERVATION TC (its Expected Results say "the job log clearly indicates the
behavior ... backed up as-is, skipped, or resolved") — there is no single fixed pass/fail for
whether symlinks are followed vs. stored as links, only that the behavior is consistent and
lossless. pytest therefore asserts the job reached Successful and the FLR recovery started; the
actual observed handling (does the symlink come back as a link or as a resolved copy? are the two
hard links deduplicated to one inode or restored as two files?) is inspected by the agent on the
NFS destination and reported alongside.

FIXTURE (seeded 2026-07-18, registered in test-data/test-data.md §7): /LinkTest_ForFLB/links/ on
flb-linux — target.txt, link_to_target.txt (symlink → target.txt), file_a + file_b (hard-linked,
one shared inode). Recovers to the NFS export (the POSIX-appropriate share, like NJM-70359).

SCOPE NOTE: pytest asserts job Successful + FLR recovery-started; the link-handling verdict is the
agent-driven destination check, reported alongside — not a pytest assertion.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-68980"),
    pytest.mark.xdist_group(name="Linux_16.84"),
]

MACHINE = "Linux_16.84"


@allure.title("NJM-68980 — handling of symbolic & hard links on backup/recovery (Linux, recover to NFS)")
def test_symbolic_and_hard_links(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68980")
    build_flb_job(page, job_name, MACHINE, ["LinkTest_ForFLB"], ["links"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"
    started = recover_to_share(page, job_name, ["root", "LinkTest_ForFLB"], ["links"], "nfs")
    assert started, "the FLR wizard did not confirm the recovery started"
