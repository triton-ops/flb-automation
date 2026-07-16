"""NJM-182431 — [FLB v3] FLB Job Wizard - Inclusion/Exclusion UI - Step 2/3 layout and controls
(FLB-11/FLB-12). Original status: PENDING (never executed under the old RPC-driven workflow —
this suite's run is the first recorded verdict). UI-behavior check — no backup job needs to run.
"""
from __future__ import annotations

import allure
import pytest

from browser.pom.common.locators import InclusionExclusionLocators as IE

from ._helpers import open_to_inclusion

pytestmark = [pytest.mark.flb, pytest.mark.include_exclude, pytest.mark.jira("NJM-182431")]


@allure.title("NJM-182431 — Inclusion/Exclusion Step 2/3 layout and controls")
def test_layout_and_controls(logged_in_page):
    page = logged_in_page
    flb = open_to_inclusion(page)
    assert flb.current_step_title().startswith("2"), "expected to land on step 2 (Inclusion)"

    # Step 2 note: the calibrated UI is a single 'Include items' checkbox + free-text textarea —
    # no separate Extension/File name/Path rule-type selector exists in this build.
    assert page.locator(IE.INCLUDE_CHECKBOX).count() > 0
    flb.enable_inclusion(["*.docx"])
    assert flb.page.locator(IE.INCLUDE_TEXTAREA).locator("visible=true").first.input_value() == "*.docx"
    # remove the rule -> textarea reflects the change (checkbox stays ticked but now empty,
    # which legitimately blocks Next — re-populate before advancing)
    flb.page.locator(IE.INCLUDE_TEXTAREA).locator("visible=true").first.fill("")
    assert flb.page.locator(IE.INCLUDE_TEXTAREA).locator("visible=true").first.input_value() == ""
    flb.enable_inclusion(["*.docx"])

    flb.click_next()  # -> Exclusion
    assert flb.current_step_title().startswith("3")
    assert page.locator(IE.EXCLUDE_CHECKBOX).count() > 0
    flb.enable_exclusion(["*.pdf"])
    assert flb.page.locator(IE.EXCLUDE_TEXTAREA).locator("visible=true").first.input_value() == "*.pdf"
    flb.page.locator(IE.EXCLUDE_TEXTAREA).locator("visible=true").first.fill("")
    assert flb.page.locator(IE.EXCLUDE_TEXTAREA).locator("visible=true").first.input_value() == ""

    flb.click_cancel()
