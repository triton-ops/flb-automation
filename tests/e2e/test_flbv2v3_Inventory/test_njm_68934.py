"""NJM-68934 — [FLB v1] FLB - Functional (Linux) - Verify Backup of XFS File System.
Original verdict (raw-RPC execution): PASS (built via the UI wizard — see NJM-67702's note; also
already covered by browser/checks/build_flb_jobs_linux_batch.py's build-only batch script).

Verify FLB backup of an XFS filesystem — a dedicated second disk (/dev/sdb1, 16GB) on
ubuntu22-desktop-src (PM-14), formatted XFS and mounted at /mnt/xfs_testdata. Seeded fileset
(test-data/test-data.md):
  /mnt/xfs_testdata/TestData_XFS/
    readme.txt, docs/notes.txt, docs/sample.json,
    media/blob_1mb.bin, media/blob_2mb.bin

This test asserts the top-level listing (readme.txt, docs, media); verifying the nested
docs/media contents individually is deferred — general nested-folder FLR-browse behavior for a
plain (no Inclusion/Exclusion filter) job hasn't been independently confirmed yet in this suite.

NOTE: this test shares a source machine (Ubuntu2204Desktop_16.98/PM-14) with NJM-67816 in this
same suite — see _helpers.py's module docstring on why these must not run concurrently with
each other.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.inventory, pytest.mark.jira("NJM-68934")]

MACHINE = "Ubuntu2204Desktop_16.98"


@allure.title("NJM-68934 — Backup of XFS file system")
def test_xfs_backup(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68934")
    build_flb_job(page, job_name, MACHINE, ["mnt", "xfs_testdata"], ["TestData_XFS"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    # CALIBRATED live 2026-07-16: same "root" top-level FLR node as every other Linux source in
    # this suite (see NJM-67702's note) — it's a generic top-level container, not literally the
    # /root home directory, since this backup's actual source is /mnt/xfs_testdata, not /root.
    rows = flr_browse(page, job_name, ["root", "mnt", "xfs_testdata", "TestData_XFS"])
    found = set(extract_item_names(rows))
    assert found == {"readme.txt", "docs", "media"}, f"expected the TestData_XFS top-level listing, got {found}"

    verify_checksum(
        page, job_name, ["root", "mnt", "xfs_testdata", "TestData_XFS"], "readme.txt",
        "manifest-ubuntu22-xfs.sha256",
    )
