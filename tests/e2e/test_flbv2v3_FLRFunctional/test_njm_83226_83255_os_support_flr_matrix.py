"""NJM-83226 / 83229 / 83231 / 83234 / 83244 / 83246 / 83252 / 83255 — [FLB v1] FLB - OS Support
- Verify End-to-End Workflow (via FLR recovery to CIFS share) on Windows Server 2022 / 2019 /
2016 / Windows 11 / RHEL 9 / SLES 15 / AlmaLinux 9 / Ubuntu 22.04 Desktop.

PARAMETRIZE PATTERN (see docs/parametrize-pattern.md): these 8 TCs' Xray steps are structurally
identical — build an FLB job on the OS's source over the seeded fileset, run it, open FLR,
select everything backed up, recover to a CIFS share, verify destination content — differing
only in machine/manifest/OS-family, the exact bar the Inventory suite's Linux-OS matrix already
cleared. NJM-83235 (Windows 10 Enterprise) is deliberately NOT in this matrix: its source has no
seeded MixedTypes/manifest and its host is unreachable for hashing, so its body genuinely
differs — see test_njm_83235.py.

FIXTURES: every row reuses the exact display name + seeded MixedTypes + manifest that the
Inventory suite's per-OS E2E tests already live-verified (NJM-67693/67694/67697/67700/67808/
67809/67813/67816) — including Win_Server2019_15.3, which is win-fs3 (10.10.15.3, the reachable
WS2019 FLB source added 2026-07-13), NOT the legacy unreachable 10.10.15.211 host. The TC text's
"10-20 subfolders and diverse file types" maps to the seeded MixedTypes convention (7 diverse
file types + per-host manifest — the same fixture-over-abstract-text mapping the Inventory suite
documented).

SCOPE NOTE (same convention as the rest of this suite): pytest asserts job status + the wizard's
recovery-started confirmation; destination-content verification (each TC's final step) is done
by the agent driving WinRM against win-fs3, comparing the landed zip's 7 files against that
row's manifest.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, recover_to_share, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.flrfunctional]

# (jira_id, machine, manifest, os_label, is_linux) — one row per TC.
OS_FLR_MATRIX = [
    pytest.param(
        "NJM-83226", "Win_Server2022_81.58", "manifest-win2022-mixed.sha256",
        "Windows Server 2022", False,
        marks=pytest.mark.jira("NJM-83226"), id="NJM-83226-win2022",
    ),
    pytest.param(
        "NJM-83229", "Win_Server2019_15.3", "manifest-win2019-mixed.sha256",
        "Windows Server 2019", False,
        marks=pytest.mark.jira("NJM-83229"), id="NJM-83229-win2019",
    ),
    pytest.param(
        "NJM-83231", "Win_Server2016_15.19", "manifest-win2016-mixed.sha256",
        "Windows Server 2016", False,
        marks=pytest.mark.jira("NJM-83231"), id="NJM-83231-win2016",
    ),
    pytest.param(
        "NJM-83234", "Window11", "manifest-win11-mixed.sha256",
        "Windows 11", False,
        marks=pytest.mark.jira("NJM-83234"), id="NJM-83234-win11",
    ),
    pytest.param(
        "NJM-83244", "RHEL_9", "manifest-rhel9-mixed.sha256",
        "RHEL 9", True,
        marks=pytest.mark.jira("NJM-83244"), id="NJM-83244-rhel9",
    ),
    pytest.param(
        "NJM-83246", "SLE_SUSE_15.205", "manifest-sles15-mixed.sha256",
        "SLES 15", True,
        marks=pytest.mark.jira("NJM-83246"), id="NJM-83246-sles15",
    ),
    pytest.param(
        "NJM-83252", "AlmaLinux9_16.48", "manifest-almalinux9-mixed.sha256",
        "AlmaLinux 9", True,
        marks=pytest.mark.jira("NJM-83252"), id="NJM-83252-almalinux9",
    ),
    pytest.param(
        "NJM-83255", "Ubuntu2204Desktop_16.98", "manifest-ubuntu22-mixed.sha256",
        "Ubuntu 22.04 Desktop", True,
        marks=pytest.mark.jira("NJM-83255"), id="NJM-83255-ubuntu22",
    ),
]


@pytest.mark.parametrize("jira_id,machine,manifest,os_label,is_linux", OS_FLR_MATRIX)
def test_os_support_flr_e2e(logged_in_page, flb_job_cleanup, jira_id, machine, manifest, os_label, is_linux):
    allure.dynamic.title(f"{jira_id} — OS-support E2E via FLR to CIFS on {os_label}")
    page = logged_in_page
    job_name = flb_job_cleanup(f"AUTO_FLB_{jira_id}")

    if is_linux:
        build_flb_job(page, job_name, machine, ["TestData_ForFLB"], ["MixedTypes"], is_linux=True)
        # a Linux source's FLR left tree top-level node is "root" (Inventory calibration 2026-07-16)
        flr_parent = ["root", "TestData_ForFLB"]
    else:
        build_flb_job(page, job_name, machine, ["Local Disk (C:)", "TestData_ForFLB"], ["MixedTypes"])
        flr_parent = ["C:", "TestData_ForFLB"]

    status = run_and_wait_flb_job(page, job_name)
    assert status == "Successful", f"job did not succeed on {os_label}: {status}"

    # "select all files and folders" (each TC's Files step) = the whole backed-up MixedTypes
    # scope, selected as one folder from its parent (the select-from-parent pattern NJM-70319
    # calibrated — recovers the complete subtree).
    started = recover_to_share(page, job_name, flr_parent, ["MixedTypes"], "cifs")
    assert started, f"the FLR wizard did not confirm the recovery started on {os_label}"
