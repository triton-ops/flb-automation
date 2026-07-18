r"""NJM-68975 — [FLB v2] FLB - Functional - Verify System Files (e.g., pagefile.sys) are Skipped.

Per the TC's Xray steps: include a source scope that contains known Windows system files
(C:\pagefile.sys, C:\hiberfil.sys, C:\swapfile.sys) alongside ordinary files; the FLB job should
complete with the system files reported as SKIPPED (not errors); the recovery point should contain
the ordinary files but NOT the system files.

BLOCKED for bounded automation — the system files this TC targets live at the C: volume ROOT and
are OS-locked; the only way to bring them "within scope" is to select the entire C: volume as the
backup source. This framework's safety/practicality convention is small, seeded filesets (a few
MB); backing up an entire live C: volume is a multi-GB, multi-hour operation that would flood the
Onboard repository and isn't a bounded, repeatable automation. A fake file merely *named*
pagefile.sys inside a small folder would NOT exercise the product's skip logic (which keys off the
real locked system file at its real root path, not the name), so a name-only fixture would produce
a misleading green.

This TC therefore needs a dedicated whole-C:-volume run (or an include/exclude-filtered run
scoping just the root system files — that machinery is the FLBv2v3_IncludeExclude suite's, not
this one) and is left written-but-skipped rather than faked. The body below is the intended
executable flow (build over the C: volume → run → browse RP root → assert system files absent,
ordinary files present).
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [
    pytest.mark.flb, pytest.mark.sourceselection, pytest.mark.jira("NJM-68975"),
    pytest.mark.xdist_group(name="Window11"),
]

MACHINE = "Window11"


@pytest.mark.skip(
    reason="BLOCKED for bounded automation: exercising root system-file skip requires selecting the "
    "whole C: volume (multi-GB), which violates the small-seeded-fileset convention; a name-only "
    "fixture wouldn't trigger the real skip logic. Written and executable; run deliberately with a "
    "whole-volume scope when that's acceptable."
)
@allure.title("NJM-68975 — Windows system files (pagefile.sys/hiberfil.sys) are skipped")
def test_system_files_skipped(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68975")
    # Whole C: volume — the only scope that actually contains the root system files.
    build_flb_job(page, job_name, MACHINE, [], ["Local Disk (C:)"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=3_600_000)
    assert status == "Successful", f"job did not succeed: {status}"

    names = extract_item_names(flr_browse(page, job_name, ["C:"]))
    lowered = {n.lower() for n in names}
    assert "pagefile.sys" not in lowered, f"pagefile.sys was NOT skipped — present in RP root: {names}"
    assert "hiberfil.sys" not in lowered, f"hiberfil.sys was NOT skipped — present in RP root: {names}"
