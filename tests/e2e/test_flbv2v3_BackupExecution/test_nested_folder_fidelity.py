r"""NJM-68960 — [FLB v1] FLB - Functional - Verify Retrieved Folders are Correctly Backed Up.

Uses `Subfolder_200Folders` (test-data/test-data.md — 218 files across 4 top-level dirs on
Window11's TestData_ForFLB) as the "nested folder structure with files at multiple levels"
fixture the TC calls for — already established in test_flbv2v3_SourceSelection as this project's
deep-nesting fixture (NJM-122657/dialog item count tests), just reused here for backup/recovery
fidelity rather than dialog UI behavior.

FIXTURE LAYOUT (confirmed live via `mcp__remoting__winrm_run` 2026-07-19 — an earlier version of
this test wrongly assumed the top-level `Folder1`/`Folder2` themselves held nested content; both
are genuinely EMPTY directories on disk. The real nested structure is one level further down, at
`Subfolder_200Folders/ft_video/Folder1/` — a distinct, separate `Folder1` holding 11 `Item_18x.txt`
files alongside `ft_video`'s own `sample_video.{avi,mov,mp4}`):
```
Subfolder_200Folders/
  Folder1/            (empty)
  Folder2/            (empty)
  ft_video/
    Folder1/          Item_189.txt .. Item_199.txt  (11 files)
    sample_video.avi / .mov / .mp4
  Item_001.txt .. Item_200.txt
  sample_word.doc / .docm / .docx / Sample_word.dotx
```

No curated checksum manifest exists for this fixture (unlike MixedTypes), so verification is
STRUCTURAL: the top-level listing must reproduce the same subdirectory names, `ft_video`'s own
listing must show its nested `Folder1`, and that nested `Folder1` must be non-empty — proving the
3-level-deep hierarchy (not just a flat file dump) survived backup + recovery, which is what
"retrieved folders are correctly backed up" is actually asserting.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import build_flb_job, extract_item_names, flr_browse, run_and_wait_flb_job

pytestmark = [pytest.mark.flb, pytest.mark.backupexecution]

MACHINE = "Window11"
DRILL_TO_TESTDATA = ["Local Disk (C:)", "TestData_ForFLB"]
# Wizard item-picker drill path uses 'Local Disk (C:)'; FLR's own Files-step tree uses plain 'C:'
# for the same drive — see test_use_case_workflows.py's FLR_DRILL_TO_MIXEDTYPES comment for the
# full story (this exact conflation was already found+fixed once in suite C, then re-found live
# here before this fix).
DRILL_TO_SUBFOLDER = ["Local Disk (C:)", "TestData_ForFLB", "Subfolder_200Folders"]
FLR_DRILL_TO_SUBFOLDER = ["C:", "TestData_ForFLB", "Subfolder_200Folders"]


@allure.title("NJM-68960 — nested folder structure survives backup + recovery intact")
@pytest.mark.jira("NJM-68960")
def test_nested_folder_structure_recovered_intact(logged_in_page, flb_job_cleanup):
    page = logged_in_page
    job_name = flb_job_cleanup("AUTO_FLB_NJM-68960_nested-folders")

    build_flb_job(page, job_name, MACHINE, DRILL_TO_TESTDATA, ["Subfolder_200Folders"])
    status = run_and_wait_flb_job(page, job_name, timeout_ms=300_000)
    assert status == "Successful", f"job did not succeed: {status}"

    top_level = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_SUBFOLDER)))
    assert {"Folder1", "Folder2", "ft_video"}.issubset(top_level), (
        f"expected Folder1/Folder2/ft_video to survive at the top level, got {top_level}"
    )

    ft_video_level = set(extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_SUBFOLDER + ["ft_video"])))
    assert "Folder1" in ft_video_level, (
        f"expected ft_video's own nested Folder1 to survive, got {ft_video_level}"
    )

    nested = extract_item_names(flr_browse(page, job_name, FLR_DRILL_TO_SUBFOLDER + ["ft_video", "Folder1"]))
    assert len(nested) == 11, f"expected ft_video/Folder1's 11 Item_18x.txt files, got {len(nested)}: {nested}"
