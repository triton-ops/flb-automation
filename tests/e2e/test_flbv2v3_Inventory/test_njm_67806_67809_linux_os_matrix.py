"""NJM-67806 / 67807 / 67808 / 67809 — [FLB v1] FLB - OS Support - Verify End-to-End Workflow on
Debian 12 / Ubuntu 24.04 LTS (Server) / RHEL 9 / SLES 15 SP6.

PARAMETRIZE PATTERN EXAMPLE (see docs/parametrize-pattern.md): these four TCs were the textbook
case flagged in docs/enterprise-gap-analysis.md's "zero @pytest.mark.parametrize usage" finding —
100% identical bodies (build -> run -> FLR browse -> checksum verify), differing only in MACHINE
and the checksum MANIFEST. Consolidated from four separate test_njm_<id>.py files (each previously
run and PASSED individually) into this one parametrized test, re-verified live post-consolidation
against all four real sources. Per-case Jira traceability — lost by default under parametrize — is
preserved deliberately: `pytest.mark.jira(...)` per `pytest.param(..., marks=...)` and a per-
invocation `allure.dynamic.title()` call so Allure still shows one distinctly-titled result per TC,
not one generically-named test with 4 sub-results.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import (
    MIXED_TYPES_FILES,
    build_flb_job,
    extract_item_names,
    flr_browse,
    run_and_wait_flb_job,
    verify_checksum,
)

pytestmark = [pytest.mark.flb, pytest.mark.inventory]

# (jira_id, machine, manifest, os_label) — one row per TC. Adding a 5th OS to this suite's
# MixedTypes coverage is a one-line addition here, not a new file.
LINUX_OS_MATRIX = [
    pytest.param(
        "NJM-67806", "Debian_12", "manifest-debian12-mixed.sha256", "Debian 12",
        marks=pytest.mark.jira("NJM-67806"), id="NJM-67806-debian12",
    ),
    pytest.param(
        "NJM-67807", "Linux_16.84", "manifest-linux-mixed.sha256", "Ubuntu 24.04 LTS (Server)",
        # xdist_group: shares a source (Linux_16.84/PM-2) with NJM-68933 in this suite — see
        # test_njm_68933.py's own marker and docs/xdist-parallelization.md.
        marks=[pytest.mark.jira("NJM-67807"), pytest.mark.xdist_group(name="Linux_16.84")],
        id="NJM-67807-ubuntu2404",
    ),
    pytest.param(
        "NJM-67808", "RHEL_9", "manifest-rhel9-mixed.sha256", "RHEL 9",
        marks=pytest.mark.jira("NJM-67808"), id="NJM-67808-rhel9",
    ),
    pytest.param(
        "NJM-67809", "SLE_SUSE_15.205", "manifest-sles15-mixed.sha256", "SLES 15 SP6",
        marks=pytest.mark.jira("NJM-67809"), id="NJM-67809-sles15",
    ),
]


@pytest.mark.parametrize("jira_id,machine,manifest,os_label", LINUX_OS_MATRIX)
def test_linux_os_support_e2e(logged_in_page, flb_job_cleanup, jira_id, machine, manifest, os_label):
    allure.dynamic.title(f"{jira_id} — End-to-end workflow on {os_label}")
    page = logged_in_page
    job_name = flb_job_cleanup(f"AUTO_FLB_{jira_id}")
    build_flb_job(page, job_name, machine, ["TestData_ForFLB"], ["MixedTypes"], is_linux=True)
    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed: {status}"

    # CALIBRATED live 2026-07-16: a Linux source's FLR left tree top-level node is "root", not
    # the wizard drill path's TestData_ForFLB — see NJM-67702's note.
    rows = flr_browse(page, job_name, ["root", "TestData_ForFLB", "MixedTypes"])
    found = set(extract_item_names(rows))
    assert found == MIXED_TYPES_FILES, f"expected the standard MixedTypes fileset, got {found}"

    verify_checksum(
        page, job_name, ["root", "TestData_ForFLB", "MixedTypes"], "sample.docx", manifest,
    )
