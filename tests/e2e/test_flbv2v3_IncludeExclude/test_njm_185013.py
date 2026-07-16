"""NJM-185013 — [FLB v3] FLB Job Wizard - Step 2 Inclusion - Wildcard pattern table validation
(*.*, abc*, abc?, *share, Na??vo.log) (FLB-11). Original status: PENDING. UI-behavior check.

Confirmed against the NAS Backup Confluence spec (https://confluence.nakivo.com/display/tst/NAS+Backup,
which File Level Backup's own spec explicitly reuses for Inclusion/Exclusion): these five exact
pattern shapes are the spec's own reference examples of valid wildcard syntax.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import InclusionExclusionLocators as IE

from ._helpers import open_to_inclusion

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-185013")]


@allure.title("NJM-185013 — Inclusion wildcard pattern table validation")
def test_wildcard_pattern_table(logged_in_page):
    page = logged_in_page
    flb = open_to_inclusion(page)
    patterns = ["*.*", "abc*", "abc?", "*share", "Na??vo.log"]
    flb.enable_inclusion(patterns)
    assert flb.page.locator(IE.INCLUDE_TEXTAREA).locator("visible=true").first.input_value() == "\n".join(patterns)
    assert flb.inclusion_advances_wizard(), "all five spec wildcard shapes should be accepted"
    flb.click_cancel()
