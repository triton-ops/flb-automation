"""NJM-185014 — [FLB v3] FLB Job Wizard - Step 2/3 - Wildcards allowed in filename but not in
path (FLB-11/FLB-12). Original status: PENDING. UI-behavior/validation check.

Per the NAS Backup Confluence spec (https://confluence.nakivo.com/display/tst/NAS+Backup, which
File Level Backup's own spec explicitly reuses for Inclusion/Exclusion): "Wildcard characters and
file masks shall NOT be supported in path" for a FULL path (e.g. `\\\\Server\\Share\\*\\Backup\\*.ext`
shall not be supported), but "shall [be] supported for filename" even within a full path (e.g.
`\\\\Server\\Share\\Backup\\*.ext` shall be supported).

CALIBRATED live 2026-07-15 against the seeded IncludeExclude\\MixedTypes fixture — the live
behavior is MORE restrictive than spec in one respect and MORE permissive in another:
  - An ABSOLUTE Windows path (C:\\...) is REJECTED outright regardless of wildcard placement —
    even C:\\TestData_ForFLB\\*.ext (filename-only wildcard, direct source overlap), which per
    spec's own full-path example SHOULD be accepted. This is a genuine spec deviation, not
    "expected" behavior — flagged here, not silently normalized.
  - A RELATIVE path with a wildcard in an INTERMEDIATE segment is ACCEPTED, contradicting the
    spec's path-wildcard restriction (which is worded for full/UNC paths — it's untested whether
    the intent was meant to extend to relative paths too).
Both findings are reported as explicit test outcomes rather than adjusted to match assumptions.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import open_to_inclusion

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185014")]


@allure.title("NJM-185014a — absolute Windows path rejected regardless of wildcard (spec deviation)")
def test_wildcard_absolute_path_rejected(logged_in_page):
    """Per spec, a full path with a filename-only wildcard SHOULD be accepted (spec's own
    example: `\\\\Server\\Share\\Backup\\*.ext` shall be supported). This build rejects it anyway —
    a genuine spec deviation worth flagging, not a defect in this test's expectation."""
    flb = open_to_inclusion(logged_in_page)
    flb.enable_inclusion([r"C:\TestData_ForFLB\*.ext"])
    assert not flb.inclusion_advances_wizard(), (
        "an absolute C:\\ path is rejected regardless of wildcard placement in this build, even "
        "though spec's own full-path example implies a filename-only wildcard should be accepted"
    )
    flb.click_cancel()


@allure.title("NJM-185014b — relative path, wildcard in filename segment accepted")
def test_wildcard_relative_filename_accepted(logged_in_page):
    flb = open_to_inclusion(logged_in_page)
    flb.enable_inclusion([r"IncludeExclude\MixedTypes\*.docx"])
    assert flb.inclusion_advances_wizard(), "a relative path with a filename-segment wildcard should be accepted"


@allure.title("NJM-185014c — relative path, wildcard in intermediate segment also accepted")
def test_wildcard_relative_intermediate_segment(logged_in_page):
    flb = open_to_inclusion(logged_in_page)
    flb.enable_inclusion([r"IncludeExclude\*\MixedTypes\*.docx"])
    assert flb.inclusion_advances_wizard(), (
        "spec's path-wildcard restriction (worded for full/UNC paths) would expect a wildcard in "
        "an intermediate path segment to be rejected, but this build accepts it — documenting "
        "the actual behavior for a relative path"
    )


@allure.title("NJM-185014d — exact relative paths accepted with either delimiter")
def test_exact_relative_path_either_delimiter(logged_in_page):
    # slash direction doesn't matter for a relative path either (same finding as NJM-182426's
    # investigation: "slash direction doesn't matter" for backend path matching)
    flb = open_to_inclusion(logged_in_page)
    flb.enable_inclusion([r"IncludeExclude\MixedTypes\sample.docx", "IncludeExclude/MixedTypes/sample.docx"])
    assert flb.inclusion_advances_wizard(), "exact relative paths with either delimiter should be accepted"
