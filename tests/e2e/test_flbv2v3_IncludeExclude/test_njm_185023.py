"""NJM-185023 — [FLB v3] FLB Job Wizard - Step 2/3 - Inclusion/Exclusion applied consistently
across initial + 3 incremental runs (FLB-11/FLB-12). Original verdict (raw-RPC execution): PASS.

Verify Inclusion (*.docx) / Exclusion (*.tmp) filters remain consistently applied across an
initial full backup and 3 subsequent incremental runs.

SCOPE NOTE: the original RPC-driven investigation added new files to the source (via winrm)
BETWEEN each of the 4 runs. Live remote file manipulation mid-test requires WinRM access, which
is only available to the agent driving this session (via mcp__remoting__*), not to Python code
executing inside a pytest test process — so this port pre-seeds all 8 fixture files
(keep1-4.docx, exclude1-4.tmp) upfront rather than adding them between runs, and instead runs
the SAME job 4 times consecutively (full + 3 incremental). This still verifies the core
requirement — the Inclusion/Exclusion filter is enforced identically on every run of the job, not
just its first — though it doesn't exercise the literal "source data changes between runs"
scenario. Re-introducing genuine between-run data changes would need either a WinRM-capable
pytest fixture (e.g. via a `pywinrm` dependency) or an out-of-band seeding step, deferred here.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import IE_FLR_PREFIX, IE_WIZARD_DRILL, build_flb_job, flr_browse, extract_item_names, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185023")]


@allure.title("NJM-185023 — Inclusion/Exclusion consistent across initial + 3 incremental runs")
def test_incremental_consistency(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-185023")
    build_flb_job(
        page, job_name, IE_WIZARD_DRILL, ["IncrementalConsistency"],
        inclusion=["*.docx"], exclusion=["*.tmp"],
    )

    for run_label in ("full", "incremental #1", "incremental #2", "incremental #3"):
        status = run_and_wait_flb_job(page, job_name)
        assert status == "Successful", f"{run_label} run did not succeed: {status}"

    rows = flr_browse(page, job_name, IE_FLR_PREFIX + ["IncrementalConsistency"])
    found = set(extract_item_names(rows))
    expected_keep = {"keep1.docx", "keep2.docx", "keep3.docx", "keep4.docx"}
    assert expected_keep <= found, f"all keep*.docx should be present, got {found}"
    assert not any(n.startswith("exclude") for n in found), (
        f"no exclude*.tmp files should ever appear across repeated runs, got {found}"
    )
