r"""NJM-68976 — [FLB v2] FLB - Functional - Verify Behavior with Filesystem-Encrypted Items
(Expected to Skip).

Per the TC's Xray steps: back up a folder holding an EFS-encrypted file (secret.docx) alongside an
ordinary file (plain.txt); the encrypted file is expected to be SKIPPED (the FLB agent's service
account can't decrypt another user's EFS key), while the ordinary file backs up; the recovery point
should contain the ordinary file but NOT the encrypted one.

BLOCKED — fixture cannot be provisioned by this automation. Verified live 2026-07-18: creating a
genuine EFS-encrypted file requires `cipher /E`, which needs the interactive user's EFS key loaded
in the logon session. Over the WinRM network logon this automation uses, `cipher /E` returns
"Access is denied." and the file's Encrypted attribute stays clear — so no real EFS fixture can be
seeded remotely. Backing up a merely *named* "secret.docx" would not exercise the product's
skip-EFS logic (which keys off the real Encrypted attribute / unreadable cipher stream, not the
name), so a name-only fixture would produce a misleading green. This TC needs an interactive
session on the Windows host to seed a real EFS file; it is left written-but-skipped rather than
faked.

The body below is the intended executable flow (build → run → browse RP → assert the encrypted
file is absent and the ordinary file present) and will run as soon as a real EFSTest_ForFLB fixture
(C:\EFSTest_ForFLB\{secret.docx EFS-encrypted, plain.txt ordinary}) exists on Window11.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-68976"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@pytest.mark.skip(
    reason="BLOCKED: a real EFS-encrypted fixture can't be provisioned over WinRM (cipher /E needs "
    "an interactive session; returns Access denied). Written and executable; unskip once the host "
    "has a real C:\\EFSTest_ForFLB seeded interactively."
)
@allure.title("NJM-68976 — EFS-encrypted items are skipped; ordinary files back up (Windows)")
def test_efs_encrypted_items_skipped(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68976")
    build_flb_job(page, job_name, MACHINE, ["Local Disk (C:)"], ["EFSTest_ForFLB"])
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    names = extract_item_names(flr_browse(page, job_name, ["C:", "EFSTest_ForFLB"]))
    assert "plain.txt" in names, f"ordinary file missing from recovery point: {names}"
    assert "secret.docx" not in names, f"EFS-encrypted file was NOT skipped — present in RP: {names}"
