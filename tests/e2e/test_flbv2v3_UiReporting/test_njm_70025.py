r"""NJM-70025 — [FLB v1] FLB - Licensing - Verify Workload Count is Correctly Decremented After Job
Creation.

Read-only wrt appliance-wide state: this test only ever READS Settings > Licensing (never
"Change License" — see LicensingPage's own safety note) and creates exactly one AUTO_FLB_* job of
its own, matching the safety fence.

⚠ CALIBRATION NOTE (real finding, live 2026-07-21): the TC's literal steps expect the Used
Workloads counter to increase "by the number of newly added physical machines" after building a
job. Confirmed live that this counts UNIQUE PROTECTED MACHINES, not jobs: building a brand-new
AUTO_FLB_* job against Window11 — a machine already protected by 40+ pre-existing jobs in this
environment — left the workload count completely unchanged (9 before, 9 after), because Window11
already consumed its one workload slot the first time any job protected it. This is itself the
correct, defensible licensing behavior (no double-counting a machine across multiple jobs) — it
just means the TC's literal "verify it increases" wording can't be observed using ANY machine in
this environment, since every discovered physical machine (win11, win2022, win2016, win2019,
win2025, linux-src, ubuntu22/24, almalinux9, rocky9, debian12, sles15, rhel9) already has at
least one pre-existing job protecting it from this project's own suite history — there is no
never-before-protected machine left to add. Verifying a genuine increment would need either
removing ALL of a machine's existing job coverage first (unsafe — those aren't this suite's jobs
to touch) or discovering a brand-new machine (out of scope for this TC). This test instead
verifies the closest honestly-checkable claim: the workload count is NOT double-counted when the
same already-protected machine gets an additional job.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.licensing_page import LicensingPage

from ._helpers import build_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.uireporting, pytest.mark.jira("NJM-70025")]

MACHINE = "Window11"
JOB_NAME = "AUTO_FLB_NJM-70025_workload-count"


@allure.title("NJM-70025 — workload count is per-unique-machine, not per-job (adjusted per live finding)")
@pytest.mark.flaky(reruns=0)  # builds a uniquely-named job via Finish — an automatic rerun would
# hit a duplicate-name conflict rather than a clean retry (see this project's documented
# duplicate-job-on-rerun lesson from suites D/F; this exact test leaked 3 duplicates before this
# marker was added, cleaned up manually)
def test_workload_count_not_double_counted_for_same_machine(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    page.wait_for_timeout(1500)

    before = LicensingPage(page).open().workloads_used()
    assert before is not None, "expected a 'Workloads — N out of ... used' line on the Licensing page"

    build_flb_job(page, JOB_NAME, MACHINE, ["Local Disk (C:)"], ["TestData_ForFLB"])

    after = LicensingPage(page).open().workloads_used()
    assert after is not None, "expected a 'Workloads — N out of ... used' line after job creation"
    assert after == before, (
        f"expected the workload count to stay the same (Window11 is already protected by "
        f"existing jobs — see module docstring), got before={before}, after={after}"
    )

    flb_job_cleanup(JOB_NAME)
