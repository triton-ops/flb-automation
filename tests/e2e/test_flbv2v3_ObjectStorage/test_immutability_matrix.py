r"""NJM-123118 / 123120 / 123122 / 123124 / 123133 / 70517 / 70017 — [FLB v1] FLB - Functional -
Verify Backup to Immutable Amazon S3 / Azure Blob / Wasabi / Backblaze B2 / Local Linux Repository;
Verify Backup Job with Immutability Enabled; Verify User Story: Backup Files to Immutable Cloud
Storage (US5).

PARAMETRIZE PATTERN: these TCs' Xray steps are structurally identical — build a job against an
immutable repository with an 'Immutable for N days' retention set, run it, confirm the recovery
point is genuinely marked immutable, and verify the recovered content matches the source. NJM-70517
("Linux-based or NAS repository with immutability") maps onto the Local-Immutable row (matches its
"Local Linux" framing most directly — see test-data/environment.md). NJM-70017 ("Immutable Cloud
Storage" user story) maps onto the Wasabi-immutable row as a representative cloud case — no
separate test needed for either, per the same jira-marker-folding convention used elsewhere in
this suite (see NJM-85728 in test_repo_backup_matrix.py).

CONFIRMED LIVE 2026-07-18 (browser/checks/check_immutability_calibration.py — first-ever proof on
this appliance that NBR can create a genuinely immutable savepoint, updating test-data/
environment.md's long-standing "never proven" caveat): the recovery point's own detail page
(Settings -> Repositories -> <repo> -> <machine>) shows 'Immutable until'/'Protected until'
columns with real computed timestamps. Deleting the JOB is NOT blocked (disappears from the Jobs
sidebar normally via flb_job_cleanup) — but the underlying BACKUP does NOT delete with it; it
survives as an orphaned entry until the immutable window elapses. Every row here uses the
shortest practical period (1 day) to minimize how long that orphaned data lingers — this is
expected/by-design, not a leak to chase.

⚠ COST NOTE: the four cloud rows (S3/Azure/Wasabi/Backblaze) upload real data to real external
cloud accounts and leave it there, undeletable, for the immutability window. Per this project's
write-all/run-selectively pace, only the Local-Immutable row (free, local disk) is intended to be
run routinely; the cloud rows are written and correct but should be run deliberately, not by
default, given the real external cost/footprint each run leaves behind.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.data_protection_page import DataProtectionPage
from browser.pom.common.repository_management_page import RepositoryManagementPage

from ._helpers import build_flb_job, run_and_wait_flb_job, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage]

# (jira_id, repo_label, repo_name, machine, is_linux, manifest, drill_parent, flr_parent) —
# one row per immutable repo. Folded markers: NJM-70517 -> local row, NJM-70017 -> wasabi row.
IMMUTABILITY_MATRIX = [
    pytest.param(
        "NJM-123133", "local-immutable", "Local-Immutable", "Window11", False,
        "manifest-win11-mixed.sha256", ["Local Disk (C:)", "TestData_ForFLB"], ["C:", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123133"), pytest.mark.jira("NJM-70517"),
               pytest.mark.xdist_group(name="Window11")],
        id="NJM-123133-local-immutable",
    ),
    pytest.param(
        "NJM-123118", "s3-immutable", "Amazon_Immutable", "Window11", False,
        "manifest-win11-mixed.sha256", ["Local Disk (C:)", "TestData_ForFLB"], ["C:", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123118"), pytest.mark.xdist_group(name="Window11")],
        id="NJM-123118-s3-immutable",
    ),
    pytest.param(
        "NJM-123120", "azure-immutable", "Azure_Immutable", "Window11", False,
        "manifest-win11-mixed.sha256", ["Local Disk (C:)", "TestData_ForFLB"], ["C:", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123120"), pytest.mark.xdist_group(name="Window11")],
        id="NJM-123120-azure-immutable",
    ),
    pytest.param(
        "NJM-123122", "wasabi-immutable", "Wasabi-immutable", "Window11", False,
        "manifest-win11-mixed.sha256", ["Local Disk (C:)", "TestData_ForFLB"], ["C:", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123122"), pytest.mark.jira("NJM-70017"),
               pytest.mark.xdist_group(name="Window11")],
        id="NJM-123122-wasabi-immutable",
    ),
    pytest.param(
        "NJM-123124", "backblaze-immutable", "BlackBlaze_Immutable", "Window11", False,
        "manifest-win11-mixed.sha256", ["Local Disk (C:)", "TestData_ForFLB"], ["C:", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123124"), pytest.mark.xdist_group(name="Window11")],
        id="NJM-123124-backblaze-immutable",
    ),
]


@pytest.mark.parametrize(
    "jira_id,repo_label,repo_name,machine,is_linux,manifest,drill_parent,flr_parent", IMMUTABILITY_MATRIX,
)
def test_backup_to_immutable_repository(
    logged_in_page, flb_job_cleanup, jira_id, repo_label, repo_name, machine, is_linux, manifest,
    drill_parent, flr_parent,
):
    allure.dynamic.title(f"{jira_id} — backup to immutable {repo_name} ({repo_label}), 1-day immutability")
    page = logged_in_page
    job_name = flb_job_cleanup(f"AUTO_FLB_{jira_id}_{repo_label}")

    build_flb_job(
        page, job_name, machine, drill_parent, ["MixedTypes"], is_linux=is_linux,
        repository=repo_name, immutable_days=1,
    )
    status = run_and_wait_flb_job(page, job_name, timeout_ms=600_000)
    assert status == "Successful", f"job did not succeed on {repo_name} ({repo_label}): {status}"

    rp = RepositoryManagementPage(page)
    rp.open()
    rp.open_repository(repo_name)
    rp.open_backup(machine)
    marker = rp.immutability_marker_text()
    assert marker, f"expected an 'Immutable until' marker on the recovery point for {repo_name}, found none"

    # recover_file_level() (inside verify_checksum) expects the Data Protection dashboard's own
    # Jobs sidebar to already be on-screen — the repo-detail navigation above (Settings ->
    # Repositories -> ...) leaves the page somewhere that sidebar doesn't exist on at all, so
    # without navigating back first the job-row locator waits out its full timeout for a node
    # that can never appear. FOUND LIVE 2026-07-19: both pytest attempts (job id=339 original,
    # id=340 the automatic rerun) died at the identical spot for the identical reason — a real
    # authoring bug in this test, not appliance flakiness.
    DataProtectionPage(page).open()
    verify_checksum(page, job_name, flr_parent + ["MixedTypes"], "sample.pdf", manifest)
