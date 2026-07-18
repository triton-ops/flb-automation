r"""NJM-67687 / 123117 / 123119 / 123121 / 123123 — [FLB v1] FLB - Functional - Verify Backup to
the Onboard / Amazon S3 / Azure Blob / Wasabi / Backblaze B2 Repository (Windows & Linux Sources).

PARAMETRIZE PATTERN (see docs/parametrize-pattern.md, same as the FLRFunctional OS-support
matrix): these 4 TCs' Xray steps are structurally identical across BOTH the repository axis and
the OS axis — back up the seeded MixedTypes fixture, run a full then an incremental backup,
recover a file via FLR Download and verify its checksum against the source manifest — differing
only in which repository the job targets and which OS sources it. 4 repos x 2 OS = 8 rows.

FIXTURES: reuses the exact per-OS MixedTypes tree + manifest every other suite already relies on
(Window11 + manifest-win11-mixed.sha256; Linux_16.84 + manifest-linux-mixed.sha256). Repositories
per test-data/environment.md's "FLB target repositories (nbr-84)" table: Onboard repository (id
2), Amazon_Repo (id 9, AWS S3), Azure_Repo (id 11, AZURE_BLOB), Wasabi_Repo (id 6, WASABI) — none
of these have immutability enabled (see test_repo_immutability_matrix.py for the *_Immutable
variants). NJM-123123 (Backblaze B2, non-immutable) has no separate non-immutable Backblaze repo
on nbr-84 — it reuses `BlackBlaze_Immutable` (id 13) WITHOUT enabling any immutability/retention
option on the job, the same documented substitution convention environment.md already uses for
Cloudian standing in for the removed Ceph_S3.

SCOPE NOTE (same convention as the rest of this project): pytest asserts both the full AND the
incremental job runs reached Successful, and the downloaded file's SHA-256 matches the manifest —
this last assertion IS the "recovered files are byte-identical to the source" check the TCs ask
for, verified directly in Python (not deferred to an agent-driven remoting step), since
verify_checksum() downloads through the browser itself.

INCREMENTAL METHODOLOGY — see _helpers.py's module docstring for the full reasoning. In short: a
real incremental backup captures the CHANGE since the last backup (Confluence "File Level Backup
v1" FRD: "Transporter performs the incremental backup using the base files"), which this suite
cannot literally exercise (changing SOURCE content mid-test needs SSH/WinRM from inside the
pytest process — a capability this project doesn't have; test_flbv2v3_IncludeExclude/
test_njm_185023.py already documented the identical gap). Consistent with that precedent, this
test runs the SAME job twice unmodified via run_full_then_incremental() — the second run is
confirmed live to default to 'Incremental' on its own (screenshot-verified 'Backup type:
Incremental' pre-selected), not something this test forces by editing the job's selection.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, run_full_then_incremental, verify_checksum

pytestmark = [pytest.mark.flb, pytest.mark.objectstorage]

# (jira_id, repo_label, repo_name, machine, is_linux, manifest, drill_parent, flr_parent) — one
# row per repo x OS. drill_parent is the FLB wizard's Select Items dialog naming ('Local Disk
# (C:)'); flr_parent is the FLR wizard's OWN, DIFFERENT left-tree naming for the same volume
# ('C:', or 'root' for a Linux source's top-level node) — CALIBRATED precedent already
# established by the FLRFunctional OS-support matrix (test_njm_83226_83255_..._matrix.py's
# flr_parent = ["C:", ...] / ["root", ...]). An earlier version of this file reused drill_parent
# for BOTH purposes, which happened to look plausible but is wrong — the FLR left tree has no
# 'Local Disk (C:)' node at all, only 'C:'.
REPO_MATRIX = [
    pytest.param(
        # Also covers NJM-85728 (Repository - Integrity and Structure of Backup Data Post-Job):
        # that TC's steps (build+run full, verify RP, add data+run incremental, FLR-recover and
        # verify content) are exactly this row's body — no separate test needed.
        "NJM-67687", "onboard-win", "Onboard repository", "Window11", False,
        "manifest-win11-mixed.sha256", ["Local Disk (C:)", "TestData_ForFLB"], ["C:", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-67687"), pytest.mark.jira("NJM-85728"), pytest.mark.xdist_group(name="Window11")],
        id="NJM-67687-onboard-win",
    ),
    pytest.param(
        "NJM-67687", "onboard-linux", "Onboard repository", "Linux_16.84", True,
        "manifest-linux-mixed.sha256", ["TestData_ForFLB"], ["root", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-67687"), pytest.mark.xdist_group(name="Linux_16.84")],
        id="NJM-67687-onboard-linux",
    ),
    pytest.param(
        "NJM-123117", "s3-win", "Amazon_Repo", "Window11", False,
        "manifest-win11-mixed.sha256", ["Local Disk (C:)", "TestData_ForFLB"], ["C:", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123117"), pytest.mark.xdist_group(name="Window11")],
        id="NJM-123117-s3-win",
    ),
    pytest.param(
        "NJM-123117", "s3-linux", "Amazon_Repo", "Linux_16.84", True,
        "manifest-linux-mixed.sha256", ["TestData_ForFLB"], ["root", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123117"), pytest.mark.xdist_group(name="Linux_16.84")],
        id="NJM-123117-s3-linux",
    ),
    pytest.param(
        "NJM-123119", "azure-win", "Azure_Repo", "Window11", False,
        "manifest-win11-mixed.sha256", ["Local Disk (C:)", "TestData_ForFLB"], ["C:", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123119"), pytest.mark.xdist_group(name="Window11")],
        id="NJM-123119-azure-win",
    ),
    pytest.param(
        "NJM-123119", "azure-linux", "Azure_Repo", "Linux_16.84", True,
        "manifest-linux-mixed.sha256", ["TestData_ForFLB"], ["root", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123119"), pytest.mark.xdist_group(name="Linux_16.84")],
        id="NJM-123119-azure-linux",
    ),
    pytest.param(
        "NJM-123121", "wasabi-win", "Wasabi_Repo", "Window11", False,
        "manifest-win11-mixed.sha256", ["Local Disk (C:)", "TestData_ForFLB"], ["C:", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123121"), pytest.mark.xdist_group(name="Window11")],
        id="NJM-123121-wasabi-win",
    ),
    pytest.param(
        "NJM-123121", "wasabi-linux", "Wasabi_Repo", "Linux_16.84", True,
        "manifest-linux-mixed.sha256", ["TestData_ForFLB"], ["root", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123121"), pytest.mark.xdist_group(name="Linux_16.84")],
        id="NJM-123121-wasabi-linux",
    ),
    pytest.param(
        "NJM-123123", "backblaze-win", "BlackBlaze_Immutable", "Window11", False,
        "manifest-win11-mixed.sha256", ["Local Disk (C:)", "TestData_ForFLB"], ["C:", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123123"), pytest.mark.xdist_group(name="Window11")],
        id="NJM-123123-backblaze-win",
    ),
    pytest.param(
        "NJM-123123", "backblaze-linux", "BlackBlaze_Immutable", "Linux_16.84", True,
        "manifest-linux-mixed.sha256", ["TestData_ForFLB"], ["root", "TestData_ForFLB"],
        marks=[pytest.mark.jira("NJM-123123"), pytest.mark.xdist_group(name="Linux_16.84")],
        id="NJM-123123-backblaze-linux",
    ),
]


@pytest.mark.parametrize(
    "jira_id,repo_label,repo_name,machine,is_linux,manifest,drill_parent,flr_parent", REPO_MATRIX,
)
def test_backup_to_repository(
    logged_in_page, flb_job_cleanup, jira_id, repo_label, repo_name, machine, is_linux, manifest,
    drill_parent, flr_parent,
):
    allure.dynamic.title(f"{jira_id} — backup to {repo_name} ({repo_label}), full + incremental + checksum verify")
    page = logged_in_page
    job_name = flb_job_cleanup(f"AUTO_FLB_{jira_id}_{repo_label}")

    build_flb_job(page, job_name, machine, drill_parent, ["MixedTypes"], is_linux=is_linux, repository=repo_name)
    full_status, incremental_status = run_full_then_incremental(page, job_name, timeout_ms=600_000)
    assert full_status == "Successful", f"full run did not succeed on {repo_name} ({repo_label}): {full_status}"
    assert incremental_status == "Successful", (
        f"incremental run did not succeed on {repo_name} ({repo_label}): {incremental_status}"
    )

    verify_checksum(page, job_name, flr_parent + ["MixedTypes"], "sample.pdf", manifest)
