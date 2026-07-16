"""NJM-185016 — [FLB v3] FLB Job Wizard - Step 2/3 - Invalid parameter highlights box red with
'Invalid parameters' message (FLB-11/FLB-12). Original status: PENDING. UI-behavior/validation
check.

Per the NAS Backup Confluence spec (https://confluence.nakivo.com/display/tst/NAS+Backup, which
File Level Backup's own spec explicitly reuses for Inclusion/Exclusion): "If at least one
parameter is invalid, the whole parameter text box shall be highlighted in red" and "Shall
display a message which line(s) are invalid" (spec's own example: "Invalid parameters: *.docx,
My file.xlsx" — the exact scenario this test reproduces).

CALIBRATED live 2026-07-15: this build shows NEITHER the red highlight NOR the message — only a
behavioral Next-block (confirmed working). test_invalid_parameter_shows_visible_feedback is
written to fail explicitly (not hidden via xfail) so the report honestly shows this spec gap.
"""
from __future__ import annotations

import allure
import pytest

from ._helpers import has_visible_invalid_feedback, open_to_inclusion

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185016")]


@allure.title("NJM-185016a — invalid parameter blocks Next")
def test_invalid_parameter_blocks_next(logged_in_page):
    flb = open_to_inclusion(logged_in_page)
    flb.enable_inclusion(["*.docx", "My file.xlsx"])
    assert not flb.inclusion_advances_wizard(), "an entry with a space should block Next"
    flb.click_cancel()


@allure.title("NJM-185016b — invalid parameter shows visible red/invalid feedback (spec gap)")
def test_invalid_parameter_shows_visible_feedback(logged_in_page):
    page = logged_in_page
    flb = open_to_inclusion(page)
    flb.enable_inclusion(["*.docx", "My file.xlsx"])
    assert has_visible_invalid_feedback(page), (
        "spec expects the textarea to highlight red with a message naming 'My file.xlsx'; "
        "this build shows no such visual feedback (behavioral-only gate)"
    )
    flb.click_cancel()


@allure.title("NJM-185016c — removing the invalid line re-enables Next")
def test_invalid_parameter_fix_reenables_next(logged_in_page):
    flb = open_to_inclusion(logged_in_page)
    flb.enable_inclusion(["*.docx"])
    assert flb.inclusion_advances_wizard(), "a valid entry alone should not block Next"
